---
kind: module
id: "module:harness.containment.denylist"
title: "Load the oracle denylist and give it a digest the fingerprint can carry."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/denylist.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Load the oracle denylist and give it a digest the fingerprint can carry."
  - "harness.containment.denylist"
generated: true
---

# Load the oracle denylist and give it a digest the fingerprint can carry.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/denylist.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/denylist.py |
| `tree` | harness |

## Binds

- [[module__harness_containment|harness.containment]] **contains** → this

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """Load the oracle denylist and give it a digest the fingerprint can carry.

The denylist is versioned protected policy 
- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — """Load the oracle denylist and give it a digest the fingerprint can carry.

The denylist is versioned protected policy 
