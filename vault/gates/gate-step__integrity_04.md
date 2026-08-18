---
kind: gate-step
id: "gate-step:integrity.04"
title: "Document header contract"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:59"
extractor: "workflows"
tags: [protected]
aliases:
  - "Document header contract"
  - "integrity.04"
generated: true
---

# Document header contract

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:59`

## Statement

python3 scripts/lint_docs.py --check

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_docs.py --check |
| `kind` | run |
| `ordinal` | 4 |

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
