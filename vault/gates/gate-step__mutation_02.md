---
kind: gate-step
id: "gate-step:mutation.02"
title: "Set up Python"
shape: "step"
job: "mutation"
source: ".github/workflows/gates.yml:398"
extractor: "workflows"
tags: [protected]
aliases:
  - "Set up Python"
  - "mutation.02"
generated: true
---

# Set up Python

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:398`

## Statement

uv python install ${{ env.PYTHON_VERSION }}

## Fields

| Field | Value |
|---|---|
| `command` | uv python install ${{ env.PYTHON_VERSION }} |
| `kind` | run |
| `ordinal` | 2 |

## Binds

- [[gate__mutation|mutation control (the suite's own negative control)]] **contains** → this
