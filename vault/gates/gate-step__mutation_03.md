---
kind: gate-step
id: "gate-step:mutation.03"
title: "Sync dependencies from the lockfile"
shape: "step"
job: "mutation"
source: ".github/workflows/gates.yml:405"
extractor: "workflows"
tags: [protected]
aliases:
  - "Sync dependencies from the lockfile"
  - "mutation.03"
generated: true
---

# Sync dependencies from the lockfile

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:405`

## Statement

uv sync --frozen --all-extras --dev

## Fields

| Field | Value |
|---|---|
| `command` | uv sync --frozen --all-extras --dev |
| `kind` | run |
| `ordinal` | 3 |

## Binds

- [[gate__mutation|mutation control (the suite's own negative control)]] **contains** → this
