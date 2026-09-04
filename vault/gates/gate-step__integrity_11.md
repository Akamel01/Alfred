---
kind: gate-step
id: "gate-step:integrity.11"
title: "Verdict boundary holds"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:107"
extractor: "workflows"
tags: [protected]
aliases:
  - "Verdict boundary holds"
  - "integrity.11"
generated: true
---

# Verdict boundary holds

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:107`

## Statement

python3 scripts/lint_verdict_boundary.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_verdict_boundary.py |
| `kind` | run |
| `ordinal` | 11 |

## Binds

- **runs** → [[module__scripts_lint_verdict_boundary|D16/D39: the verdict boundary, enforced structurally rather than by convention.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
