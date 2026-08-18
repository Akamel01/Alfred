---
kind: gate-step
id: "gate-step:inspector.08"
title: "Containment probes (C6 egress canary, C7 oracle absence)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:218"
extractor: "workflows"
tags: [protected]
aliases:
  - "Containment probes (C6 egress canary, C7 oracle absence)"
  - "inspector.08"
generated: true
---

# Containment probes (C6 egress canary, C7 oracle absence)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:218`

## Statement

uv run pytest harness/containment

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/containment |
| `kind` | run |
| `ordinal` | 8 |

## Binds

- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
