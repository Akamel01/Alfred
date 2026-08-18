---
kind: module
id: "module:tests.properties.test_metric_properties"
title: "Property tests over the representation types."
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/properties/test_metric_properties.py:1"
extractor: "code"
aliases:
  - "Property tests over the representation types."
  - "tests.properties.test_metric_properties"
generated: true
---

# Property tests over the representation types.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/properties/test_metric_properties.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/properties/test_metric_properties.py |
| `tree` | tests |

## Enforced by (code)

- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """The invariant ADR-0002 exists for: no integer decodes to DEFINED unless it is 0."""
