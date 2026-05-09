#!/usr/bin/env node
'use strict';

/**
 * Extron Telnet watcher / raw logger / JSONL event capture.
 *
 * Goal:
 *   Capture exactly what the Extron sends, while also creating a normalized JSONL
 *   event stream that can be consumed later by LazyVidEditor, Companion helper
 *   scripts, or after-show automation.
 *
 * This intentionally avoids third-party packages so it can run on a Mac mini with
 * only Node.js installed.
 *
 * Example:
 *   node node-loggers/extron-watch.js --host 10.2.16.50 --port 23 --init W1CV --keepalive Q --stdin
 */

const fs = require('fs');
const net = require('net');
const os = require('os');
const path = require('path');
const readline = require('readline');

const DEFAULTS = {
  host: '10.2.16.50',
  port: 23,
  name: 'extron',
  outDir: path.resolve(process.cwd(), 'logs'),
  init: ['W1CV'],
  keepalive: 'Q',
  keepaliveMs: 50000,
  poll: [],
  pollMs: 60000,
  reconnect: true,
  reconnectMinMs: 2000,
  reconnectMaxMs: 30000,
  sendCrLf: true,
  stdin: false,
  echoTx: true,
  stripTelnetNegotiation: true,
};

function usage(exitCode) {
  const text = `
Extron Telnet watcher

Usage:
  node node-loggers/extron-watch.js --host <ip> [options]

Options:
  --config <file>          JSON config file. CLI args override config values.
  --host <ip-or-dns>       Extron host. Default: ${DEFAULTS.host}
  --port <number>          Telnet/SIS port. Default: ${DEFAULTS.port}
  --name <label>           Friendly name used in log records. Default: ${DEFAULTS.name}
  --out <folder>           Output folder. Default: ./logs
  --init <command>         Command sent after connect. Can be repeated. Default: W1CV
  --no-init                Do not send startup commands.
  --keepalive <command>    Keepalive command. Default: Q
  --no-keepalive           Disable keepalive.
  --keepalive-ms <ms>      Keepalive interval. Default: ${DEFAULTS.keepaliveMs}
  --poll <command>         Poll command. Can be repeated. Disabled by default.
  --poll-ms <ms>           Poll interval. Default: ${DEFAULTS.pollMs}
  --stdin                  Allow typing commands into this process and forwarding them to Extron.
  --no-reconnect           Disable reconnect loop.
  --lf                     Send LF only instead of CRLF after commands.
  --no-telnet-strip        Do not strip Telnet IAC negotiation bytes.
  --help                   Show this help.

Outputs:
  <timestamp>-<name>-raw.log       Raw receive/transmit/status log
  <timestamp>-<name>-events.jsonl  Structured JSONL event log
  <timestamp>-<name>-lines.txt     Timestamped received lines only

Examples:
  node node-loggers/extron-watch.js --host 10.2.16.50 --stdin
  node node-loggers/extron-watch.js --config config/extron-watch.json
  node node-loggers/extron-watch.js --host 10.2.16.50 --init W1CV --poll SG --poll-ms 60000
`;
  console.log(text.trim());
  process.exit(exitCode);
}

function parseArgs(argv) {
  const cli = {};
  const repeated = { init: [], poll: [] };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) throw new Error(`Missing value for ${arg}`);
      return argv[++i];
    };

    switch (arg) {
      case '--help':
      case '-h':
        usage(0);
        break;
      case '--config':
        cli.config = next();
        break;
      case '--host':
        cli.host = next();
        break;
      case '--port':
        cli.port = Number(next());
        break;
      case '--name':
        cli.name = next();
        break;
      case '--out':
      case '--out-dir':
        cli.outDir = path.resolve(next());
        break;
      case '--init':
        repeated.init.push(next());
        break;
      case '--no-init':
        cli.init = [];
        break;
      case '--keepalive':
        cli.keepalive = next();
        break;
      case '--no-keepalive':
        cli.keepalive = '';
        break;
      case '--keepalive-ms':
        cli.keepaliveMs = Number(next());
        break;
      case '--poll':
        repeated.poll.push(next());
        break;
      case '--poll-ms':
        cli.pollMs = Number(next());
        break;
      case '--stdin':
        cli.stdin = true;
        break;
      case '--no-reconnect':
        cli.reconnect = false;
        break;
      case '--lf':
        cli.sendCrLf = false;
        break;
      case '--no-telnet-strip':
        cli.stripTelnetNegotiation = false;
        break;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (repeated.init.length > 0) cli.init = repeated.init;
  if (repeated.poll.length > 0) cli.poll = repeated.poll;

  return cli;
}

