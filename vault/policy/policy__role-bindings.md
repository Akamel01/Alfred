---
kind: policy
id: "policy:role-bindings"
title: "Role Bindings policy"
shape: "file"
source: "policy/role-bindings.json:1"
extractor: "policy"
aliases:
  - "Role Bindings policy"
  - "role-bindings"
generated: true
---

# Role Bindings policy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `policy/role-bindings.json:1`

## Fields

| Field | Value |
|---|---|
| `count:bindable_values` | 3 |
| `count:bindings` | 8 |
| `count:kinds` | 21 |
| `count:notes` | 5 |
| `path` | policy/role-bindings.json |
| `unset_field_count` | 24 |
| `version` | 1 |

**authority**

> docs/tier3/agent-definition-standard.md (schema) and docs/tier7/ticket-43-role-bindings-decision.md (the decisions). Protected by policy/ in protected-paths.json; a change here is a requalification event.

## Enforced by (code)

- **references** → [[policy__model-routing|Model Routing policy]] — capability_id IS the routing key. policy/model-routing.json maps it to a model. Ticket #43 D5 gave the binding a separat
- [[policy__model-routing|Model Routing policy]] **references** → this — The routing key is capability_id, declared in policy/role-bindings.json. Not palette kind: the frozen task specification
