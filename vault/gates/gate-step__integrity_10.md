---
kind: gate-step
id: "gate-step:integrity.10"
title: "CI coverage lint detects planted violations"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:104"
extractor: "workflows"
tags: [protected]
aliases:
  - "CI coverage lint detects planted violations"
  - "integrity.10"
generated: true
---

# CI coverage lint detects planted violations

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:104`

## Statement

python3 scripts/lint_ci_coverage.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_ci_coverage.py --self-test |
| `kind` | run |
| `ordinal` | 10 |

## Binds

- **runs** → [[module__scripts_lint_ci_coverage|Two claims of CI coverage, checked against what CI actually runs.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
