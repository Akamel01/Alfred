---
kind: gate-step
id: "gate-step:inspector.04"
title: "ACS-1 — Python conformance"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:197"
extractor: "workflows"
tags: [protected]
aliases:
  - "ACS-1 — Python conformance"
  - "inspector.04"
generated: true
---

# ACS-1 — Python conformance

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:197`

## Statement

uv run pytest harness/acs

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/acs |
| `kind` | run |
| `ordinal` | 4 |

## Binds

- **runs** → [[module__harness_acs|harness.acs]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
