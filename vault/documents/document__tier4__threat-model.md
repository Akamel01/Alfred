---
kind: document
id: "document:tier4/threat-model"
title: "Threat Model"
status: "frozen"
shape: "file"
owner: "human"
enforcement: "review-cadence"
tier: "4"
written: "full"
review_after: "Phase 2"
source: "docs/tier4/threat-model.md:1"
extractor: "documents"
tags: [human, review-cadence, tier4]
aliases:
  - "Threat Model"
  - "tier4/threat-model"
generated: true
---

# Threat Model

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier4/threat-model.md:1`

## Falsifies if

> An incident occurs whose mechanism appears nowhere in this model, meaning the model enumerates the wrong hazards.

## Fields

| Field | Value |
|---|---|
| `evidence` | Every threat listed has a documented instance or a measured attack success rate. None is included on speculation; where a threat is theoretical for Alfred specifically, that is stated. |
| `path` | docs/tier4/threat-model.md |
| `tier_name` | Security and governance |

## Binds

- [[tier__tier4|Tier 4 — Security and governance]] **contains** → this
