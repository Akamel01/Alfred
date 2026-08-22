---
kind: module
id: "module:scripts.lint_stage_gates"
title: "The stage gate, as a check rather than as a sentence somebody reads."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_stage_gates.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The stage gate, as a check rather than as a sentence somebody reads."
  - "scripts.lint_stage_gates"
generated: true
---

# The stage gate, as a check rather than as a sentence somebody reads.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_stage_gates.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_stage_gates.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_15|Stage gate register integrity]] **runs** → this
- [[gate-step__integrity_16|Stage gate lint detects planted violations]] **runs** → this

## Enforced by (code)

- [[adr__ADR-0022|Phase 0's exit, narrowed along the ownership seam, with the residue dated]] **enforced_by** → this — """The stage gate, as a check rather than as a sentence somebody reads.

`docs/tier2/stage-gate-definitions.md` carried 
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """The stage gate, as a check rather than as a sentence somebody reads.

`docs/tier2/stage-gate-definitions.md` carried 
