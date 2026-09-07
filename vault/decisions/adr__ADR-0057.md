---
kind: adr
id: "adr:ADR-0057"
title: "The C13/C7 archive-suffix split is defensible only under a wiring premise nothing in this repository can confirm, and the spec fix it implies is blocked on #78"
status: "accepted"
shape: "heading"
date: "2026-09-05"
source: "docs/tier1/adr-log.md:5435"
extractor: "adrs"
aliases:
  - "ADR-0057"
  - "The C13/C7 archive-suffix split is defensible only under a wiring premise nothing in this "
generated: true
---

# The C13/C7 archive-suffix split is defensible only under a wiring premise nothing in this repository can confirm, and the spec fix it implies is blocked on #78

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:5435`

## Statement

**Date:** 2026-09-05 · **Status:** Accepted · **Supersedes:** none · **Amends:** nothing · **See also:** commit `6f6d5de` (froze the split as declared contract), `harness/containment/test_archive_suffix_binding.py`, `docs/tier4/sandbox-specification.md` C13 and layer 3, ADR-0017 (an unread hole yields `not_executed`, never `passed`), ADR-0007 (the vacuity class), #7, #78 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0017|A containment assertion with an unread premise is a hole, and a hole never passes]]
