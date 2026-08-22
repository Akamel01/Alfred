---
kind: module
id: "module:scripts.lint_adr_numbers"
title: "ADR number claim lint: a branch may not claim a number the base has issued."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_adr_numbers.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "ADR number claim lint: a branch may not claim a number the base has issued."
  - "scripts.lint_adr_numbers"
generated: true
---

# ADR number claim lint: a branch may not claim a number the base has issued.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_adr_numbers.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_adr_numbers.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_06|ADR numbers are claimed once]] **runs** → this
- [[gate-step__integrity_07|ADR number lint detects planted collisions]] **runs** → this
