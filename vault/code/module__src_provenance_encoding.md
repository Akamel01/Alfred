---
kind: module
id: "module:src.provenance.encoding"
title: "The single door to ACS-1 (ADR-0003, ADR-0004)."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/provenance/encoding.py:1"
extractor: "code"
aliases:
  - "The single door to ACS-1 (ADR-0003, ADR-0004)."
  - "src.provenance.encoding"
generated: true
---

# The single door to ACS-1 (ADR-0003, ADR-0004).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/provenance/encoding.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/provenance/encoding.py |
| `tree` | src |

## Binds

- [[module__src_provenance|src.provenance]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """The single door to ACS-1 (ADR-0003, ADR-0004).

Product code hashes structures through this module and nowhere else. 
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — """The single door to ACS-1 (ADR-0003, ADR-0004).

Product code hashes structures through this module and nowhere else. 
