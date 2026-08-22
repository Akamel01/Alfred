---
kind: module
id: "module:tests.test_stamp_verify"
title: "The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006)."
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/test_stamp_verify.py:1"
extractor: "code"
aliases:
  - "The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006)."
  - "tests.test_stamp_verify"
generated: true
---

# The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/test_stamp_verify.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/test_stamp_verify.py |
| `tree` | tests |

## Binds

- **imports** → [[module__harness_verdicts|harness.verdicts]]

## Enforced by (code)

- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).

Every row of the ADR's verdic
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """Required by ADR-0006: without it the operator cannot act on the finding."""
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """D57. Both directions above are set comparisons and would agree on two empty sets."""
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """D57. The parametrized check above would report nothing on an empty table."""
