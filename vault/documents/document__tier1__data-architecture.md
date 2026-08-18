---
kind: document
id: "document:tier1/data-architecture"
title: "Data Architecture"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "schema"
tier: "1"
written: "full"
review_after: "Phase 2"
source: "docs/tier1/data-architecture.md:1"
extractor: "documents"
tags: [executable, schema, tier1]
aliases:
  - "Data Architecture"
  - "tier1/data-architecture"
generated: true
---

# Data Architecture

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/data-architecture.md:1`

## Falsifies if

> An agent-role connection succeeds against a held-out, verdict or policy table; or an evidence row is found mutated after write; or the observed grant set differs from the declared matrix in any direction, an extra grant included; or Phase 2 asks a question of the golden set, the taxonomy or the cost attribution that the tables specified here cannot answer without re-running Phase 1.

## Fields

| Field | Value |
|---|---|
| `evidence` | The role split and the separate held-out table are required because graph-level visibility controls were found not to constitute a boundary; the hash chain is required because append-only alone does not survive a single login compromise. The Phase 2 tables section rests on no observation at all — it is written against D25/D29/D35/D40/D49 and Phase 1 is its first test; it is included only where the |
| `path` | docs/tier1/data-architecture.md |
| `tier_name` | Architecture |

## Binds

- [[tier__tier1|Tier 1 — Architecture]] **contains** → this
