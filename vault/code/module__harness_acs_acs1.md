---
kind: module
id: "module:harness.acs.acs1"
title: "ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004)."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/acs/acs1.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004)."
  - "harness.acs.acs1"
generated: true
---

# ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/acs/acs1.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/acs/acs1.py |
| `tree` | harness |

## Binds

- [[module__harness_acs|harness.acs]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """ACS-1 float grammar: normalized scientific, shortest round-tripping digits.

        sign? digit "." digit+ "e" "-"? 
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

The canonical byte form of any structure who
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — """ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

The canonical byte form of any structure who
