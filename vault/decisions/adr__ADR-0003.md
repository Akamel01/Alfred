---
kind: adr
id: "adr:ADR-0003"
title: "Canonical serialization for hashed structures (ACS-1)"
status: "accepted"
shape: "heading"
date: "2026-08-12"
source: "docs/tier1/adr-log.md:219"
extractor: "adrs"
aliases:
  - "ADR-0003"
  - "Canonical serialization for hashed structures (ACS-1)"
generated: true
---

# Canonical serialization for hashed structures (ACS-1)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:219`

## Statement

**Date:** 2026-08-12 · **Status:** Accepted · **Supersedes:** none · **Amended by:** ADR-0004 (float grammar) · **See also:** ADR-0006 (the `alfred.result_stamp` field set becomes versioned; record type `alfred.upstream_config` allocated; SSP-LS-Traceability evaluated against §"the split that decides the shape" and declined)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amended_by** → [[adr__ADR-0004|The ACS-1 float presentation grammar]]
- **see_also** → [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]]
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **amends** → this
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **see_also** → this
- [[adr__ADR-0016|`StampedResult` takes its schema version from the stamp it contains]] **see_also** → this
- [[adr__ADR-0047|The ownership router gains the factory's facts, and runtime state is never evidence]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — digests without running Alfred's code (ADR-0003). It runs on stock Node with
- **enforced_by** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]] — """ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

The canonical byte form of any structure who
- **enforced_by** → [[module__harness_acs_acs1_mjs|ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).]] — ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).
- **enforced_by** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]] — """Generate the ACS-1 test-vector suite (ADR-0003).

The vectors are the specification. ACS-1 is deliberately not a publ
- **enforced_by** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]] — "reason ADR-0003 does not adopt it"
- **enforced_by** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]] — """Append-only, hash-chained evidence writes.

**The evidence plane is never written by the agent.** That single rule dr
- **enforced_by** → [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]] — #: ACS-1 takes the record type as its domain separator (ADR-0003): a bundle and a
- **enforced_by** → [[module__harness_fingerprint_factory|The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.]] — #: record type as its domain separator (ADR-0003), so a factory record and a lane record
- **enforced_by** → [[module__harness_fingerprint_test_attempt_start|Check A: a planted substitution must refuse to start, and its control must proceed.]] — """ACS-1 takes the record type as its domain separator (ADR-0003)."""
- **enforced_by** → [[module__harness_fingerprint_test_factory|The factory fingerprint, and the two claims about it that a docstring cannot keep true.]] — # ACS-1 takes the record type as its domain separator (ADR-0003). Two record types
- **enforced_by** → [[module__migrations_harness_evidence_versions_0001_evidence_base|evidence: run records, verdicts, operator actions, artifacts, defect escapes.]] — # hash, over ACS-1, and ADR-0003 treats them as two different problems.
- **enforced_by** → [[module__src_provenance___init__|Result stamping and the one ACS-1 door (ADR-0003, ADR-0004, ADR-0006).]] — """Result stamping and the one ACS-1 door (ADR-0003, ADR-0004, ADR-0006).

Cannot be retrofitted: results computed befor
- **enforced_by** → [[module__src_provenance_encoding|The single door to ACS-1 (ADR-0003, ADR-0004).]] — """The single door to ACS-1 (ADR-0003, ADR-0004).

Product code hashes structures through this module and nowhere else. 
- **enforced_by** → [[module__src_provenance_stamp_types|Shared stamp vocabulary: record types, tolerance, assumption set, the input hash.]] — """Shared stamp vocabulary: record types, tolerance, assumption set, the input hash.

These are **not** versioned, and n
- **enforced_by** → [[module__src_provenance_stamp_types|Shared stamp vocabulary: record types, tolerance, assumption set, the input hash.]] — """The input hash of a metric evaluation: ACS-1 over the declared inputs.

    The preimage today is the full structured
- **enforced_by** → [[module__tests_test_one_encoder|ADR-0003: "A CI check asserts no code path hashes a structure through any encoder]] — """ADR-0003: "A CI check asserts no code path hashes a structure through any encoder
but this one."

Structural rather t
- **enforced_by** → [[module__tests_test_provenance|Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004).]] — """Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004)."""
