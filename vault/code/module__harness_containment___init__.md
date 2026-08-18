---
kind: module
id: "module:harness.containment.__init__"
title: "Containment assertions: what the sandbox must prove before a run starts."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/__init__.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Containment assertions: what the sandbox must prove before a run starts."
  - "harness.containment.__init__"
generated: true
---

# Containment assertions: what the sandbox must prove before a run starts.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/__init__.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/__init__.py |
| `tree` | harness |

## Binds

- [[module__harness_containment|harness.containment]] **contains** → this

## Enforced by (code)

- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion 
