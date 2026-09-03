---
kind: gate-step
id: "gate-step:product.04"
title: "ruff"
shape: "step"
job: "product"
source: ".github/workflows/gates.yml:256"
extractor: "workflows"
tags: [protected]
aliases:
  - "product.04"
  - "ruff"
generated: true
---

# ruff

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:256`

## Statement

uv run ruff check

## Fields

| Field | Value |
|---|---|
| `command` | uv run ruff check |
| `kind` | run |
| `ordinal` | 4 |

## Binds

- [[gate__product|product (lint, types, tests)]] **contains** → this
