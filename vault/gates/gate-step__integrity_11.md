---
kind: gate-step
id: "gate-step:integrity.11"
title: "Vault and published graph are current"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:134"
extractor: "workflows"
tags: [protected]
aliases:
  - "Vault and published graph are current"
  - "integrity.11"
generated: true
---

# Vault and published graph are current

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:134`

## Statement

python3 tools/gen_vault.py --check

## Fields

| Field | Value |
|---|---|
| `command` | python3 tools/gen_vault.py --check |
| `kind` | run |
| `ordinal` | 11 |

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
