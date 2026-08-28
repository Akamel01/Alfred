---
kind: gate-step
id: "gate-step:database.05"
title: "EvidenceStore, chain re-walk, and the D-synthetic restore drill"
shape: "step"
job: "database"
source: ".github/workflows/gates.yml:396"
extractor: "workflows"
tags: [protected]
aliases:
  - "EvidenceStore, chain re-walk, and the D-synthetic restore drill"
  - "database.05"
generated: true
---

# EvidenceStore, chain re-walk, and the D-synthetic restore drill

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:396`

## Statement

uv run pytest harness/evidence

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/evidence |
| `kind` | run |
| `ordinal` | 5 |

## Binds

- **runs** → [[module__harness_evidence|harness.evidence]]
- [[gate__database|database (throwaway cluster, roles and grants)]] **contains** → this
