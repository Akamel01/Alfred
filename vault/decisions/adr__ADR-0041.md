---
kind: adr
id: "adr:ADR-0041"
title: "The S0–S9 build materialized as a numbered pipeline"
status: "accepted"
shape: "heading"
date: "2026-08-29"
source: "docs/tier1/adr-log.md:4057"
extractor: "adrs"
aliases:
  - "ADR-0041"
  - "The S0–S9 build materialized as a numbered pipeline"
generated: true
---

# The S0–S9 build materialized as a numbered pipeline

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:4057`

## Statement

**Date:** 2026-08-29 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier2/execution-order.md` § Stages and § What must not be built yet (graph-editor line) · **See also:** ADR-0039 (topology canvas as protected source), ADR-0040 (fence v2, `stages/`), docs/tier2/stage-gate-definitions.md

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0039|Orchestration Canvas: Protected Topology Source & Palette Binding]]
- **see_also** → [[adr__ADR-0040|The structure fence grows to eighteen]]
- [[adr__ADR-0042|The vault gains verbs and effects]] **see_also** → this
- [[adr__ADR-0043|Dead material archived and templates shelved]] **see_also** → this
