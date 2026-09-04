---
kind: module
id: "module:scripts.lint_ci_coverage"
title: "Two claims of CI coverage, checked against what CI actually runs."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_ci_coverage.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Two claims of CI coverage, checked against what CI actually runs."
  - "scripts.lint_ci_coverage"
generated: true
---

# Two claims of CI coverage, checked against what CI actually runs.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_ci_coverage.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_ci_coverage.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_13|CI coverage (test directories, failure register)]] **runs** → this
- [[gate-step__integrity_14|CI coverage lint detects planted violations]] **runs** → this

## Enforced by (code)

- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """Two claims of CI coverage, checked against what CI actually runs.

`gates.yml` states the rule this file generalizes:
