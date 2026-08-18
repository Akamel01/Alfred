---
kind: document
id: "document:tier4/audit-and-retention-policy"
title: "Audit and Retention Policy"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "4"
written: "full"
review_after: "Phase 2"
source: "docs/tier4/audit-and-retention-policy.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier4]
aliases:
  - "Audit and Retention Policy"
  - "tier4/audit-and-retention-policy"
generated: true
---

# Audit and Retention Policy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier4/audit-and-retention-policy.md:1`

## Falsifies if

> A restore drill fails, a chain-head anchor is missing for any day, or an evidence row is found whose hash does not match its predecessor link.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier4/audit-and-retention-policy.md |
| `tier_name` | Security and governance |

**evidence**

> Append-only defends against the agent and not against hardware failure, kernel-panic corruption, or a bad migration. For an audit-layer product, an unchained audit log is rewritable by anyone holding one login.

## Binds

- [[tier__tier4|Tier 4 — Security and governance]] **contains** → this
