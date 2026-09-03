---
kind: module
id: "module:scripts.lint_model_routing"
title: "MR001-MR005: model routing policy conformance, checked before any spawn."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_model_routing.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "MR001-MR005: model routing policy conformance, checked before any spawn."
  - "scripts.lint_model_routing"
generated: true
---

# MR001-MR005: model routing policy conformance, checked before any spawn.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_model_routing.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_model_routing.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_23|Model routing lint checks its own vacuity]] **runs** → this
- [[gate-step__integrity_24|Model routing policy conforms to the bindings]] **runs** → this

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """MR001-MR005: model routing policy conformance, checked before any spawn.

**Why a static lint can enforce this at all
