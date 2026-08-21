---
kind: module
id: "module:harness.acs.gen_vectors"
title: "Generate the ACS-1 test-vector suite (ADR-0003)."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/acs/gen_vectors.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Generate the ACS-1 test-vector suite (ADR-0003)."
  - "harness.acs.gen_vectors"
generated: true
---

# Generate the ACS-1 test-vector suite (ADR-0003).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/acs/gen_vectors.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/acs/gen_vectors.py |
| `tree` | harness |

## Binds

- [[module__harness_acs|harness.acs]] **contains** → this
- [[gate-step__integrity_15|ACS-1 vectors regenerate byte-identically]] **runs** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — # ---- the ADR-0001 tagged metric value, which is why any of this exists
- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — "the ADR-0001 tagged form, which is what actually gets hashed"
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """Generate the ACS-1 test-vector suite (ADR-0003).

The vectors are the specification. ACS-1 is deliberately not a publ
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — "reason ADR-0003 does not adopt it"
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — # against (ADR-0004), and a specification generated from the implementation it
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # ================================================ ADR-0006: the v1 result stamp
- [[adr__ADR-0016|`StampedResult` takes its schema version from the stamp it contains]] **enforced_by** → this — "stamp_schema_version is inside this preimage (ADR-0016)"
