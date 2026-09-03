---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      The decisions in docs/tier7/ticket-43-role-bindings-decision.md, the glossary's Capability definition, the frozen task specification standard's `capability` field, and the seven bindings now in policy/role-bindings.json checked by lint_topology.py TOP010-TOP013. No agent has been dispatched through a binding; the field set rests on the fingerprint's D19 group, not on an observed run.
falsifies_if:  An agent is dispatched whose definition names a job title rather than a capability; or a binding is edited without the fingerprint moving, meaning the version fields below are not actually the D19 group.
review_after:  Phase 2
---

# Agent Definition Standard

The schema every agent definition must satisfy. **Roles are not valid agent definitions.**

A palette kind is a role — the glossary is explicit that a capability is *"the unit an agent
is scoped to. Never a job title."* A **binding** is what turns a role into a definition, by
supplying the rest of the capability tuple:

> **Capability** — `(input contract, output contract, tools, permissions, criteria, escalation)`

The executable form is `policy/role-bindings.json`. This document is its schema.

## Field set

| Field | Meaning |
|---|---|
| `kind` | Palette kind id. The join to `policy/node-palette.json`. |
| `capability_id` | The identity of this capability. **This is also the routing key** — `policy/model-routing.json` maps it to a model. |
| `phases` | Which lifecycle phases dispatch to it. See `docs/tier3/execution-lifecycle.md`. |
| `agents[]` | `{ agent, harness }`. The runtime agents this capability dispatches to. May be empty; see below. |
| `unbound_reason` | Required when `agents[]` is empty. An empty roster is a real answer; an unexplained one is an omission wearing the same shape. |
| `tools[]` | Hashed into `tool_version`. |
| `permissions{}` | What the capability may do. |
| `context_budget` | Turn and token caps. |
| `prompt_version`, `tool_version`, `context_strategy_version` | The D19 group. See *A binding edit is a requalification event*. |

**There is deliberately no `model` field.** Ticket #43's D5 gave the binding a `model`
reference into the routing policy; ticket #46's D4 then established that the routing key **is**
`capability_id`. A separate `model` field would be a second name for one join, and a second
name for one fact is the shape `docs/tier7/ticket-45-state-authority-decision.md` forbids.
A model-policy change therefore touches no binding record.

## `bindable`

Every palette kind carries one of three values:

| Value | Meaning |
|---|---|
| `agent` | Dispatched to a runtime agent; carries a full binding record. |
| `unbound` | A legitimate kind that no lifecycle phase dispatches today. |
| `never` | May never be delegated to an agent. |

**`bindable` is stated explicitly and also derived from the palette's `category`, and the two
are compared.** This is not redundancy. An explicit `never` is a statement a reviewer sees in
the diff; deriving it from `category` is an inference that breaks silently the day someone adds
a non-agent kind outside the operator category. `lint_topology.py` TOP011 fails on disagreement,
in both directions. Two independent expressions of one fact, checked against each other, is not
two homes for it.

## Seven kinds are bound, not twenty-one

Only the kinds the execution lifecycle actually dispatches carry bindings: **researcher,
examiner, architect, planner, code-writer, reviewer, validator**. The rest are `unbound` or
`never`.

`docs/tier3/agent-catalog.md` stays a stub. Its own text says a catalog records *"observed
capability boundaries, not an imagined org chart"*, and nothing has been observed.

## Two capabilities bind to no agent, on purpose

- **`examiner`** — no ECC agent performs requirements interrogation. ECC's 68 agents are
  language reviewers and build resolvers; `council` is a skill, not an agent.
- **`validator`** — no agent may hold validation authority. `verification-loop` and
  `eval-harness` are skills; `agent-evaluator` is classified *never authoritative*, because an
  agent rating its own output is a self-reported verdict from the executing session.

Both state an `unbound_reason` rather than binding a near-miss.

## A binding edit is a requalification event

The version fields above **are** the Run Fingerprint's D19 group —
*"what tiered requalification reads to decide which component moved."* And per the glossary, an
autonomy grant is *"suspended by any fingerprint change."*

So editing a binding is not cheap, and should not be. It is the correct price for changing which
model reviews work, and the same reason `policy/` is protected. It is also what makes *"why did
this capability's merge rate move?"* answerable: without it, a silent binding edit is
indistinguishable from genuine capability drift, which is the one number the autonomy gates read.

## Enforcement

`schema` — owned by `executable`. `scripts/lint_topology.py` checks TOP010–TOP013 against
`policy/node-palette.json` and `policy/role-bindings.json`, with a paired negative control for
each direction of each check.
