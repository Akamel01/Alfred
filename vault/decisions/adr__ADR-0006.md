---
kind: adr
id: "adr:ADR-0006"
title: "The result stamp field set, its own version, and upstream toolchain provenance"
status: "accepted"
shape: "heading"
date: "2026-08-16"
source: "docs/tier1/adr-log.md:459"
extractor: "adrs"
aliases:
  - "ADR-0006"
  - "The result stamp field set, its own version, and upstream toolchain provenance"
generated: true
---

# The result stamp field set, its own version, and upstream toolchain provenance

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:459`

## Statement

**Date:** 2026-08-16 · **Status:** Accepted · **Supersedes:** none · **Forward pointers:** ADR-0001 (the tagged-union pattern gains a third use), ADR-0003 (the record type `alfred.result_stamp` gains a versioned field set; a second record type `alfred.upstream_config` is allocated)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0001|Representation of undefined and infinite metric values]]
- **see_also** → [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]]
- [[adr__ADR-0016|`StampedResult` takes its schema version from the stamp it contains]] **amends** → this
- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **see_also** → this
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]] — # ================================================ ADR-0006: the v1 result stamp
- **enforced_by** → [[module__harness_verdicts_test_verdicts|The verdict vocabulary's bindings: every other spelling answers to this module.]] — # The five rows ADR-0006 specifies, restated here rather than read from the module under
- **enforced_by** → [[module__migrations_product_versions_0001_product_base|product: scenarios, trajectories, metric results, result stamps.]] — # The ten keys, frozen by D55 / ADR-0006. `stamp_schema_version` is in the
- **enforced_by** → [[module__src_provenance___init__|Result stamping and the one ACS-1 door (ADR-0003, ADR-0004, ADR-0006).]] — """Result stamping and the one ACS-1 door (ADR-0003, ADR-0004, ADR-0006).

Cannot be retrofitted: results computed befor
- **enforced_by** → [[module__src_provenance_stamp|Result stamping — the shape in which a number leaves the system.]] — """Result stamping — the shape in which a number leaves the system.

Cannot be retrofitted. A result computed before the
- **enforced_by** → [[module__src_provenance_stamp|Result stamping — the shape in which a number leaves the system.]] — # old documents against a new model, which is the thing ADR-0006 forbids outright.
- **enforced_by** → [[module__src_provenance_stamp|Result stamping — the shape in which a number leaves the system.]] — """A metric value that can be re-derived and, if necessary, recalled.

    The only shape in which a number leaves the s
- **enforced_by** → [[module__src_provenance_stamp_v1|Result stamp, schema version 1 — the ten-key shape (ADR-0006).]] — """Result stamp, schema version 1 — the ten-key shape (ADR-0006).

**This file is frozen.** Once any stamp has been pers
- **enforced_by** → [[module__src_provenance_stamp_v1|Result stamp, schema version 1 — the ten-key shape (ADR-0006).]] — """False iff `upstream` is the `unknown` arm.

        The instrument ADR-0006 asks for when it says the `unknown` state
- **enforced_by** → [[module__src_provenance_upstream|`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).]] — """`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).

The stamp names *Alfred's* `metr
- **enforced_by** → [[module__src_provenance_upstream|`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).]] — # The domain-separation tag allocated by ADR-0006 for the canonicalized upstream
- **enforced_by** → [[module__src_provenance_upstream|`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).]] — """There *was* an upstream toolchain and Alfred could not determine it.

    A defect-grade state: a stamp carrying this
- **enforced_by** → [[module__src_provenance_verify|The two-stage stamp read, and what a verifier says about a version it does not know.]] — """The two-stage stamp read, and what a verifier says about a version it does not know.

ADR-0006's central property: **
- **enforced_by** → [[module__src_provenance_verify|The two-stage stamp read, and what a verifier says about a version it does not know.]] — """Every schema version this build can verify, ascending.

    Public because the ADR-0006 enforcement checks iterate th
- **enforced_by** → [[module__tests_test_provenance|Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004).]] — # Required, with no default and no null arm (ADR-0006). The fixture uses the
- **enforced_by** → [[module__tests_test_provenance|Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004).]] — # The two ADR-0006 additions. `stamp_schema_version` is pinned to 1 by the model,
- **enforced_by** → [[module__tests_test_stamp_schema_contract|ADR-0006's enforcement clauses, as executable checks with their own controls.]] — """ADR-0006's enforcement clauses, as executable checks with their own controls.

The ADR's Consequences list names four
- **enforced_by** → [[module__tests_test_stamp_schema_contract|ADR-0006's enforcement clauses, as executable checks with their own controls.]] — # The fields ADR-0006 marks Required on each arm. Restated here rather than read from the
- **enforced_by** → [[module__tests_test_stamp_schema_contract|ADR-0006's enforcement clauses, as executable checks with their own controls.]] — """Cross-version collision is complete from the content; a second place to bump is a
    second place to drift (ADR-0006
- **enforced_by** → [[module__tests_test_stamp_v1_vectors|The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).]] — """The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).

`harness/acs/gen_vectors.py` write
- **enforced_by** → [[module__tests_test_stamp_v1_vectors|The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).]] — """ADR-0006 allocates `alfred.upstream_config`; the vector must use that exact tag."""
- **enforced_by** → [[module__tests_test_stamp_v1_vectors|The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).]] — """ADR-0006 freezes the key set. Spelled out rather than counted."""
- **enforced_by** → [[module__tests_test_stamp_verify|The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).]] — """The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).

Every row of the ADR's verdic
- **enforced_by** → [[module__tests_test_stamp_verify|The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).]] — """Required by ADR-0006: without it the operator cannot act on the finding."""
