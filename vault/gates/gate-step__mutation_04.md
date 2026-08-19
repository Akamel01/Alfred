---
kind: gate-step
id: "gate-step:mutation.04"
title: "ACS-1 mutation control"
shape: "step"
job: "mutation"
source: ".github/workflows/gates.yml:320"
extractor: "workflows"
tags: [protected]
aliases:
  - "ACS-1 mutation control"
  - "mutation.04"
generated: true
---

# ACS-1 mutation control

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:320`

## Statement

uv run python harness/acs/mutate.py

## Fields

| Field | Value |
|---|---|
| `command` | uv run python harness/acs/mutate.py |
| `kind` | run |
| `ordinal` | 4 |

## Binds

- **runs** → [[module__harness_acs_mutate|Mutation control for the ACS-1 conformance suite.]]
- [[gate__mutation|mutation control (the suite's own negative control)]] **contains** → this
