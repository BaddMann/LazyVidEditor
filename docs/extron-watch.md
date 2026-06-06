# Extron Watcher

`node-loggers/extron-watch.js` is a modern replacement for the older `extron-test.js` raw Telnet experiment.

It connects to an Extron device over Telnet/SIS, captures the raw stream, and writes normalized JSONL events that can later be used for LazyVidEditor, Companion helper scripts, or after-show automation.

## Why this exists

The old logger proved the concept, but it mixed Telnet stream handling, console output, and file logging in a way that made it hard to answer the practical question:

> What did the Extron actually do during the show?

This watcher writes three files per run:

```text
logs/YYYY-MM-DD_HH-MM-SS-room-extron-raw.log
logs/YYYY-MM-DD_HH-MM-SS-room-extron-events.jsonl
logs/YYYY-MM-DD_HH-MM-SS-room-extron-lines.txt
```

## Quick start

Copy the example config:

```bash
cp config/extron-watch.example.json config/extron-watch.local.json
```

Edit `config/extron-watch.local.json` and set the Extron host.

Run:

```bash
node node-loggers/extron-watch.js --config config/extron-watch.local.json
```

Or run without a config:

```bash
node node-loggers/extron-watch.js --host EXTRON_IP_OR_DNS_HERE --stdin
```

## Interactive mode

When `stdin` is enabled, you can type commands into the terminal and they will be sent to the Extron.

```text
extron> Q
extron> W1CV
extron> .exit
```

Every transmit command is written to the JSONL file with `direction: "tx"`.

## Output types

The JSONL file contains one JSON object per line.

Status records:

```json
{"timestamp":"2026-05-09T18:00:00.000Z","deviceName":"room-extron","direction":"status","raw":"connected"}
```

Transmit records:

```json
{"timestamp":"2026-05-09T18:00:01.000Z","deviceName":"room-extron","direction":"tx","raw":"W1CV","reason":"init"}
```

Receive records:

```json
{"timestamp":"2026-05-09T18:00:02.000Z","deviceName":"room-extron","direction":"rx","raw":"Evt...","parsed":{"eventType":"ExtronEvent","category":"event"}}
```

## Parser behavior

The first pass parser is intentionally conservative. Extron models vary, so it does not pretend to know the exact meaning of every line.

It classifies likely events into broad categories:

- `event`
- `routing`
- `relay`
- `button`
- `screen`
- `display`
- `error`
- `raw`

After capturing a real show or test session, use the raw log to map exact strings to real meanings such as:

- screen up
- screen down
- projector power
- input switch
- wall panel button press
- relay closure

## Suggested Glencroft test flow

1. Start the watcher.
2. Press the wall panel screen up/down buttons.
3. Switch projector/display inputs.
4. Trigger any known Extron-controlled actions.
5. Stop the watcher.
6. Open the JSONL file and raw log.
7. Map the observed event strings to friendly names.

## Companion integration idea

Keep Companion doing fast ATEM work directly with the ATEM module.

Use this watcher for slower support tasks:

- after-show state logging
- projector/screen diagnostics
- confirming the wall panel generated an event
- future helper service for Companion status buttons

For direct Extron control from Companion, prefer the native Extron module if it matches the exact model. If not, trigger a local shell script or Node helper that sends the needed SIS command.
