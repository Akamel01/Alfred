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
- **enforced_by** → [[module__migrations_harness_evidence_versions_0001_evidence_base|evidence: run records, verdicts, operator actions, artifacts, defect escapes.]] — # hash, over ACS-1, and ADR-0003 treats them as two different problems.
- **enforced_by** → [[module__src_provenance___init__|Result stamping and the one ACS-1 door (ADR-0003, ADR-0004).]] — """Result stamping and the one ACS-1 door (ADR-0003, ADR-0004).

Cannot be retrofitted: results computed before stamping
- **enforced_by** → [[module__src_provenance_encoding|The single door to ACS-1 (ADR-0003, ADR-0004).]] — """The single door to ACS-1 (ADR-0003, ADR-0004).

Product code hashes structures through this module and nowhere else. 
- **enforced_by** → [[module__src_provenance_stamp|Result stamping — metric version, code commit, assumption set, input hash, tolerance.]] — """Result stamping — metric version, code commit, assumption set, input hash, tolerance.

Cannot be retrofitted. A resul
- **enforced_by** → [[module__src_provenance_stamp|Result stamping — metric version, code commit, assumption set, input hash, tolerance.]] — """The input hash of a metric evaluation: ACS-1 over the declared inputs.

    Trajectory arrays are *artifacts* and are
- **enforced_by** → [[module__tests_test_one_encoder|ADR-0003: "A CI check asserts no code path hashes a structure through any encoder]] — """ADR-0003: "A CI check asserts no code path hashes a structure through any encoder
but this one."

Structural rather t
- **enforced_by** → [[module__tests_test_provenance|Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004).]] — """Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004)."""
