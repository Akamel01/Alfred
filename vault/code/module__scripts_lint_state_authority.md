---
kind: module
id: "module:scripts.lint_state_authority"
title: "SA001-SA003: the ownership router's mechanical half, checked."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_state_authority.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "SA001-SA003: the ownership router's mechanical half, checked."
  - "scripts.lint_state_authority"
generated: true
---

# SA001-SA003: the ownership router's mechanical half, checked.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_state_authority.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_state_authority.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_25|State authority lint checks its own vacuity]] **runs** → this
- [[gate-step__integrity_26|Ownership router homes exist and no gate cites runtime state]] **runs** → this

## Enforced by (code)

- [[adr__ADR-0047|The ownership router gains the factory's facts, and runtime state is never evidence]] **enforced_by** → this — """SA001-SA003: the ownership router's mechanical half, checked.

ADR-0047 extends `docs/tier1/data-architecture.md`'s o
- [[adr__ADR-0047|The ownership router gains the factory's facts, and runtime state is never evidence]] **enforced_by** → this — #: Runtime state, named once. ADR-0047 decision 3.
