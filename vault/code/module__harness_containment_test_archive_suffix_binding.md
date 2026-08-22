---
kind: module
id: "module:harness.containment.test_archive_suffix_binding"
title: "Two ARCHIVE_SUFFIXES tuples, frozen verbatim, because their split is real and unexplained."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/test_archive_suffix_binding.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Two ARCHIVE_SUFFIXES tuples, frozen verbatim, because their split is real and unexplained."
  - "harness.containment.test_archive_suffix_binding"
generated: true
---

# Two ARCHIVE_SUFFIXES tuples, frozen verbatim, because their split is real and unexplained.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/test_archive_suffix_binding.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/containment/test_archive_suffix_binding.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_inside|C8, C9, C12, C13 — the assertions that need no executor vocabulary.]]
- **imports** → [[module__harness_containment_oracle_absence|C7 — the oracle is absent, asserted rather than assumed.]]
- [[module__harness_containment|harness.containment]] **contains** → this

## Enforced by (code)

- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Vacuity guard (D57): two empty frozensets agree perfectly and check nothing."""
