---
kind: gate-step
id: "gate-step:inspector.07"
title: "Lane controls"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:273"
extractor: "workflows"
tags: [protected]
aliases:
  - "Lane controls"
  - "inspector.07"
generated: true
---

# Lane controls

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:273`

## Statement

uv run pytest harness/lane

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/lane |
| `kind` | run |
| `ordinal` | 7 |

## Binds

- **runs** → [[module__harness_lane|harness.lane]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
