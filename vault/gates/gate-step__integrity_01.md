---
kind: gate-step
id: "gate-step:integrity.01"
title: "Install uv"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:43"
extractor: "workflows"
tags: [protected]
aliases:
  - "Install uv"
  - "integrity.01"
generated: true
---

# Install uv

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:43`

## Statement

astral-sh/setup-uv@v5

## Fields

| Field | Value |
|---|---|
| `command` | astral-sh/setup-uv@v5 |
| `kind` | action |
| `ordinal` | 1 |

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
