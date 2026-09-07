---
kind: adr
id: "adr:ADR-0066"
title: "A D28 waiver declaration becomes correctable in the same append-only channel as its ordinal, and ADR-0050's is corrected"
status: "accepted"
shape: "heading"
date: "2026-09-07"
source: "docs/tier1/adr-log.md:6850"
extractor: "adrs"
aliases:
  - "A D28 waiver declaration becomes correctable in the same append-only channel as its ordina"
  - "ADR-0066"
generated: true
---

# A D28 waiver declaration becomes correctable in the same append-only channel as its ordinal, and ADR-0050's is corrected

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:6850`

## Statement

**Date:** 2026-09-07 · **Status:** Accepted · **Supersedes:** none · **Amends:** `scripts/lint_adr_numbers.py` (the declaration becomes an effective value, not a header read); corrects the declaration of ADR-0050 and the ordinals of ADR-0063 and ADR-0064, none of which can be edited in place · **See also:** ADR-0052 (which built this channel for the ordinal and stopped there), #78 (the ruling that reclassified ADR-0050), ADR-0063 and ADR-0064 (which recorded the discrepancy and could not fix it), `docs/tier0/operating-principles.md` (the falsification clause the count feeds) · **D28 waiver:** no — `scripts/` is code, and the ADR log is `frozen` with `enforcement: none` and append-only by construction, so neither is the frozen `ci-gate` shape #78 ruled on

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0050|Mission Control is hosted off-host, and the loopback bind is replaced rather than relaxed]]
- **amends** → [[adr__ADR-0063|The structure fence is split out and reclassified provisional, discharging the falsificati]]
- **amends** → [[adr__ADR-0064|The cross-stage invariants are reclassified provisional and stop re-listing what the lint ]]
- **see_also** → [[adr__ADR-0050|Mission Control is hosted off-host, and the loopback bind is replaced rather than relaxed]]
- **see_also** → [[adr__ADR-0052|The D28 waiver ordinal becomes derived, and ADR-0040's is corrected in place]]
- **see_also** → [[adr__ADR-0063|The structure fence is split out and reclassified provisional, discharging the falsificati]]
- **see_also** → [[adr__ADR-0064|The cross-stage invariants are reclassified provisional and stop re-listing what the lint ]]

## Enforced by (code)

- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — """The record's effective `D28 waiver` declaration: its header, unless a correction
    note overrides it. `None` for a 
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — # ADR-0066's channel. The ordinal has been correctable since ADR-0052; the
