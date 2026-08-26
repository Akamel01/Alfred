---
kind: gate-step
id: "gate-step:product.06"
title: "pytest — product"
shape: "step"
job: "product"
source: ".github/workflows/gates.yml:229"
extractor: "workflows"
tags: [protected]
aliases:
  - "product.06"
  - "pytest — product"
generated: true
---

# pytest — product

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:229`

## Statement

uv run pytest tests

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest tests |
| `kind` | run |
| `ordinal` | 6 |

## Binds

- [[gate__product|product (lint, types, tests)]] **contains** → this
