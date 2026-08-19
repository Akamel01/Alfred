---
kind: module
id: "module:tests.test_stamp_v1_vectors"
title: "The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006)."
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/test_stamp_v1_vectors.py:1"
extractor: "code"
aliases:
  - "The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006)."
  - "tests.test_stamp_v1_vectors"
generated: true
---

# The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/test_stamp_v1_vectors.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/test_stamp_v1_vectors.py |
| `tree` | tests |

## Enforced by (code)

- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — """The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).

`harness/acs/gen_vectors.py` write
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).

`harness/acs/gen_vectors.py` write
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """ADR-0006 allocates `alfred.upstream_config`; the vector must use that exact tag."""
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """ADR-0006 freezes the key set. Spelled out rather than counted."""
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).

`harness/acs/gen_vectors.py` write
