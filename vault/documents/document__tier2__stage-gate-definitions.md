---
kind: document
id: "document:tier2/stage-gate-definitions"
title: "Stage Gate Definitions"
status: "provisional"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "2"
written: "full"
review_after: "Phase 1 exit"
source: "docs/tier2/stage-gate-definitions.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier2]
aliases:
  - "Stage Gate Definitions"
  - "tier2/stage-gate-definitions"
generated: true
---

# Stage Gate Definitions

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/stage-gate-definitions.md:1`

## Falsifies if

> A phase is exited with a gate red and no waiver ADR recorded; or a criterion is marked met with evidence that does not resolve; or this document names a criterion the register does not carry, in either direction.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier2/stage-gate-definitions.md |
| `tier_name` | Build protocol |

**evidence**

> ADR-0022, 2026-08-19. Phase 0's criteria are written out here because the narrowing decision forced an enumeration of them; before that they existed only as prose in an orchestrator-owned plan file and no check read them. Phase 1 and later remain unwritten and say so — content written before the evidence exists cannot be current. The register this document commits to is `harness/selftest/stage_gate_register.json` and the check is `scripts/lint_stage_gates.py`.

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
