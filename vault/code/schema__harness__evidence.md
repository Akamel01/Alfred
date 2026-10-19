---
kind: schema
id: "schema:harness/evidence"
title: "harness/evidence"
shape: "migration-tree"
protected: "true"
agent_migratable: "false"
source: "migrations/harness/evidence:1"
extractor: "schema"
tags: [protected]
aliases:
  - "harness/evidence"
generated: true
---

# harness/evidence

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/harness/evidence:1`

## Fields

| Field | Value |
|---|---|
| `additive_only_lint` | true |
| `migrations` | 1 |
| `path` | migrations/harness/evidence |

## Binds

- **contains** → [[schema__harness__evidence__0001_evidence_base|0001_evidence_base]]
