---
kind: document
id: "document:tier1/adr-log"
title: "ADR Log"
status: "frozen"
shape: "file"
owner: "human"
enforcement: "none"
tier: "1"
written: "full"
review_after: "Phase 4"
source: "docs/tier1/adr-log.md:1"
extractor: "documents"
tags: [human, none, tier1]
aliases:
  - "ADR Log"
  - "tier1/adr-log"
generated: true
---

# ADR Log

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1`

## Falsifies if

> An ADR is edited after publication rather than superseded.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier1/adr-log.md |
| `tier_name` | Architecture |

**evidence**

> One published ADR, whose decisive inputs were measured on this machine rather than argued: Pydantic v2's default serialization of infinity, and the cost of per-timestep objects against vectorized evaluation.

## Binds

- [[tier__tier1|Tier 1 — Architecture]] **contains** → this
