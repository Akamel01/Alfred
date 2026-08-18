---
kind: document
id: "document:tier4/permission-and-identity-model"
title: "Permission and Identity Model"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "schema"
tier: "4"
written: "full"
review_after: "Phase 2"
source: "docs/tier4/permission-and-identity-model.md:1"
extractor: "documents"
tags: [executable, schema, tier4]
aliases:
  - "Permission and Identity Model"
  - "tier4/permission-and-identity-model"
generated: true
---

# Permission and Identity Model

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier4/permission-and-identity-model.md:1`

## Falsifies if

> An agent-role connection succeeds against a held-out, verdict or policy table, or any identity is found holding a permission not listed here.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier4/permission-and-identity-model.md |
| `tier_name` | Security and governance |

**evidence**

> Graph-level visibility controls were verified not to constitute a boundary — private state schemas do not hide channels from stream, output_keys is caller-side, and the checkpointer persists everything. The security property has to come from physical separation.

## Binds

- [[tier__tier4|Tier 4 — Security and governance]] **contains** → this
