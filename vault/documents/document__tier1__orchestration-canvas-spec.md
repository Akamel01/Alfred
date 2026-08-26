---
kind: document
id: "document:tier1/orchestration-canvas-spec"
title: "Orchestration Canvas Specification"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "review-cadence"
tier: "1"
written: "full"
review_after: "Phase 3"
source: "docs/tier1/orchestration-canvas-spec.md:1"
extractor: "documents"
tags: [human, review-cadence, tier1]
aliases:
  - "Orchestration Canvas Specification"
  - "tier1/orchestration-canvas-spec"
generated: true
---

# Orchestration Canvas Specification

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/orchestration-canvas-spec.md:1`

## Falsifies if

> The topology file contains a structure the lint does not reject, or the canvas emits a contract the palette does not declare.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier1/orchestration-canvas-spec.md |
| `tier_name` | Architecture |

**evidence**

> none — written as destination deliverable of wayfinder map #8; generated evidence is orchestration/topology.json + policy/node-palette.json + tools/orchestration/gen_canvas.py + scripts/lint_topology.py

## Binds

- [[tier__tier1|Tier 1 — Architecture]] **contains** → this
