---
kind: gate-step
id: "gate-step:inspector.10"
title: "Oracle boundary (pins, refusals, admissibility)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:259"
extractor: "workflows"
tags: [protected]
aliases:
  - "Oracle boundary (pins, refusals, admissibility)"
  - "inspector.10"
generated: true
---

# Oracle boundary (pins, refusals, admissibility)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:259`

## Statement

uv run pytest harness/oracle

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/oracle |
| `kind` | run |
| `ordinal` | 10 |

## Binds

- **runs** → [[module__harness_oracle|harness.oracle]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
