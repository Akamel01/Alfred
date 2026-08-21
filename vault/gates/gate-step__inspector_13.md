---
kind: gate-step
id: "gate-step:inspector.13"
title: "Patch gate (protected paths, A10 invisibles, import hooks)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:294"
extractor: "workflows"
tags: [protected]
aliases:
  - "Patch gate (protected paths, A10 invisibles, import hooks)"
  - "inspector.13"
generated: true
---

# Patch gate (protected paths, A10 invisibles, import hooks)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:294`

## Statement

uv run pytest harness/patch

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/patch |
| `kind` | run |
| `ordinal` | 13 |

## Binds

- **runs** → [[module__harness_patch|harness.patch]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
