---
kind: module
id: "module:harness.fingerprint.__init__"
title: "The run fingerprint record — the declared configuration a run is measured on."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/fingerprint/__init__.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The run fingerprint record — the declared configuration a run is measured on."
  - "harness.fingerprint.__init__"
generated: true
---

# The run fingerprint record — the declared configuration a run is measured on.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/fingerprint/__init__.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/fingerprint/__init__.py |
| `tree` | harness |

## Binds

- [[module__harness_fingerprint|harness.fingerprint]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]] **enforced_by** → this — """The run fingerprint record — the declared configuration a run is measured on.

Inspector machinery (D20). `record.py`
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **enforced_by** → this — """The run fingerprint record — the declared configuration a run is measured on.

Inspector machinery (D20). `record.py`
- [[adr__ADR-0020|The run fingerprint record, and the two assertions that were waiting on it]] **enforced_by** → this — """The run fingerprint record — the declared configuration a run is measured on.

Inspector machinery (D20). `record.py`
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """The run fingerprint record — the declared configuration a run is measured on.

Inspector machinery (D20). `record.py`
