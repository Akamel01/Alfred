---
kind: gate-step
id: "gate-step:inspector.11"
title: "Deploy and rollback (ledger, identity, refusals)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:320"
extractor: "workflows"
tags: [protected]
aliases:
  - "Deploy and rollback (ledger, identity, refusals)"
  - "inspector.11"
generated: true
---

# Deploy and rollback (ledger, identity, refusals)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:320`

## Statement

uv run pytest harness/deploy

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/deploy |
| `kind` | run |
| `ordinal` | 11 |

## Binds

- **runs** → [[module__harness_deploy|harness.deploy]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
