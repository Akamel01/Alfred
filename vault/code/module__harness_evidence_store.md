---
kind: module
id: "module:harness.evidence.store"
title: "Append-only, hash-chained evidence writes."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/evidence/store.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Append-only, hash-chained evidence writes."
  - "harness.evidence.store"
generated: true
---

# Append-only, hash-chained evidence writes.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/evidence/store.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/evidence/store.py |
| `tree` | harness |

## Binds

- [[module__harness_evidence|harness.evidence]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """Append-only, hash-chained evidence writes.

**The evidence plane is never written by the agent.** That single rule dr
- [[decision__D51|Mission control exists, it is split, and every operator action is an evidence row]] **enforced_by** → this — # stable if a table is ever renamed, and so D51's "distinguished by ACS-1 domain
- [[decision__D51|Mission control exists, it is split, and every operator action is an evidence row]] **enforced_by** → this — """One operator action, written before its side effect is emitted (D51).

        `attended_ms` and `attended_ms_upper` 
