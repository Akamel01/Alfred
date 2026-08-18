---
kind: module
id: "module:migrations.product.versions.0001_product_base"
title: "product: scenarios, trajectories, metric results, result stamps."
shape: "file"
present: "true"
protected: "false"
lint_gated: "false"
source: "migrations/product/versions/0001_product_base.py:1"
extractor: "code"
aliases:
  - "migrations.product.versions.0001_product_base"
  - "product: scenarios, trajectories, metric results, result stamps."
generated: true
---

# product: scenarios, trajectories, metric results, result stamps.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/product/versions/0001_product_base.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | migrations/product/versions/0001_product_base.py |
| `tree` | migrations |

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — # ADR-0001's tagged union, stored as its three arms rather than as one float.
- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — # ADR-0001 exists to prevent.
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — # The reason *name* is what crosses a boundary and what gets hashed (ADR-0002);
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # The ten keys, frozen by D55 / ADR-0006. `stamp_schema_version` is in the
- [[decision__D27|all in Phase 0]] **enforced_by** → this — """product: scenarios, trajectories, metric results, result stamps.

Revision ID: 0001_product_base
Revises:
Create Date
- [[decision__D55|SSP Layered Standard Traceability is declined — and its field set freezes at ten keys with]] **enforced_by** → this — """product: scenarios, trajectories, metric results, result stamps.

Revision ID: 0001_product_base
Revises:
Create Date
- [[decision__D55|SSP Layered Standard Traceability is declined — and its field set freezes at ten keys with]] **enforced_by** → this — # The ten keys, frozen by D55 / ADR-0006. `stamp_schema_version` is in the
