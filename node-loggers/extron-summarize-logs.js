#!/usr/bin/env node
'use strict';

/**
 * Summarize historical LazyVidEditor log files.
 *
 * Designed for old `Sampleoutput/*-Slides.txt` files that mixed Q-SYS,
 * Extron, OBS, and timestamp heartbeat lines in one stream.
 *
 * Example:
 *   node node-loggers/extron-summarize-logs.js Sampleoutput/2017-06-25_09-40-Slides.txt
 *   node node-loggers/extron-summarize-logs.js "Sampleoutput/*.txt" --json out/extron-summary.json
 */

const fs = require('fs');
const path = require('path');

function usage(code) {
  console.log(`
Usage:
  node node-loggers/extron-summarize-logs.js <file-or-glob> [more files] [--json <file>]

Examples:
  node node-loggers/extron-summarize-logs.js Sampleoutput/2017-06-25_09-40-Slides.txt
  node node-loggers/extron-summarize-logs.js "Sampleoutput/*.txt" --json logs/historical-extron-summary.json

Notes:
  The glob support is intentionally simple and supports folder/*.ext patterns.
`.trim());
  process.exit(code);
}

function parseArgs(argv) {
  const inputs = [];
  const options = { json: '' };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') usage(0);
    if (arg === '--json') {
      if (i + 1 >= argv.length) throw new Error('Missing value for --json');
      options.json = argv[++i];
      continue;
    }
    inputs.push(arg);
  }
  if (inputs.length === 0) usage(1);
  return { inputs, options };
}

function expandInput(input) {
  if (!input.includes('*')) return [input];

  const dir = path.dirname(input);
  const base = path.basename(input);
  const escaped = base
    .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
    .replace(/\*/g, '.*');
  const re = new RegExp(`^${escaped}$`, 'i');
  const resolvedDir = dir === '.' ? process.cwd() : dir;

  if (!fs.existsSync(resolvedDir)) return [];
  return fs.readdirSync(resolvedDir)
    .filter((name) => re.test(name))
    .map((name) => path.join(resolvedDir, name));
}

function isTimestampLine(line) {
  return /^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*$/.test(line);
}

function classify(line) {
  const trimmed = String(line || '').trim();
  const lower = trimmed.toLowerCase();

  if (!trimmed) return { category: 'blank', key: 'blank' };
  if (isTimestampLine(trimmed)) return { category: 'timestamp', key: 'timestamp' };

  if (/^evt\d+/i.test(trimmed)) {
    const evtCode = (trimmed.match(/^(Evt\d+)/i) || [null, 'Evt'])[1];
    return { category: 'extron-event', key: evtCode, family: 'extron' };
  }

  if (/\brly\d*\b/i.test(trimmed) || /\brelay\b/i.test(trimmed)) {
    const relay = (trimmed.match(/\b(Rly\d*)\b/i) || [null, 'Relay'])[1];
    return { category: 'extron-relay', key: relay, family: 'extron' };
  }

  if (/^cpn\d+/i.test(trimmed)) {
    const component = (trimmed.match(/^(Cpn\d+)/i) || [null, 'Cpn'])[1];
    return { category: 'extron-component', key: component, family: 'extron' };
  }

  if (/^cv\s+"/i.test(trimmed)) {
    const controlName = (trimmed.match(/^cv\s+"([^"]+)"/i) || [null, 'cv'])[1];
    return { category: 'qsys-control', key: controlName, family: 'qsys' };
  }

  if (/^sr\s+"/i.test(trimmed)) {
    return { category: 'qsys-status', key: 'sr', family: 'qsys' };
  }

  if (/recording(starting|started|stopping|stopped)/i.test(trimmed)) {
    const rec = (trimmed.match(/Recording(?:Starting|Started|Stopping|Stopped)/i) || [null, 'Recording'])[0];
    return { category: 'obs-recording', key: rec, family: 'obs' };
  }

  if (/rec-timecode/i.test(trimmed)) return { category: 'obs-timecode', key: 'rec-timecode', family: 'obs' };

  if (/extron|ipcp|copyright 20\d\d, extron/i.test(trimmed)) {
    return { category: 'extron-banner', key: 'banner', family: 'extron' };
  }

  return { category: 'other', key: trimmed.slice(0, 80) };
}

function addExample(bucket, example, limit = 5) {
  if (bucket.examples.length >= limit) return;
  bucket.examples.push(example);
}

function summarizeFile(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  const lines = text.split(/\r\n|\n|\r/g);
  const summary = {
    file: filePath,
    lineCount: lines.length,
    categories: {},
    keys: {},
    extronEvents: {},
    firstTimestamp: null,
    lastTimestamp: null,
  };

  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    const trimmed = line.trim();
    const info = classify(trimmed);

    if (info.category === 'timestamp') {
      if (!summary.firstTimestamp) summary.firstTimestamp = trimmed;
      summary.lastTimestamp = trimmed;
    }

    if (!summary.categories[info.category]) {
      summary.categories[info.category] = { count: 0, examples: [] };
    }
    summary.categories[info.category].count += 1;
    addExample(summary.categories[info.category], { lineNumber: index + 1, text: trimmed });

    const keyName = `${info.category}:${info.key}`;
    if (!summary.keys[keyName]) {
      summary.keys[keyName] = { count: 0, category: info.category, key: info.key, examples: [] };
    }
    summary.keys[keyName].count += 1;
    addExample(summary.keys[keyName], { lineNumber: index + 1, text: trimmed });

    if (info.category === 'extron-event') {
      if (!summary.extronEvents[info.key]) summary.extronEvents[info.key] = { count: 0, examples: [] };
      summary.extronEvents[info.key].count += 1;
      addExample(summary.extronEvents[info.key], { lineNumber: index + 1, text: trimmed });
    }
  }

  return summary;
}

function printSummary(summaries) {
  for (const summary of summaries) {
    console.log('\n' + '='.repeat(80));
    console.log(summary.file);
    console.log(`Lines: ${summary.lineCount}`);
    console.log(`Time:  ${summary.firstTimestamp || '(none)'} -> ${summary.lastTimestamp || '(none)'}`);

    console.log('\nCategories:');
    for (const [name, data] of Object.entries(summary.categories).sort((a, b) => b[1].count - a[1].count)) {
      console.log(`  ${String(data.count).padStart(6)}  ${name}`);
    }

    const extronKeys = Object.entries(summary.keys)
      .filter(([, data]) => data.category.startsWith('extron'))
      .sort((a, b) => b[1].count - a[1].count);

    if (extronKeys.length > 0) {
      console.log('\nExtron-ish keys:');
      for (const [, data] of extronKeys.slice(0, 20)) {
        console.log(`  ${String(data.count).padStart(6)}  ${data.category}:${data.key}`);
        for (const ex of data.examples.slice(0, 2)) {
          console.log(`          L${ex.lineNumber}: ${ex.text}`);
        }
      }
    }
  }
}

function main() {
  try {
    const { inputs, options } = parseArgs(process.argv.slice(2));
    const files = Array.from(new Set(inputs.flatMap(expandInput))).filter((file) => fs.existsSync(file));

    if (files.length === 0) throw new Error('No input files found');

    const summaries = files.map(summarizeFile);
    printSummary(summaries);

    if (options.json) {
      const outPath = path.resolve(options.json);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, JSON.stringify({ generatedAt: new Date().toISOString(), summaries }, null, 2));
      console.log(`\nWrote JSON summary: ${outPath}`);
    }
  } catch (err) {
    console.error(`ERROR: ${err.message}`);
    process.exit(1);
  }
}

main();
