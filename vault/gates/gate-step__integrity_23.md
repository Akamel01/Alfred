---
kind: gate-step
id: "gate-step:integrity.23"
title: "Orchestration canvas is current"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:213"
extractor: "workflows"
tags: [protected]
aliases:
  - "Orchestration canvas is current"
  - "integrity.23"
generated: true
---

# Orchestration canvas is current

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:213`

## Statement

python3 tools/orchestration/gen_canvas.py --check

## Fields

| Field | Value |
|---|---|
| `command` | python3 tools/orchestration/gen_canvas.py --check |
| `kind` | run |
| `ordinal` | 23 |

## Binds

- **runs** → [[module__tools_orchestration_gen_canvas|Factory generator for orchestration canvas.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
