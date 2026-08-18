---
kind: document
id: "document:tier2/coding-standards"
title: "Coding Standards"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "2"
written: "full"
review_after: "Phase 2"
source: "docs/tier2/coding-standards.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier2]
aliases:
  - "Coding Standards"
  - "tier2/coding-standards"
generated: true
---

# Coding Standards

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/coding-standards.md:1`

## Falsifies if

> Merged code carries a type suppression without a recorded justification, or the agent's output requires routine style correction in review — meaning the conventions are not reaching it.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier2/coding-standards.md |
| `tier_name` | Build protocol |

**evidence**

> Strict typing is enforced now because retrofitting it onto a grown codebase is impractical; the agent inherits Phase 0's conventions, so conventions set before Phase 1 are the ones that propagate.

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
