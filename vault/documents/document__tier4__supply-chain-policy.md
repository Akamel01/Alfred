---
kind: document
id: "document:tier4/supply-chain-policy"
title: "Supply Chain Policy"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "4"
written: "full"
review_after: "Phase 2"
source: "docs/tier4/supply-chain-policy.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier4]
aliases:
  - "Supply Chain Policy"
  - "tier4/supply-chain-policy"
generated: true
---

# Supply Chain Policy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier4/supply-chain-policy.md:1`

## Falsifies if

> A dependency, image or model artifact resolves to content other than its pinned hash, or a behaviour change is traced to a component whose identity was believed pinned.

## Fields

| Field | Value |
|---|---|
| `evidence` | An unconstrained dependency has broken a graph library's tool node in a patch release. Identical model weights have produced opposite tool-calling outcomes on different serving stacks. Imatrix quantization variants share names while differing in content. |
| `path` | docs/tier4/supply-chain-policy.md |
| `tier_name` | Security and governance |

## Binds

- [[tier__tier4|Tier 4 — Security and governance]] **contains** → this
