---
kind: adr
id: "adr:ADR-0061"
title: "An interruption is recorded as a termination, not a verdict: the record-shape half of #69"
status: "accepted"
shape: "heading"
date: "2026-09-05"
source: "docs/tier1/adr-log.md:6132"
extractor: "adrs"
aliases:
  - "ADR-0061"
  - "An interruption is recorded as a termination, not a verdict: the record-shape half of #69"
generated: true
---

# An interruption is recorded as a termination, not a verdict: the record-shape half of #69

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:6132`

## Statement

**Date:** 2026-09-05 · **Status:** Accepted · **Supersedes:** none · **Amends:** nothing on disk; it specifies changes to the Run Instrumentation and Mission Control specifications and `docs/tier1/data-architecture.md` for a later, separately reviewed commit · **Discharges:** the record-shape half of #69 · **See also:** ADR-0017 (a hole never passes), ADR-0055 (evidence chain link keys), `harness/verdicts/__init__.py` (the three-valued vocabulary), D51 (operator actions as evidence), #69 · **D28 waiver:** no — `data-architecture.md` is `status: frozen` but `enforcement: schema`, not `ci-gate`, so this falls outside the class disputed by #78, and no document is amended by this ADR itself

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0017|A containment assertion with an unread premise is a hole, and a hole never passes]]
- **see_also** → [[adr__ADR-0055|Evidence and heldout primary keys become UUIDv7, by a duplicated generator the harness sui]]
