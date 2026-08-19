---
kind: module
id: "module:src.provenance.verify"
title: "The two-stage stamp read, and what a verifier says about a version it does not know."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/provenance/verify.py:1"
extractor: "code"
aliases:
  - "The two-stage stamp read, and what a verifier says about a version it does not know."
  - "src.provenance.verify"
generated: true
---

# The two-stage stamp read, and what a verifier says about a version it does not know.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/provenance/verify.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/provenance/verify.py |
| `tree` | src |

## Binds

- [[module__src_provenance|src.provenance]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """The two-stage stamp read, and what a verifier says about a version it does not know.

ADR-0006's central property: **
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """Every schema version this build can verify, ascending.

    Public because the ADR-0006 enforcement checks iterate th
- [[decision__D16|Verdict fields are owned by deterministic nodes]] **enforced_by** → this — """The two-stage stamp read, and what a verifier says about a version it does not know.

ADR-0006's central property: **
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — """The two-stage stamp read, and what a verifier says about a version it does not know.

ADR-0006's central property: **
