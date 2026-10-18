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

- [[gate-step__integrity_24|Topology lint checks its own vacuity]] **runs** → this
- [[gate-step__integrity_25|Topology file is valid]] **runs** → this

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """TOP010-TOP013. The palette says which roles exist; the bindings say which ones run.

    This is a two-file invariant
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # TOP014 -- a requalification may not report pass while the D19 fields are unset.
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — "TOP014 requalification reports 'pass' while D19 version fields are 'unset'"
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — "no dispatcher; D19 fields unset"
