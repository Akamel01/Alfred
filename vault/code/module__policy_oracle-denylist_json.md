---
kind: module
id: "module:policy.oracle-denylist.json"
title: "policy/oracle-denylist.json"
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "policy/oracle-denylist.json:1"
extractor: "code"
tags: [protected]
aliases:
  - "policy.oracle-denylist.json"
  - "policy/oracle-denylist.json"
generated: true
---

# policy/oracle-denylist.json

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `policy/oracle-denylist.json:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | policy/oracle-denylist.json |
| `tree` | policy |

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — "the vacuity ADR-0007 named. They are now read from importlib.metadata inside the pinned",
- [[decision__D50|The oracle is absent from the execution plane by assertion, not by convention]] **enforced_by** → this — "D50/D54. Versioned protected policy configuration; the version is a fingerprint field.",
- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — "D50/D54. Versioned protected policy configuration; the version is a fingerprint field.",
