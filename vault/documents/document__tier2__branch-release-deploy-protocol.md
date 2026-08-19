---
kind: document
id: "document:tier2/branch-release-deploy-protocol"
title: "Branch, Release and Deploy Protocol"
status: "provisional"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "2"
written: "full"
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

> A deploy occurs by any path other than CI on merge; or a rollback is reported successful without the served release identity having been read back and matched; or a release is deployed whose identity is not baked into its artifact; or `harness/deploy/` records a ledger entry for a transition that did not take.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier2/branch-release-deploy-protocol.md |
| `tier_name` | Build protocol |

**evidence**

> S8, 2026-08-18. Two releases built, deployed and rolled back through `docker compose` on this machine, each transition verified by reading `/version` from the running service rather than by the exit code of the command that caused it. The branch and release halves rest on no observation: no agent branch has ever been opened, so everything below about patch flow is written against A2/D10 and Phase 1 is its first test.

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
