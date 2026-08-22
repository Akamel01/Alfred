---
kind: gate-step
id: "gate-step:inspector.14"
title: "Stamp (version, upstream union, total verifier)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:316"
extractor: "workflows"
tags: [protected]
aliases:
  - "Stamp (version, upstream union, total verifier)"
  - "inspector.14"
generated: true
---

# Stamp (version, upstream union, total verifier)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:316`

## Statement

uv run pytest harness/stamp

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/stamp |
| `kind` | run |
| `ordinal` | 14 |

## Binds

- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
