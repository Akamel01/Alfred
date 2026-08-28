---
kind: gate-step
id: "gate-step:mutation.01"
title: "Install uv"
shape: "step"
job: "mutation"
source: ".github/workflows/gates.yml:414"
extractor: "workflows"
tags: [protected]
aliases:
  - "Install uv"
  - "mutation.01"
generated: true
---

# Install uv

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:414`

## Statement

astral-sh/setup-uv@v5

## Fields

| Field | Value |
|---|---|
| `command` | astral-sh/setup-uv@v5 |
| `kind` | action |
| `ordinal` | 1 |

## Binds

- [[gate__mutation|mutation control (the suite's own negative control)]] **contains** → this
