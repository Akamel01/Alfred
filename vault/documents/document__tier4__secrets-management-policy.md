---
kind: document
id: "document:tier4/secrets-management-policy"
title: "Secrets Management Policy"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "4"
written: "full"
review_after: "Phase 2"
source: "docs/tier4/secrets-management-policy.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier4]
aliases:
  - "Secrets Management Policy"
  - "tier4/secrets-management-policy"
generated: true
---

# Secrets Management Policy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier4/secrets-management-policy.md:1`

## Falsifies if

> Any credential is found reachable from agent context, or a secret is discovered outside the declared inventory.

## Fields

| Field | Value |
|---|---|
| `evidence` | A pull-request-opening flow has been used to exfiltrate a token within eight minutes of the PR being opened. Repository-scoped CI caches survive container ephemerality, so ephemerality alone does not contain a leaked secret. |
| `path` | docs/tier4/secrets-management-policy.md |
| `tier_name` | Security and governance |

## Binds

- [[tier__tier4|Tier 4 — Security and governance]] **contains** → this
