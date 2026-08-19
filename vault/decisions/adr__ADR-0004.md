---
kind: adr
id: "adr:ADR-0004"
title: "The ACS-1 float presentation grammar"
status: "accepted"
shape: "heading"
date: "2026-08-12"
source: "docs/tier1/adr-log.md:314"
extractor: "adrs"
aliases:
  - "ADR-0004"
  - "The ACS-1 float presentation grammar"
generated: true
---

# The ACS-1 float presentation grammar

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:314`

## Statement

**Date:** 2026-08-12 · **Status:** Accepted · **Amends:** ADR-0003 (float rule only)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]]
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **amended_by** → this

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — ACS-1 test vectors are the published specification (ADR-0004), so a
- **enforced_by** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]] — """ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

The canonical byte form of any structure who
- **enforced_by** → [[module__harness_acs_acs1_mjs|ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).]] — ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).
- **enforced_by** → [[module__harness_acs_acs1_mjs|ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).]] — ADR-0004 pins that.
- **enforced_by** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]] — # against (ADR-0004), and a specification generated from the implementation it
- **enforced_by** → [[module__harness_acs_mutate|Mutation control for the ACS-1 conformance suite.]] — """Mutation control for the ACS-1 conformance suite.

    python3 harness/acs/mutate.py            # every mutant, both 
- **enforced_by** → [[module__harness_acs_mutate|Mutation control for the ACS-1 conformance suite.]] — # Grouped by the rule each one breaks. The five at the top are the original ADR-0004
- **enforced_by** → [[module__harness_acs_mutate|Mutation control for the ACS-1 conformance suite.]] — # ---------------------------------------------------------------- ADR-0004 five
- **enforced_by** → [[module__harness_acs_mutate|Mutation control for the ACS-1 conformance suite.]] — "the exponent keeps the host's '+' sign, which ADR-0004 forbids"
- **enforced_by** → [[module__harness_acs_mutate|Mutation control for the ACS-1 conformance suite.]] — "the host's repr used directly, which is precisely what ADR-0004 exists to "
- **enforced_by** → [[module__src_provenance___init__|Result stamping and the one ACS-1 door (ADR-0003, ADR-0004, ADR-0006).]] — """Result stamping and the one ACS-1 door (ADR-0003, ADR-0004, ADR-0006).

Cannot be retrofitted: results computed befor
- **enforced_by** → [[module__src_provenance_encoding|The single door to ACS-1 (ADR-0003, ADR-0004).]] — """The single door to ACS-1 (ADR-0003, ADR-0004).

Product code hashes structures through this module and nowhere else. 
- **enforced_by** → [[module__src_provenance_stamp_v1|Result stamp, schema version 1 — the ten-key shape (ADR-0006).]] — """Result stamp, schema version 1 — the ten-key shape (ADR-0006).

**This file is frozen.** Once any stamp has been pers
- **enforced_by** → [[module__tests_test_provenance|Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004).]] — """Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004)."""
- **enforced_by** → [[module__tests_test_stamp_v1_vectors|The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).]] — """The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).

`harness/acs/gen_vectors.py` write
