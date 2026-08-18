---
kind: module
id: "module:harness.acs.acs1.mjs"
title: "ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004)."
shape: "javascript"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/acs/acs1.mjs:1"
extractor: "code"
tags: [protected]
aliases:
  - "ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004)."
  - "harness.acs.acs1.mjs"
generated: true
---

# ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/acs/acs1.mjs:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/acs/acs1.mjs |
| `tree` | harness |

## Binds

- [[module__harness_acs|harness.acs]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — ADR-0004 pins that.
