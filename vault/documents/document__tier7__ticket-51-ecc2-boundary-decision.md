---
kind: document
id: "document:tier7/ticket-51-ecc2-boundary-decision"
title: "Ticket #51 — the ECC2 reuse boundary"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "Phase 2"
source: "docs/tier7/ticket-51-ecc2-boundary-decision.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "Ticket #51 — the ECC2 reuse boundary"
  - "tier7/ticket-51-ecc2-boundary-decision"
generated: true
---

# Ticket #51 — the ECC2 reuse boundary

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ticket-51-ecc2-boundary-decision.md:1`

## Falsifies if

> An ECC2 pattern refused here is later adopted because the refusal reasoning was wrong; or Alfred is found importing, vendoring or executing ECC2 code.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ticket-51-ecc2-boundary-decision.md |
| `tier_name` | Meta |

**evidence**

> A read of ECC2 at ~/.config/opencode/ecc-source/ecc2 — 17 Rust files, ~54,100 lines, self-described alpha — including harness_eval.rs (579 lines), observability/mod.rs's compute_risk, and config's RISK_THRESHOLDS. Comparison is against Alfred's CriterionRunner, ACS-1 evidence chain, held-out isolation by SQL grant, and the Wilson-interval reading in K3.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
