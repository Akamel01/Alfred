---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      The decisions in docs/tier7/ticket-43-role-bindings-decision.md, the glossary's Capability definition, the frozen task specification standard's `capability` field, and the eight bindings now in policy/role-bindings.json checked by lint_topology.py TOP010-TOP015. No agent has been dispatched through a binding; the field set rests on the fingerprint's D19 group, not on an observed run.
falsifies_if:  An agent is dispatched whose definition names a job title rather than a capability; or a binding is edited without the fingerprint moving, meaning the version fields below are not actually the D19 group; or a `requalification` status of `pass` is recorded while any D19 version field is `unset`; or a `paths_match` selector ships that matches no file in the tree, meaning the conditional roster never fires.
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
| `agents[]` | `{ agent, harness, applies_when? }`. The runtime agents this capability dispatches to. May be empty; see below. `applies_when` is optional and makes the entry conditional; see *A conditional roster member*. |
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

## A conditional roster member

A roster entry may carry an optional `applies_when` selector:

```json
{ "agent": "python-reviewer", "harness": "claude-code",
  "applies_when": { "paths_match": ["*.py"], "glob": "pathlib-match" } }
```

An entry **without** `applies_when` is unconditional — always dispatched. An entry **with**
it is conditional: dispatched only when the selector matches the paths the change touches —
the task record's `writable_paths` (`docs/tier2/task-specification-standard.md`), the path
list the harness mounts, fixed at dispatch and never chosen by the agent mid-run. The caller
never picks the reviewer: the selector is keyed off the task's paths, not off a
caller-supplied language tag. The selector lives on the roster entry, never on the binding
record: one binding may carry several members with different selectors, and a selector on
the record would apply to all of them at once. `lint_topology.py` TOP015 fails an
`applies_when` found on the binding record itself — a selector in the wrong place never
fires, which is the same vacuity one level up.

`glob` is **required** and names the dialect. There is no default — an unnamed dialect is
exactly the ambiguity the field exists to remove, and a selector whose meaning depends on
which glob implementation the reader happened to have is not a specification. The dialect
set is **closed**: `pathlib-match` is its only member (the lint's `GLOB_DIALECTS` set,
`scripts/lint_topology.py:58`), so a selector naming any other dialect fails TOP015. A
second dialect is not available yet.

### The `pathlib-match` dialect

`pathlib-match` is `pathlib.PurePath.match()` semantics: a pattern matches a path when the
pattern's trailing components match the path's trailing components, and `*` does not cross
`/`. Measured against this repository with
`PurePath(path).match(pattern)`:

| pattern | path | matches |
|---|---|---|
| `*.py` | `src/app/x.py` | yes |
| `**/*.py` | `src/app/x.py` | yes |
| `**/*.py` | `x.py` | no |
| `*.py` | `x.py` | yes |
| `**/*.py` | `a/b/c/x.py` | yes |
| `src/*.py` | `src/app/x.py` | no |
| `src/**/*.py` | `src/app/x.py` | yes |
| `src/**/*.py` | `src/a/b/x.py` | no |
| `migrations/**/*.sql` | `migrations/roles/001_roles.sql` | yes |
| `*.sql` | `migrations/roles/001_roles.sql` | yes |

**`**` is not a recursive wildcard.** It matches exactly one directory level and never
recurses: `src/**/*.py` matches `src/app/x.py` but not `src/a/b/x.py`. Because the pattern
is matched from the right, the components above the last one are unconstrained, so
`**/*.py` matches a `.py` file that has at least one directory above it — `a/b/c/x.py` yes,
a top-level `x.py` no. `*.py` is the any-depth pattern: it matches at every depth, the top
level included. `**/*.py` is therefore the *narrower* of the two, not the better "any depth"
one.

The dialect is **named** because the same pattern string means different things under
different glob implementations, and the difference is not academic here. Under shell-glob
semantics `*` does not cross `/`, so `*.py` would match **0** of this repository's 215
tracked `.py` files — every one of them nested, none at the top level — and the selector
would silently never fire. A selector that matches nothing is a finding, not a pass (the
D57 vacuity class). `lint_topology.py` TOP015 therefore fails any `paths_match` glob that
matches no file in the tree, under this dialect and no other.

### Selection is additive

A conditional member is **added to** the unconditional members of the roster, never
substituted for one. `code-reviewer` and `security-reviewer` stay unconditional; a
matching language reviewer joins them. Swapping a generalist out to make room for a
specialist narrows coverage without buying the independence the roster exists for.

### A member that was not selected is recorded, never silently skipped

A conditional member that is **not** selected must be recorded in the review record, so an
audit can see that the reviewer did not run and why. **That recording mechanism is owed by
a future dispatcher and does not exist today.** Nothing in this repository dispatches a
binding: the only readers of `policy/role-bindings.json` are `scripts/lint_topology.py`,
`scripts/lint_model_routing.py` and the vault extractor
(`tools/vaultgraph/extract/policy.py`), and `docs/tier2/review-protocol.md` is a stub. This
section specifies an obligation; it does not discharge it.

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

## Eight kinds are bound, not twenty-one

Only the kinds the execution lifecycle actually reaches carry bindings: **researcher,
examiner, architect, planner, code-writer, reviewer, validator, wayfinder**. The rest are
`unbound` or `never`.

`docs/tier3/agent-catalog.md` stays a stub. Its own text says a catalog records *"observed
capability boundaries, not an imagined org chart"*, and nothing has been observed.

## Three capabilities bind to no agent, on purpose

- **`examiner`** — no ECC agent performs requirements interrogation. ECC's 68 agents are
  language reviewers and build resolvers; `council` is a skill, not an agent.
- **`validator`** — no agent may hold validation authority. `verification-loop` and
  `eval-harness` are skills; `agent-evaluator` is classified *never authoritative*, because an
  agent rating its own output is a self-reported verdict from the executing session.
- **`wayfinder`** — no ECC agent charts long-horizon work through fog. It ran unbound until
  2026-09-03, when the `~/.claude` wayfinder skill carried `disable-model-invocation: true`
  and no agent could run it; the operator removed that flag, so the fact changed and the
  kind became `agent` with an empty roster. The capability runs Alfred-native, invoking the
  `wayfinder` skill directly.

All three state an `unbound_reason` rather than binding a near-miss.

## A binding edit is a requalification event

The version fields above **are** the Run Fingerprint's D19 group —
*"what tiered requalification reads to decide which component moved."* And per the glossary, an
autonomy grant is *"suspended by any fingerprint change."*

So editing a binding is not cheap, and should not be. It is the correct price for changing which
model reviews work, and the same reason `policy/` is protected. It is also what makes *"why did
this capability's merge rate move?"* answerable: without it, a silent binding edit is
indistinguishable from genuine capability drift, which is the one number the autonomy gates read.

## The requalification report

`policy/role-bindings.json` carries one file-level `requalification` object — `{ status, reason, ticket }`.
`status` is one of `pass`, `fail`, `indeterminate` — the fingerprint's three-valued vocabulary
(`harness/verdicts/__init__.py`). While any D19 version field is `"unset"` or absent the status may
not be `pass`; it reads `indeterminate`, and `indeterminate` must carry a `reason`. The key's
**absence is itself a violation**: a binding edit with no recorded status is indistinguishable from
a silent pass. Checked by `lint_topology.py` TOP014.

## Enforcement

`schema` — owned by `executable`. `scripts/lint_topology.py` checks TOP010–TOP015 against
`policy/node-palette.json` and `policy/role-bindings.json`, with a paired negative control for
each direction of each check.
