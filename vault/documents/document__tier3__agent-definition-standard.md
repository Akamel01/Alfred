---
kind: document
id: "document:tier3/agent-definition-standard"
title: "Agent Definition Standard"
status: "provisional"
shape: "file"
owner: "executable"
enforcement: "schema"
tier: "3"
written: "full"
review_after: "Phase 2"
source: "docs/tier3/agent-definition-standard.md:1"
extractor: "documents"
tags: [executable, schema, tier3]
aliases:
  - "Agent Definition Standard"
  - "tier3/agent-definition-standard"
generated: true
---

# Agent Definition Standard

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier3/agent-definition-standard.md:1`

## Falsifies if

> An agent is dispatched whose definition names a job title rather than a capability; or a binding is edited without the fingerprint moving, meaning the version fields below are not actually the D19 group.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier3/agent-definition-standard.md |
| `tier_name` | Agent specifications |

**evidence**

> The decisions in docs/tier7/ticket-43-role-bindings-decision.md, the glossary's Capability definition, the frozen task specification standard's `capability` field, and the seven bindings now in policy/role-bindings.json checked by lint_topology.py TOP010-TOP013. No agent has been dispatched through a binding; the field set rests on the fingerprint's D19 group, not on an observed run.

## Binds

- [[tier__tier3|Tier 3 — Agent specifications]] **contains** → this
