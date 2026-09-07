---
kind: document
id: "document:tier2/structure-fence"
title: "Structure Fence"
status: "provisional"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "2"
written: "full"
review_after: "Phase 2"
source: "docs/tier2/structure-fence.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier2]
aliases:
  - "Structure Fence"
  - "tier2/structure-fence"
generated: true
---

# Structure Fence

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/structure-fence.md:1`

## Falsifies if

> A top-level directory exists in the tree and neither a fence line nor a committed layout-miss anomaly accounts for it; or a fence line names a directory that does not exist and no layout-ghost anomaly is committed for it; or a D28 waiver is spent against this fence at any point after ADR-0063, which would mean the reclassification did not remove the waiver source.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier2/structure-fence.md |
| `tier_name` | Build protocol |

**evidence**

> Reclassified from frozen by ADR-0063. Three D28 waivers landed against this fence's frozen status — ADR-0033, ADR-0040, and ADR-0050 once #78 reclassified it — tripping the three-waiver falsification clause at docs/tier0/operating-principles.md:6, which concludes that the principle is wrong rather than the situations. The fence itself is not wrong: tools/vaultgraph/extract/layout.py floors it at eighteen and surfaces layout-miss and layout-ghost anomalies that fire. What was wrong is freezing a list that tracks a directory tree, because the tree grows and a frozen list cannot follow it without a waiver each time.

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
