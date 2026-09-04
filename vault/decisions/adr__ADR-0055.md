---
kind: adr
id: "adr:ADR-0055"
title: "Evidence and heldout primary keys become UUIDv7, by a duplicated generator the harness suite checks against drift"
status: "accepted"
shape: "heading"
date: "2026-09-04"
source: "docs/tier1/adr-log.md:5146"
extractor: "adrs"
aliases:
  - "ADR-0055"
  - "Evidence and heldout primary keys become UUIDv7, by a duplicated generator the harness sui"
generated: true
---

# Evidence and heldout primary keys become UUIDv7, by a duplicated generator the harness suite checks against drift

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:5146`

## Statement

**Date:** 2026-09-04 · **Status:** Accepted · **Supersedes:** none · **Amends:** nothing · **See also:** ADR-0053 decision 6 (named the excluded instance), `harness/fingerprint/factory.py`'s `d19_is_shared()` (the pattern this borrows), `harness/verdicts/__init__.py` and `tests/test_stamp_verify.py` (the precedent for where a cross-tree bridge test lives), #56, #80 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0053|The cross-stage invariants get the lint their register claims, and a checked map of what e]]
