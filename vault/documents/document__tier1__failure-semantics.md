---
kind: document
id: "document:tier1/failure-semantics"
title: "Failure Semantics and Error Handling"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "1"
written: "full"
review_after: "Phase 1"
source: "docs/tier1/failure-semantics.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier1]
aliases:
  - "Failure Semantics and Error Handling"
  - "tier1/failure-semantics"
generated: true
---

# Failure Semantics and Error Handling

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/failure-semantics.md:1`

## Falsifies if

> A run reaches a verdict while any control that gates it could not be shown to have executed, or a harness fault is recorded as an agent failure.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier1/failure-semantics.md |
| `tier_name` | Architecture |

**evidence**

> Two documented cases of controls failing open silently: an eval sandbox left with live internet access under a deny-by-default configuration, and an SDK that treated an empty settings-source list as omitted and loaded user configuration anyway. Both failed without signalling.

## Binds

- [[tier__tier1|Tier 1 — Architecture]] **contains** → this
