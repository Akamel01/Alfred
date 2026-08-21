---
kind: gate-step
id: "gate-step:inspector.08"
title: "Containment (C6, C7 probes; C8-C15; and the O5 shells that must not pass)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:266"
extractor: "workflows"
tags: [protected]
aliases:
  - "Containment (C6, C7 probes; C8-C15; and the O5 shells that must not pass)"
  - "inspector.08"
generated: true
---

# Containment (C6, C7 probes; C8-C15; and the O5 shells that must not pass)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:266`

## Statement

uv run pytest harness/containment

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/containment |
| `kind` | run |
| `ordinal` | 8 |

## Binds

- **runs** → [[module__harness_containment|harness.containment]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
