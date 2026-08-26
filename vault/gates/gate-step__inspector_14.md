---
kind: gate-step
id: "gate-step:inspector.14"
title: "Verdict vocabulary (words, stamp bridge table, authority bindings)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:315"
extractor: "workflows"
tags: [protected]
aliases:
  - "Verdict vocabulary (words, stamp bridge table, authority bindings)"
  - "inspector.14"
generated: true
---

# Verdict vocabulary (words, stamp bridge table, authority bindings)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:315`

## Statement

uv run pytest harness/verdicts

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/verdicts |
| `kind` | run |
| `ordinal` | 14 |

## Binds

- **runs** → [[module__harness_verdicts|harness.verdicts]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
