---
kind: module
id: "module:harness.fingerprint.test_record"
title: "The run fingerprint record, and the control that the hash covers every field."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/fingerprint/test_record.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The run fingerprint record, and the control that the hash covers every field."
  - "harness.fingerprint.test_record"
generated: true
---

# The run fingerprint record, and the control that the hash covers every field.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/fingerprint/test_record.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/fingerprint/test_record.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- [[module__harness_fingerprint|harness.fingerprint]] **contains** → this

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """A record field with no column is a field the register cannot answer *what changed* on.

    D19's tiered requalificat
