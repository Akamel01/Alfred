---
kind: gate-step
id: "gate-step:integrity.24"
title: "Topology file is valid"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:224"
extractor: "workflows"
tags: [protected]
aliases:
  - "Topology file is valid"
  - "integrity.24"
generated: true
---

# Topology file is valid

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:224`

## Statement

python3 scripts/lint_topology.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_topology.py |
| `kind` | run |
| `ordinal` | 24 |

## Binds

- **runs** → [[module__scripts_lint_topology|Topology lint — TOP001-TOP009 per orchestration-canvas-spec §6.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
