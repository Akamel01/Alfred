---
kind: adr
id: "adr:ADR-0064"
title: "The cross-stage invariants are reclassified provisional and stop re-listing what the lint checks, applying ADR-0063's lesson before a third waiver rather than after"
status: "accepted"
shape: "heading"
date: "2026-09-06"
source: "docs/tier1/adr-log.md:6634"
extractor: "adrs"
aliases:
  - "ADR-0064"
  - "The cross-stage invariants are reclassified provisional and stop re-listing what the lint "
generated: true
---

# The cross-stage invariants are reclassified provisional and stop re-listing what the lint checks, applying ADR-0063's lesson before a third waiver rather than after

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:6634`

## Statement

**Date:** 2026-09-06 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier1/cross-stage-invariants.md` (header, the enforcement claim, and § *What the lint checks*), `docs/README.md` (register row), `scripts/gen_doc_stubs.py` (stub register) · **See also:** ADR-0063 (the precedent, and the contrast in decision 3), ADR-0062 (the falsification that produced the lesson), ADR-0053 (the lint the split describes), #78, #79 · **D28 waiver:** yes — the sixth by the log's derivation, seventh in fact

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0053|The cross-stage invariants get the lint their register claims, and a checked map of what e]]
- **see_also** → [[adr__ADR-0062|Amending a frozen ci-gate document is a D28 waiver; ADR-0050 is retroactively the third ag]]
- **see_also** → [[adr__ADR-0063|The structure fence is split out and reclassified provisional, discharging the falsificati]]

## Enforced by (code)

- **enforced_by** → [[module__scripts_gen_doc_stubs|Generate the Alfred documentation register as stubs (D32).]] — "ENFORCEMENT map as the authority on which holds which; provisional per ADR-0064 because that "
