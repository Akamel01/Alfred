---
kind: gate-step
id: "gate-step:product.05"
title: "pyright --strict"
shape: "step"
job: "product"
source: ".github/workflows/gates.yml:259"
extractor: "workflows"
tags: [protected]
aliases:
  - "product.05"
  - "pyright --strict"
generated: true
---

# pyright --strict

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:259`

## Statement

uv run pyright

## Fields

| Field | Value |
|---|---|
| `command` | uv run pyright |
| `kind` | run |
| `ordinal` | 5 |

## Binds

- [[gate__product|product (lint, types, tests)]] **contains** → this
