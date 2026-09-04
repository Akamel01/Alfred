---
kind: module
id: "module:scripts.lint_invariants"
title: "Cross-stage invariants (I1–I17), and the map of what actually enforces each one."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_invariants.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Cross-stage invariants (I1–I17), and the map of what actually enforces each one."
  - "scripts.lint_invariants"
generated: true
---

# Cross-stage invariants (I1–I17), and the map of what actually enforces each one.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_invariants.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_invariants.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_09|Cross-stage invariants hold]] **runs** → this
- [[gate-step__integrity_10|Invariant lint detects planted violations]] **runs** → this

## Enforced by (code)

- [[decision__D13|Python throughout]] **enforced_by** → this — "no long-running endpoint exists yet; S8 under D13"
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """Cross-stage invariants (I1–I17), and the map of what actually enforces each one.

`docs/tier1/cross-stage-invariants.
