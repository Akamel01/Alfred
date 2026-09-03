---
kind: document
id: "document:tier3/handoff-contract-standard"
title: "Handoff Contract Standard"
status: "provisional"
shape: "file"
owner: "executable"
enforcement: "schema"
tier: "3"
written: "full"
review_after: "Phase 3"
source: "docs/tier3/handoff-contract-standard.md:1"
extractor: "documents"
tags: [executable, schema, tier3]
aliases:
  - "Handoff Contract Standard"
  - "tier3/handoff-contract-standard"
generated: true
---

# Handoff Contract Standard

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier3/handoff-contract-standard.md:1`

## Falsifies if

> A handoff carries prose the successor relies on without reading the underlying artifact.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier3/handoff-contract-standard.md |
| `tier_name` | Agent specifications |

**evidence**

> The seven phases fixed in docs/tier3/execution-lifecycle.md and the phase_end record added to docs/tier3/run-instrumentation-specification.md by ADR-0047, whose artifact_ref is a hash rather than a path (I3). Promoted ahead of its stated review_after because those two supplied the content it was waiting for; no handoff has yet been observed crossing a phase boundary.

## Binds

- [[tier__tier3|Tier 3 — Agent specifications]] **contains** → this
