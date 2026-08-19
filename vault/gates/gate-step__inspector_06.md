---
kind: gate-step
id: "gate-step:inspector.06"
title: "bench harness self-tests"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:231"
extractor: "workflows"
tags: [protected]
aliases:
  - "bench harness self-tests"
  - "inspector.06"
generated: true
---

# bench harness self-tests

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:231`

## Statement

uv run pytest bench

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest bench |
| `kind` | run |
| `ordinal` | 6 |

## Binds

- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
