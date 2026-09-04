---
kind: adr
id: "adr:ADR-0052"
title: "The D28 waiver ordinal becomes derived, and ADR-0040's is corrected in place"
status: "accepted"
shape: "heading"
date: "2026-09-03"
source: "docs/tier1/adr-log.md:4816"
extractor: "adrs"
aliases:
  - "ADR-0052"
  - "The D28 waiver ordinal becomes derived, and ADR-0040's is corrected in place"
generated: true
---

# The D28 waiver ordinal becomes derived, and ADR-0040's is corrected in place

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:4816`

## Statement

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** nothing; this record repairs a drift and closes the class · **See also:** ADR-0022 (the first D28 waiver), ADR-0033 (the second), ADR-0035 (the third), ADR-0040 (the fourth, which claimed to be the third), `docs/tier0/operating-principles.md` (the falsification clause the count feeds), #55 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0022|Phase 0's exit, narrowed along the ownership seam, with the residue dated]]
- **see_also** → [[adr__ADR-0033|The structure fence names every top-level directory, and the vault floors it]]
- **see_also** → [[adr__ADR-0035|The protected set's single home names its fourth shape as a projection, not a second autho]]
- **see_also** → [[adr__ADR-0040|The structure fence grows to eighteen]]

## Enforced by (code)

- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — #: that record's claim. ADR-0052 is the instance — it quotes ADR-0040's line while explaining
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — #     outside a blockquote is not making that claim. ADR-0052 is the live instance,