function readConfig(configPath) {
  if (!configPath) return {};
  const full = path.resolve(configPath);
  const raw = fs.readFileSync(full, 'utf8');
  return JSON.parse(raw);
}

function normalizeConfig(config) {
  const result = Object.assign({}, DEFAULTS, config);

  if (!Array.isArray(result.init)) {
    result.init = result.init ? [String(result.init)] : [];
  }
  if (!Array.isArray(result.poll)) {
    result.poll = result.poll ? [String(result.poll)] : [];
  }

  result.port = Number(result.port);
  result.keepaliveMs = Number(result.keepaliveMs);
  result.pollMs = Number(result.pollMs);
  result.reconnectMinMs = Number(result.reconnectMinMs);
  result.reconnectMaxMs = Number(result.reconnectMaxMs);

  if (!result.host) throw new Error('host is required');
  if (!Number.isFinite(result.port) || result.port <= 0) throw new Error('port must be a number');
  if (!Number.isFinite(result.keepaliveMs) || result.keepaliveMs < 1000) throw new Error('keepaliveMs must be at least 1000');
  if (!Number.isFinite(result.pollMs) || result.pollMs < 1000) throw new Error('pollMs must be at least 1000');

  result.outDir = path.resolve(result.outDir || DEFAULTS.outDir);
  result.name = String(result.name || DEFAULTS.name).replace(/[^a-z0-9._-]+/gi, '-');

  return result;
}

function stampForFile(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0');
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
  ].join('-') + '_' + [
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join('-');
}

function nowIso() {
  return new Date().toISOString();
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function openLogs(config) {
  ensureDir(config.outDir);
  const prefix = `${stampForFile()}-${config.name}`;
  const rawPath = path.join(config.outDir, `${prefix}-raw.log`);
  const jsonlPath = path.join(config.outDir, `${prefix}-events.jsonl`);
  const linesPath = path.join(config.outDir, `${prefix}-lines.txt`);

  return {
    rawPath,
    jsonlPath,
    linesPath,
    raw: fs.createWriteStream(rawPath, { flags: 'a' }),
    jsonl: fs.createWriteStream(jsonlPath, { flags: 'a' }),
    lines: fs.createWriteStream(linesPath, { flags: 'a' }),
  };
}

function writeJsonLine(stream, obj) {
  stream.write(JSON.stringify(obj) + os.EOL);
}

function stripTelnetNegotiationBytes(buffer) {
  // Remove common Telnet IAC negotiation sequences while preserving ordinary text.
  // IAC = 255. WILL/WONT/DO/DONT are 3-byte sequences. SB runs until IAC SE.
  const out = [];
  for (let i = 0; i < buffer.length; i++) {
    const byte = buffer[i];
    if (byte !== 255) {
      out.push(byte);
      continue;
    }

    const command = buffer[i + 1];
    if (command === undefined) break;

    // Escaped 255 byte.
    if (command === 255) {
      out.push(255);
      i += 1;
      continue;
    }

    // WILL/WONT/DO/DONT option negotiation.
    if ([251, 252, 253, 254].includes(command)) {
      i += 2;
      continue;
    }

    // Subnegotiation: IAC SB ... IAC SE
    if (command === 250) {
      i += 2;
      while (i < buffer.length) {
        if (buffer[i] === 255 && buffer[i + 1] === 240) {
          i += 1;
          break;
        }
        i += 1;
      }
      continue;
    }

    // Other two-byte IAC command.
    i += 1;
  }
  return Buffer.from(out);
}

function normalizeWhitespace(text) {
  return String(text || '').replace(/\s+/g, ' ').trim();
}

function firstMatch(text, regex) {
  const m = text.match(regex);
  return m ? m[1] : null;
}

function parsePossibleNumbers(text) {
  const nums = [];
  const re = /-?\d+(?:\.\d+)?/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const n = Number(m[0]);
    if (Number.isFinite(n)) nums.push(n);
  }
  return nums;
}

