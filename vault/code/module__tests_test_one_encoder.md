---
kind: module
id: "module:tests.test_one_encoder"
title: "ADR-0003: \"A CI check asserts no code path hashes a structure through any encoder"
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/test_one_encoder.py:1"
extractor: "code"
aliases:
  - "ADR-0003: \"A CI check asserts no code path hashes a structure through any encoder"
  - "tests.test_one_encoder"
generated: true
---

# ADR-0003: "A CI check asserts no code path hashes a structure through any encoder

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/test_one_encoder.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/test_one_encoder.py |
| `tree` | tests |

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """ADR-0003: "A CI check asserts no code path hashes a structure through any encoder
but this one."

Structural rather t
