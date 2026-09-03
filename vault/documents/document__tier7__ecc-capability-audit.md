---
kind: document
id: "document:tier7/ecc-capability-audit"
title: "ECC capability classification"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "the ECC2 reuse boundary decision"
source: "docs/tier7/ecc-capability-audit.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "ECC capability classification"
  - "tier7/ecc-capability-audit"
generated: true
---

# ECC capability classification

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ecc-capability-audit.md:1`

## Falsifies if

> A capability classified ECC-NATIVE turns out to require an Alfred-side adapter to be usable, or a capability classified REMOVE/REPLACE is found to be load-bearing for something Alfred already depends on.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ecc-capability-audit.md |
| `tier_name` | Meta |

**evidence**

> A read of ECC 2.2.1 at commit ca185ef (286 skills, 68 agents, 11 JSON schemas, the ecc2 Rust control plane, the AutoForge workspace) against Alfred's register as of 2026-09-02. Classification is from what the source does, never from what its documentation claims.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
