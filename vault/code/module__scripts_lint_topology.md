---
kind: module
id: "module:scripts.lint_topology"
title: "Topology lint — TOP001-TOP009 per orchestration-canvas-spec §6."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_topology.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Topology lint — TOP001-TOP009 per orchestration-canvas-spec §6."
  - "scripts.lint_topology"
generated: true
---

# Topology lint — TOP001-TOP009 per orchestration-canvas-spec §6.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_topology.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_topology.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_23|Topology lint checks its own vacuity]] **runs** → this
- [[gate-step__integrity_24|Topology file is valid]] **runs** → this
