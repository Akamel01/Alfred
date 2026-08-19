---
kind: module
id: "module:scripts.lint_migrations"
title: "Additive-only lint over the evidence and held-out migration directories."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_migrations.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Additive-only lint over the evidence and held-out migration directories."
  - "scripts.lint_migrations"
generated: true
---

# Additive-only lint over the evidence and held-out migration directories.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_migrations.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_migrations.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_06|Migrations are additive-only]] **runs** → this
