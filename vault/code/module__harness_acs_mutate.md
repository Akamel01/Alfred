---
kind: module
id: "module:harness.acs.mutate"
title: "Mutation control for the ACS-1 conformance suite."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/acs/mutate.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Mutation control for the ACS-1 conformance suite."
  - "harness.acs.mutate"
generated: true
---

# Mutation control for the ACS-1 conformance suite.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/acs/mutate.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/acs/mutate.py |
| `tree` | harness |

## Binds

- [[module__harness_acs|harness.acs]] **contains** → this
- [[gate-step__mutation_04|ACS-1 mutation control]] **runs** → this

## Enforced by (code)

- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — """Mutation control for the ACS-1 conformance suite.

    python3 harness/acs/mutate.py            # every mutant, both 
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — # Grouped by the rule each one breaks. The five at the top are the original ADR-0004
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — # ---------------------------------------------------------------- ADR-0004 five
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — "the exponent keeps the host's '+' sign, which ADR-0004 forbids"
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — "the host's repr used directly, which is precisely what ADR-0004 exists to "
