---
kind: gate-step
id: "gate-step:inspector.12"
title: "Worker port (claim/fault split, containment refusals)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:291"
extractor: "workflows"
tags: [protected]
aliases:
  - "Worker port (claim/fault split, containment refusals)"
  - "inspector.12"
generated: true
---

# Worker port (claim/fault split, containment refusals)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:291`

## Statement

uv run pytest harness/worker

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/worker |
| `kind` | run |
| `ordinal` | 12 |

## Binds

- **runs** → [[module__harness_worker|harness.worker]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
