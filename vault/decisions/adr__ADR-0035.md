---
kind: adr
id: "adr:ADR-0035"
title: "The protected set's single home names its fourth shape as a projection, not a second authority"
status: "accepted"
shape: "heading"
date: "2026-08-21"
source: "docs/tier1/adr-log.md:3790"
extractor: "adrs"
aliases:
  - "ADR-0035"
  - "The protected set's single home names its fourth shape as a projection, not a second autho"
generated: true
---

# The protected set's single home names its fourth shape as a projection, not a second authority

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:3790`

## Statement

**Date:** 2026-08-21 · **Status:** Accepted · **Supersedes:** nothing · **Amends:** the protected paths policy · **See also:** ADR-0022 (the first D28 waiver), ADR-0033 (the second), ADR-0031 (the protected set) · **D28 waiver:** yes

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0022|Phase 0's exit, narrowed along the ownership seam, with the residue dated]]
- **see_also** → [[adr__ADR-0031|The protected set is one file, and the gate protects its own policy]]
- **see_also** → [[adr__ADR-0033|The structure fence names every top-level directory, and the vault floors it]]
- [[adr__ADR-0052|The D28 waiver ordinal becomes derived, and ADR-0040's is corrected in place]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_test_dispatch_mount|Tests for dispatch mount exclusion (C12/C13).]] — """Tests for dispatch mount exclusion (C12/C13).

Prototype for ADR-0035: dispatch mount must be excluded from "no unexp
