---
kind: module
id: "module:src.provenance.stamp_types"
title: "Shared stamp vocabulary: record types, tolerance, assumption set, the input hash."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/provenance/stamp_types.py:1"
extractor: "code"
aliases:
  - "Shared stamp vocabulary: record types, tolerance, assumption set, the input hash."
  - "src.provenance.stamp_types"
generated: true
---

# Shared stamp vocabulary: record types, tolerance, assumption set, the input hash.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/provenance/stamp_types.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/provenance/stamp_types.py |
| `tree` | src |

## Binds

- [[module__src_provenance|src.provenance]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """Shared stamp vocabulary: record types, tolerance, assumption set, the input hash.

These are **not** versioned, and n
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """The input hash of a metric evaluation: ACS-1 over the declared inputs.

    The preimage today is the full structured
