---
kind: module
id: "module:src.provenance.stamp"
title: "Result stamping — metric version, code commit, assumption set, input hash, tolerance."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/provenance/stamp.py:1"
extractor: "code"
aliases:
  - "Result stamping — metric version, code commit, assumption set, input hash, tolerance."
  - "src.provenance.stamp"
generated: true
---

# Result stamping — metric version, code commit, assumption set, input hash, tolerance.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/provenance/stamp.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/provenance/stamp.py |
| `tree` | src |

## Binds

- [[module__src_provenance|src.provenance]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — # `value` uses the ADR-0001 tagged form because ACS-1 refuses a raw
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """Result stamping — metric version, code commit, assumption set, input hash, tolerance.

Cannot be retrofitted. A resul
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """The input hash of a metric evaluation: ACS-1 over the declared inputs.

    Trajectory arrays are *artifacts* and are