function classifyExtronLine(line) {
  const raw = String(line || '');
  const normalized = normalizeWhitespace(raw);
  const lower = normalized.toLowerCase();
  const numbers = parsePossibleNumbers(normalized);

  const parsed = {
    eventType: 'ExtronRawLine',
    category: 'raw',
    raw,
    normalized,
    tokens: normalized ? normalized.split(' ') : [],
    numbers,
    confidence: 'low',
    notes: [],
  };

  if (!normalized) {
    parsed.eventType = 'ExtronBlankLine';
    parsed.category = 'blank';
    return parsed;
  }

  // Extron devices vary a lot by family and firmware. Keep this classifier broad,
  // and treat exact mappings as discoveries from the raw log rather than truth.
  if (/^evt\b/i.test(normalized) || /\bevt\b/i.test(normalized)) {
    parsed.eventType = 'ExtronEvent';
    parsed.category = 'event';
    parsed.confidence = 'medium';
  }

  if (/\b(rly|relay)\b/i.test(normalized) || /^rly/i.test(normalized)) {
    parsed.eventType = 'ExtronRelayEvent';
    parsed.category = 'relay';
    parsed.confidence = 'medium';
  }

  if (/\b(input|inp|in)\b/i.test(normalized) || /\b(output|out)\b/i.test(normalized)) {
    parsed.eventType = 'ExtronRouteOrInputEvent';
    parsed.category = 'routing';
    parsed.confidence = 'medium';
  }

  if (/\b(btn|button|panel|press|release)\b/i.test(normalized)) {
    parsed.eventType = 'ExtronButtonOrPanelEvent';
    parsed.category = 'button';
    parsed.confidence = 'medium';
  }

  if (/\b(screen|shade|lift|up|down|stop)\b/i.test(normalized)) {
    parsed.eventType = 'ExtronScreenOrLiftEvent';
    parsed.category = 'screen';
    parsed.confidence = parsed.confidence === 'low' ? 'medium' : parsed.confidence;
  }

  if (/\b(power|pwr|lamp|display|projector|mute|freeze)\b/i.test(normalized)) {
    parsed.eventType = 'ExtronDisplayControlEvent';
    parsed.category = 'display';
    parsed.confidence = parsed.confidence === 'low' ? 'medium' : parsed.confidence;
  }

  if (/\b(err|error|e\d{2})\b/i.test(normalized)) {
    parsed.eventType = 'ExtronErrorOrWarning';
    parsed.category = 'error';
    parsed.confidence = 'medium';
  }

  if (/^\w{2,6}\*/.test(normalized) || /\*/.test(normalized)) {
    parsed.notes.push('Contains * separator, common in SIS-style responses on some Extron products. Verify against the exact model manual.');
  }

  const inputCandidate = firstMatch(normalized, /(?:input|inp|in)\D*(\d+)/i);
  const outputCandidate = firstMatch(normalized, /(?:output|out)\D*(\d+)/i);
  const relayCandidate = firstMatch(normalized, /(?:relay|rly)\D*(\d+)/i);
  const buttonCandidate = firstMatch(normalized, /(?:button|btn)\D*(\d+)/i);

  if (inputCandidate) parsed.inputCandidate = Number(inputCandidate);
  if (outputCandidate) parsed.outputCandidate = Number(outputCandidate);
  if (relayCandidate) parsed.relayCandidate = Number(relayCandidate);
  if (buttonCandidate) parsed.buttonCandidate = Number(buttonCandidate);

  if (lower.includes('on')) parsed.stateCandidate = 'on';
  if (lower.includes('off')) parsed.stateCandidate = 'off';
  if (lower.includes('up')) parsed.motionCandidate = 'up';
  if (lower.includes('down')) parsed.motionCandidate = 'down';
  if (lower.includes('stop')) parsed.motionCandidate = 'stop';

  return parsed;
}

function makeRecord(config, direction, raw, extra = {}) {
  return Object.assign({
    timestamp: nowIso(),
    deviceName: config.name,
    host: config.host,
    port: config.port,
    direction,
    raw,
  }, extra);
}

class ExtronWatcher {
  constructor(config, logs) {
    this.config = config;
    this.logs = logs;
    this.socket = null;
    this.connected = false;
    this.closing = false;
    this.rxBuffer = '';
    this.reconnectDelay = config.reconnectMinMs;
    this.keepaliveTimer = null;
    this.pollTimer = null;
    this.runId = `${stampForFile()}-${process.pid}`;
  }

  start() {
    this.status('starting', {
      rawPath: this.logs.rawPath,
      jsonlPath: this.logs.jsonlPath,
      linesPath: this.logs.linesPath,
      runId: this.runId,
    });
    this.connect();
    if (this.config.stdin) this.attachStdin();
  }

  connect() {
    if (this.closing) return;

    this.status('connecting');
    const socket = net.createConnection({ host: this.config.host, port: this.config.port });
    this.socket = socket;
    socket.setKeepAlive(true, 30000);

    socket.on('connect', () => {
      this.connected = true;
      this.reconnectDelay = this.config.reconnectMinMs;
      this.status('connected');
      this.startTimers();
      for (const command of this.config.init) this.send(command, 'init');
    });

    socket.on('data', (chunk) => this.onData(chunk));
    socket.on('error', (err) => this.status('socket-error', { message: err.message, code: err.code }));
    socket.on('close', (hadError) => {
      this.connected = false;
      this.stopTimers();
      this.status('closed', { hadError });
      if (!this.closing && this.config.reconnect) this.scheduleReconnect();
    });
  }

