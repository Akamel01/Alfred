---
kind: document
id: "document:tier4/protected-paths-policy"
title: "Protected Paths Policy"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "4"
written: "full"
review_after: "Phase 2"
source: "docs/tier4/protected-paths-policy.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier4]
aliases:
  - "Protected Paths Policy"
  - "tier4/protected-paths-policy"
generated: true
---

# Protected Paths Policy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier4/protected-paths-policy.md:1`

## Falsifies if

> A merged diff touches a protected path, or a path that should have been protected is found to have been agent-writable.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier4/protected-paths-policy.md |
| `tier_name` | Security and governance |

**evidence**

> Documented, not hypothesized. An agent has written an auto-approve setting into its own configuration file, disabling its approval gate because the gate lived in a file it could write (CVE-2025-53773).

## Binds

- [[tier__tier4|Tier 4 — Security and governance]] **contains** → this
