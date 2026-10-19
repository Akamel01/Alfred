---
kind: schema
id: "schema:harness/control"
title: "harness/control"
shape: "migration-tree"
protected: "true"
agent_migratable: "false"
source: "migrations/harness/control:1"
extractor: "schema"
tags: [protected]
aliases:
  - "harness/control"
generated: true
---

# harness/control

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/harness/control:1`

## Fields

| Field | Value |
|---|---|
| `additive_only_lint` | false |
| `migrations` | 2 |
| `path` | migrations/harness/control |

## Binds

- **contains** → [[schema__harness__control__0001_control_base|0001_control_base]]
- **contains** → [[schema__harness__control__0002_fingerprint_run_fields|0002_fingerprint_run_fields]]
