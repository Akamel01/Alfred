---
kind: policy
id: "policy:model-routing"
title: "Model Routing policy"
shape: "file"
source: "policy/model-routing.json:1"
extractor: "policy"
aliases:
  - "Model Routing policy"
  - "model-routing"
generated: true
---

# Model Routing policy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `policy/model-routing.json:1`

## Fields

| Field | Value |
|---|---|
| `count:forbidden` | 2 |
| `count:loud_default` | 2 |
| `count:notes` | 4 |
| `count:routes` | 8 |
| `count:trivial_class` | 3 |
| `path` | policy/model-routing.json |
| `unset_field_count` | 0 |
| `version` | 1 |

**authority**

> docs/tier7/ticket-46-model-routing-decision.md. Protected by policy/ in protected-paths.json. A change here moves model_version, a D19 fingerprint field, and the glossary suspends every autonomy grant on a fingerprint change.

## Enforced by (code)

- **references** → [[policy__role-bindings|Role Bindings policy]] — The routing key is capability_id, declared in policy/role-bindings.json. Not palette kind: the frozen task specification
- [[policy__role-bindings|Role Bindings policy]] **references** → this — capability_id IS the routing key. policy/model-routing.json maps it to a model. Ticket #43 D5 gave the binding a separat
