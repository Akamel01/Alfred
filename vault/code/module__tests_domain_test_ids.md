---
kind: module
id: "module:tests.domain.test_ids"
title: "`domain.ids.uuid7` and `harness.ids.uuid7`, and the claim that they agree (issue #80)."
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/domain/test_ids.py:1"
extractor: "code"
aliases:
  - "`domain.ids.uuid7` and `harness.ids.uuid7`, and the claim that they agree (issue #80)."
  - "tests.domain.test_ids"
generated: true
---

# `domain.ids.uuid7` and `harness.ids.uuid7`, and the claim that they agree (issue #80).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/domain/test_ids.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/domain/test_ids.py |
| `tree` | tests |

## Binds

- **imports** → [[module__harness_ids|harness.ids]]

## Enforced by (code)

- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """`domain.ids.uuid7` and `harness.ids.uuid7`, and the claim that they agree (issue #80).

`harness/` is the protected i
