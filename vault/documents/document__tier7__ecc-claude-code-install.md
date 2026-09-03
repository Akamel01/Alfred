---
kind: document
id: "document:tier7/ecc-claude-code-install"
title: "ECC install for Claude Code — what was done and what it changed"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "the harness-portability decision"
source: "docs/tier7/ecc-claude-code-install.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "ECC install for Claude Code — what was done and what it changed"
  - "tier7/ecc-claude-code-install"
generated: true
---

# ECC install for Claude Code — what was done and what it changed

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ecc-claude-code-install.md:1`

## Falsifies if

> A second install of the same profile and commit produces a different operation set, or ECC hook runtime appears under ~/.claude without an explicit consent decision recorded.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ecc-claude-code-install.md |
| `tier_name` | Meta |

**evidence**

> A single install performed 2026-09-02 on one machine, with a pre-install inventory captured by hash and a dry-run diffed before apply. Nothing here is measured across machines or across ECC versions.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
