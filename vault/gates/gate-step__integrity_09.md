---
kind: gate-step
id: "gate-step:integrity.09"
title: "Cross-stage invariants hold"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:94"
extractor: "workflows"
tags: [protected]
aliases:
  - "Cross-stage invariants hold"
  - "integrity.09"
generated: true
---

# Cross-stage invariants hold

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:94`

## Statement

python3 scripts/lint_invariants.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_invariants.py |
| `kind` | run |
| `ordinal` | 9 |

## Binds

- **runs** → [[module__scripts_lint_invariants|Cross-stage invariants (I1–I17), and the map of what actually enforces each one.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
