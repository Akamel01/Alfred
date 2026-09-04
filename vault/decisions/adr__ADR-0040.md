---
kind: adr
id: "adr:ADR-0040"
title: "The structure fence grows to eighteen"
status: "accepted"
shape: "heading"
date: "2026-08-29"
source: "docs/tier1/adr-log.md:3998"
extractor: "adrs"
aliases:
  - "ADR-0040"
  - "The structure fence grows to eighteen"
generated: true
---

# The structure fence grows to eighteen

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:3998`

## Statement

**Date:** 2026-08-29 · **Status:** Accepted · **Supersedes:** none · **Amends:** the structure fence of the coding standards (ADR-0033) · **See also:** ADR-0033 (the fence's first full enumeration), ADR-0039 (orchestration/ as protected prefix), ADR-0031 (protected set as single home) · **D28 waiver:** yes

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0033|The structure fence names every top-level directory, and the vault floors it]]
- **see_also** → [[adr__ADR-0031|The protected set is one file, and the gate protects its own policy]]
- **see_also** → [[adr__ADR-0033|The structure fence names every top-level directory, and the vault floors it]]
- **see_also** → [[adr__ADR-0039|Orchestration Canvas: Protected Topology Source & Palette Binding]]
- [[adr__ADR-0041|The S0–S9 build materialized as a numbered pipeline]] **see_also** → this
- [[adr__ADR-0043|Dead material archived and templates shelved]] **see_also** → this
- [[adr__ADR-0052|The D28 waiver ordinal becomes derived, and ADR-0040's is corrected in place]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — #: that record's claim. ADR-0052 is the instance — it quotes ADR-0040's line while explaining
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — """The record's effective ordinal claim: the **last** one across its claim sites.

    Last, not first, because the log 
