---
kind: gate-step
id: "gate-step:integrity.26"
title: "Vault generator suites"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:222"
extractor: "workflows"
tags: [protected]
aliases:
  - "Vault generator suites"
  - "integrity.26"
generated: true
---

# Vault generator suites

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:222`

## Statement

uv run pytest tools/tests

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest tools/tests |
| `kind` | run |
| `ordinal` | 26 |

## Binds

- **runs** → [[module__tools_tests|tools.tests]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
