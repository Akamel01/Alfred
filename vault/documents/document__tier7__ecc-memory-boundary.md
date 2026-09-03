---
kind: document
id: "document:tier7/ecc-memory-boundary"
title: "ECC memory boundary against ADR-0032"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "the ECC2 reuse boundary decision"
source: "docs/tier7/ecc-memory-boundary.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "ECC memory boundary against ADR-0032"
  - "tier7/ecc-memory-boundary"
generated: true
---

# ECC memory boundary against ADR-0032

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ecc-memory-boundary.md:1`

## Falsifies if

> A mirrored record is found in Alfred's evidence chain without a canonical source pointer, or the instincts injection path is found active on a machine this project drives.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ecc-memory-boundary.md |
| `tier_name` | Meta |

**evidence**

> A read of the ECC unified-memory implementation at commit ca185ef — schemas/memory.schema.json, scripts/lib/memory-vault.js, and scripts/hooks/session-start.js — against ADR-0032's three invariants. Findings cite line ranges in that source, not the schema's self-description.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
