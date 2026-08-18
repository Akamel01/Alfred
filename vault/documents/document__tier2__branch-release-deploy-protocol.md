---
kind: document
id: "document:tier2/branch-release-deploy-protocol"
title: "Branch, Release and Deploy Protocol"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "2"
written: "stub"
review_after: "Phase 2"
source: "docs/tier2/branch-release-deploy-protocol.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier2]
aliases:
  - "Branch, Release and Deploy Protocol"
  - "tier2/branch-release-deploy-protocol"
generated: true
---

# Branch, Release and Deploy Protocol

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/branch-release-deploy-protocol.md:1`

## Falsifies if

> A deploy occurs by any path other than CI on merge.

## Fields

| Field | Value |
|---|---|
| `evidence` | none — written pre-Phase-0 as a register stub (D32) |
| `path` | docs/tier2/branch-release-deploy-protocol.md |
| `tier_name` | Build protocol |

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
