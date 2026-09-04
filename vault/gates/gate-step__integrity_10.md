---
kind: gate-step
id: "gate-step:integrity.10"
title: "Invariant lint detects planted violations"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:98"
extractor: "workflows"
tags: [protected]
aliases:
  - "Invariant lint detects planted violations"
  - "integrity.10"
generated: true
---

# Invariant lint detects planted violations

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:98`

## Statement

python3 scripts/lint_invariants.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_invariants.py --self-test |
| `kind` | run |
| `ordinal` | 10 |

## Binds

- **runs** → [[module__scripts_lint_invariants|Cross-stage invariants (I1–I17), and the map of what actually enforces each one.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
