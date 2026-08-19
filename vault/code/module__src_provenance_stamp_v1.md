---
kind: module
id: "module:src.provenance.stamp_v1"
title: "Result stamp, schema version 1 — the ten-key shape (ADR-0006)."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/provenance/stamp_v1.py:1"
extractor: "code"
aliases:
  - "Result stamp, schema version 1 — the ten-key shape (ADR-0006)."
  - "src.provenance.stamp_v1"
generated: true
---

# Result stamp, schema version 1 — the ten-key shape (ADR-0006).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/provenance/stamp_v1.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/provenance/stamp_v1.py |
| `tree` | src |

## Binds

- [[module__src_provenance|src.provenance]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — # The reason travels as its **name**, never its ordinal (ADR-0002).
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — """Result stamp, schema version 1 — the ten-key shape (ADR-0006).

**This file is frozen.** Once any stamp has been pers
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """Result stamp, schema version 1 — the ten-key shape (ADR-0006).

**This file is frozen.** Once any stamp has been pers
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """False iff `upstream` is the `unknown` arm.

        The instrument ADR-0006 asks for when it says the `unknown` state
