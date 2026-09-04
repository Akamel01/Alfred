---
kind: module
id: "module:harness.acs.acs1"
title: "ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004)."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/acs/acs1.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004)."
  - "harness.acs.acs1"
generated: true
---

# ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/acs/acs1.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/acs/acs1.py |
| `tree` | harness |

## Binds

- [[module__harness_acs|harness.acs]] **contains** → this
- [[module__harness_containment_denylist|Load the oracle denylist and give it a digest the fingerprint can carry.]] **imports** → this
- [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]] **imports** → this
- [[module__harness_evidence_test_store|The append-only chain, asserted from both sides.]] **imports** → this
- [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]] **imports** → this
- [[module__harness_fingerprint_factory|The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.]] **imports** → this
- [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]] **imports** → this
- [[module__harness_fingerprint_test_attempt_start|Check A: a planted substitution must refuse to start, and its control must proceed.]] **imports** → this
- [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]] **imports** → this
- [[module__scripts_capture_run_fingerprint|Factory-owned script that collects all RunFingerprint fields from live sources,]] **imports** → this
- [[module__src_provenance_encoding|The single door to ACS-1 (ADR-0003, ADR-0004).]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """ACS-1 float grammar: normalized scientific, shortest round-tripping digits.

        sign? digit "." digit+ "e" "-"? 
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

The canonical byte form of any structure who
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — """ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

The canonical byte form of any structure who
