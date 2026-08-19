---
kind: module
id: "module:harness.evidence.test_store"
title: "The append-only chain, asserted from both sides."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/evidence/test_store.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The append-only chain, asserted from both sides."
  - "harness.evidence.test_store"
generated: true
---

# The append-only chain, asserted from both sides.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/evidence/test_store.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/evidence/test_store.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]]
- **imports** → [[module__harness_db_cluster|Throwaway Postgres cluster: create, migrate, assert against, destroy.]]
- **imports** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]]
- [[module__harness_evidence|harness.evidence]] **contains** → this

## Enforced by (code)

- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """The append-only chain, asserted from both sides.

**How this suite would be shown vacuous** (D57). Every positive tes
