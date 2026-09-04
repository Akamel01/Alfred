---
kind: adr
id: "adr:ADR-0053"
title: "The cross-stage invariants get the lint their register claims, and a checked map of what enforces the rest"
status: "accepted"
shape: "heading"
date: "2026-09-03"
source: "docs/tier1/adr-log.md:4923"
extractor: "adrs"
aliases:
  - "ADR-0053"
  - "The cross-stage invariants get the lint their register claims, and a checked map of what e"
generated: true
---

# The cross-stage invariants get the lint their register claims, and a checked map of what enforces the rest

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:4923`

## Statement

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** nothing; `docs/tier1/cross-stage-invariants.md` is deliberately left untouched, and the Consequences say why · **See also:** ADR-0007 (the vacuity class), D57, `scripts/lint_migrations.py` (I2), `scripts/lint_verdict_boundary.py` (I17), #56 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
