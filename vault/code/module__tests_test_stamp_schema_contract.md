---
kind: module
id: "module:tests.test_stamp_schema_contract"
title: "ADR-0006's enforcement clauses, as executable checks with their own controls."
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/test_stamp_schema_contract.py:1"
extractor: "code"
aliases:
  - "ADR-0006's enforcement clauses, as executable checks with their own controls."
  - "tests.test_stamp_schema_contract"
generated: true
---

# ADR-0006's enforcement clauses, as executable checks with their own controls.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/test_stamp_schema_contract.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/test_stamp_schema_contract.py |
| `tree` | tests |

## Enforced by (code)

- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """Names on the wire, never integers, never reused, never repurposed (ADR-0002)."""
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """ADR-0006's enforcement clauses, as executable checks with their own controls.

The ADR's Consequences list names four
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # The fields ADR-0006 marks Required on each arm. Restated here rather than read from the
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """Cross-version collision is complete from the content; a second place to bump is a
    second place to drift (ADR-0006
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """ADR-0006's enforcement clauses, as executable checks with their own controls.

The ADR's Consequences list names four
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """D57. Every check below iterates the registry and would pass on an empty one."""
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — # D57: a scan of zero files is not a pass.
