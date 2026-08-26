---
kind: gate-step
id: "gate-step:inspector.15"
title: "Run fingerprint record (field set, derived digest, register agreement)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:339"
extractor: "workflows"
tags: [protected]
aliases:
  - "Run fingerprint record (field set, derived digest, register agreement)"
  - "inspector.15"
generated: true
---

# Run fingerprint record (field set, derived digest, register agreement)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:339`

## Statement

uv run pytest harness/fingerprint

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/fingerprint |
| `kind` | run |
| `ordinal` | 15 |

## Binds

- **runs** → [[module__harness_fingerprint|harness.fingerprint]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
