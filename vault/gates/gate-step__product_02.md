---
kind: gate-step
id: "gate-step:product.02"
title: "Set up Python"
shape: "step"
job: "product"
source: ".github/workflows/gates.yml:260"
extractor: "workflows"
tags: [protected]
aliases:
  - "Set up Python"
  - "product.02"
generated: true
---

# Set up Python

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:260`

## Statement

uv python install ${{ env.PYTHON_VERSION }}

## Fields

| Field | Value |
|---|---|
| `command` | uv python install ${{ env.PYTHON_VERSION }} |
| `kind` | run |
| `ordinal` | 2 |

## Binds

- [[gate__product|product (lint, types, tests)]] **contains** → this
