---
kind: gate-step
id: "gate-step:integrity.12"
title: "Vault generator suites"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:137"
extractor: "workflows"
tags: [protected]
aliases:
  - "Vault generator suites"
  - "integrity.12"
generated: true
---

# Vault generator suites

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:137`

## Statement

uv run pytest tools/tests

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest tools/tests |
| `kind` | run |
| `ordinal` | 12 |

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
