---
kind: module
id: "module:harness.ids"
title: "harness.ids"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/ids:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.ids"
generated: true
---

# harness.ids

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/ids:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_ids___init__|A UUIDv7 for the evidence plane, independent of `src/domain/ids.py` (I4, issue #80).]]
- [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]] **imports** → this
- [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]] **imports** → this
- [[module__tests_domain_test_ids|`domain.ids.uuid7` and `harness.ids.uuid7`, and the claim that they agree (issue #80).]] **imports** → this
