---
kind: schema
id: "schema:harness/control/0001_control_base"
title: "0001_control_base"
shape: "migration-revision"
source: "migrations/harness/control/versions/0001_control_base.py:32"
extractor: "schema"
aliases:
  - "0001_control_base"
  - "harness/control/0001_control_base"
generated: true
---

# 0001_control_base

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/harness/control/versions/0001_control_base.py:32`

## Fields

| Field | Value |
|---|---|
| `down_revision` | none |
| `path` | migrations/harness/control/versions/0001_control_base.py |
| `revision` | 0001_control_base |
| `schema` | control |

## Binds

- [[schema__harness__control|harness/control]] **contains** → this
- [[schema__harness__control__0002_fingerprint_run_fields|0002_fingerprint_run_fields]] **revises** → this
