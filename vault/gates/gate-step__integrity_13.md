---
kind: gate-step
id: "gate-step:integrity.13"
title: "CI coverage (test directories, failure register)"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:127"
extractor: "workflows"
tags: [protected]
aliases:
  - "CI coverage (test directories, failure register)"
  - "integrity.13"
generated: true
---

# CI coverage (test directories, failure register)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:127`

## Statement

python3 scripts/lint_ci_coverage.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_ci_coverage.py |
| `kind` | run |
| `ordinal` | 13 |

## Binds

- **runs** → [[module__scripts_lint_ci_coverage|Two claims of CI coverage, checked against what CI actually runs.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
