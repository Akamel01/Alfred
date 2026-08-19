---
kind: module
id: "module:scripts.gen_reading_map"
title: "Generate docs/READING-MAP.md — what to read, when, and what it binds."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/gen_reading_map.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Generate docs/READING-MAP.md — what to read, when, and what it binds."
  - "scripts.gen_reading_map"
generated: true
---

# Generate docs/READING-MAP.md — what to read, when, and what it binds.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/gen_reading_map.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/gen_reading_map.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_05|Reading map current]] **runs** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — "ADR-0001 to 0008 constrain every metric signature, every hashed record, and the operator surface"
