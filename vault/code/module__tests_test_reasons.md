---
kind: module
id: "module:tests.test_reasons"
title: "The reason codebook invariants (ADR-0002)."
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/test_reasons.py:1"
extractor: "code"
aliases:
  - "The reason codebook invariants (ADR-0002)."
  - "tests.test_reasons"
generated: true
---

# The reason codebook invariants (ADR-0002).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/test_reasons.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/test_reasons.py |
| `tree` | tests |

## Enforced by (code)

- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """The reason codebook invariants (ADR-0002).

Each test here corresponds to a clause the ADR says CI asserts. Every one
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — # The point of ADR-0002: the failure lands at 80%, well before 254, so the