  scheduleReconnect() {
    const delay = this.reconnectDelay;
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.config.reconnectMaxMs);
    this.status('reconnect-scheduled', { delayMs: delay });
    setTimeout(() => this.connect(), delay);
  }

  startTimers() {
    this.stopTimers();

    if (this.config.keepalive) {
      this.keepaliveTimer = setInterval(() => {
        this.send(this.config.keepalive, 'keepalive');
      }, this.config.keepaliveMs);
    }

    if (this.config.poll.length > 0) {
      this.pollTimer = setInterval(() => {
        for (const command of this.config.poll) this.send(command, 'poll');
      }, this.config.pollMs);
    }
  }

  stopTimers() {
    if (this.keepaliveTimer) clearInterval(this.keepaliveTimer);
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.keepaliveTimer = null;
    this.pollTimer = null;
  }

  attachStdin() {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout, prompt: 'extron> ' });
    rl.prompt();
    rl.on('line', (line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        rl.prompt();
        return;
      }
      if (trimmed === '.quit' || trimmed === '.exit') {
        this.shutdown();
        return;
      }
      this.send(trimmed, 'stdin');
      rl.prompt();
    });
  }

  send(command, reason = 'command') {
    if (!this.socket || !this.connected) {
      this.status('send-skipped-not-connected', { command, reason });
      return false;
    }

    const lineEnding = this.config.sendCrLf ? '\r\n' : '\n';
    const payload = String(command).endsWith('\n') ? String(command) : String(command) + lineEnding;
    this.socket.write(payload);

    if (this.config.echoTx) {
      const record = makeRecord(this.config, 'tx', String(command), { reason, runId: this.runId });
      this.logs.raw.write(`[${record.timestamp}] TX ${reason}: ${command}${os.EOL}`);
      writeJsonLine(this.logs.jsonl, record);
      console.log(`[TX/${reason}] ${command}`);
    }
    return true;
  }

  onData(chunk) {
    const cleaned = this.config.stripTelnetNegotiation ? stripTelnetNegotiationBytes(chunk) : chunk;
    const text = cleaned.toString('utf8');
    if (!text) return;

    this.logs.raw.write(`[${nowIso()}] RX-CHUNK ${JSON.stringify(text)}${os.EOL}`);
    this.rxBuffer += text;

    const parts = this.rxBuffer.split(/\r\n|\n|\r/g);
    this.rxBuffer = parts.pop();

    for (const part of parts) this.handleLine(part);
  }

  handleLine(line) {
    const parsed = classifyExtronLine(line);
    const record = makeRecord(this.config, 'rx', line, { parsed, runId: this.runId });

    this.logs.lines.write(`${record.timestamp}\t${line}${os.EOL}`);
    writeJsonLine(this.logs.jsonl, record);

    if (parsed.category === 'blank') return;
    const label = parsed.category === 'raw' ? 'RX' : `RX/${parsed.category}`;
    console.log(`[${label}] ${line}`);
  }

  status(status, extra = {}) {
    const record = makeRecord(this.config, 'status', status, Object.assign({ runId: this.runId }, extra));
    this.logs.raw.write(`[${record.timestamp}] STATUS ${status} ${JSON.stringify(extra)}${os.EOL}`);
    writeJsonLine(this.logs.jsonl, record);
    console.log(`[STATUS] ${status}`, Object.keys(extra).length ? extra : '');
  }

  shutdown() {
    if (this.closing) return;
    this.closing = true;
    this.status('shutdown-requested');
    this.stopTimers();

    if (this.socket) {
      try { this.socket.end(); } catch (_) { /* ignore */ }
      try { this.socket.destroy(); } catch (_) { /* ignore */ }
    }

    for (const stream of [this.logs.raw, this.logs.jsonl, this.logs.lines]) {
      try { stream.end(); } catch (_) { /* ignore */ }
    }

    setTimeout(() => process.exit(0), 250);
  }
}

function main() {
  let cli;
  try {
    cli = parseArgs(process.argv.slice(2));
    const fileConfig = readConfig(cli.config);
    const config = normalizeConfig(Object.assign({}, fileConfig, cli));
    const logs = openLogs(config);
    const watcher = new ExtronWatcher(config, logs);

    process.on('SIGINT', () => watcher.shutdown());
    process.on('SIGTERM', () => watcher.shutdown());

    watcher.start();
  } catch (err) {
    console.error(`ERROR: ${err.message}`);
    console.error('Run with --help for usage.');
    process.exit(1);
  }
}

main();
