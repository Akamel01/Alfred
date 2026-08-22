---
kind: gate-step
id: "gate-step:integrity.18"
title: "Vault generator detects its own vacuity"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:180"
extractor: "workflows"
tags: [protected]
aliases:
  - "Vault generator detects its own vacuity"
  - "integrity.18"
generated: true
---

# Vault generator detects its own vacuity

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:180`

## Statement

python3 tools/gen_vault.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 tools/gen_vault.py --self-test |
| `kind` | run |
| `ordinal` | 18 |

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
