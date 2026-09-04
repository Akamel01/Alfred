---
kind: gate-step
id: "gate-step:integrity.23"
title: "Topology lint checks its own vacuity"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:221"
extractor: "workflows"
tags: [protected]
aliases:
  - "Topology lint checks its own vacuity"
  - "integrity.23"
generated: true
---

# Topology lint checks its own vacuity

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:221`

## Statement

python3 scripts/lint_topology.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_topology.py --self-test |
| `kind` | run |
| `ordinal` | 23 |

## Binds

- **runs** → [[module__scripts_lint_topology|Topology lint — TOP001-TOP009 per orchestration-canvas-spec §6.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
