---
kind: module
id: "module:harness.evidence"
title: "harness.evidence"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/evidence:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.evidence"
generated: true
---

# harness.evidence

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/evidence:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_evidence___init__|The evidence plane's writer.]]
- **contains** → [[module__harness_evidence_anchor|The chain head, recorded off-machine, and derived by the implementation that is not Python]]
- **contains** → [[module__harness_evidence_export|Dump a chain as raw columns, so something else can check it.]]
- **contains** → [[module__harness_evidence_restore_drill|D-synthetic: dump one cluster, restore into another, and check four ways.]]
- **contains** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]]
- **contains** → [[module__harness_evidence_test_restore_drill|The restore drill and the independent re-walk, each with the control that matters.]]
- **contains** → [[module__harness_evidence_test_store|The append-only chain, asserted from both sides.]]
- **contains** → [[module__harness_evidence_verify_chain_mjs|]]
