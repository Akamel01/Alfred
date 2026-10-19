---
kind: schema
id: "schema:harness/heldout"
title: "harness/heldout"
shape: "migration-tree"
protected: "true"
agent_migratable: "false"
source: "migrations/harness/heldout:1"
extractor: "schema"
tags: [protected]
aliases:
  - "harness/heldout"
generated: true
---

# harness/heldout

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/harness/heldout:1`

## Fields

| Field | Value |
|---|---|
| `additive_only_lint` | true |
| `migrations` | 1 |
| `path` | migrations/harness/heldout |

## Binds

- **contains** → [[schema__harness__heldout__0001_heldout_base|0001_heldout_base]]
