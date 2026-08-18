---
kind: gate-step
id: "gate-step:integrity.08"
title: "Verdict boundary lint detects planted violations"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:84"
extractor: "workflows"
tags: [protected]
aliases:
  - "Verdict boundary lint detects planted violations"
  - "integrity.08"
generated: true
---

# Verdict boundary lint detects planted violations

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:84`

## Statement

python3 scripts/lint_verdict_boundary.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_verdict_boundary.py --self-test |
| `kind` | run |
| `ordinal` | 8 |

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
