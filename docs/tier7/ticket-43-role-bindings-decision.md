---
status:        provisional
owner:         human
enforcement:   none
evidence:      A grilling session on 2026-09-02 against policy/node-palette.json (21 kinds), the three Tier 3 agent stubs, harness/fingerprint/record.py's D19 group, scripts/lint_topology.py, and the 68 ECC agent definitions installed to ~/.claude/agents on the same day. No palette kind has yet dispatched work; no binding has been exercised.
falsifies_if:  A palette kind of category `operator` acquires a runtime binding; or a binding record's model is resolved from anywhere other than the routing policy; or a binding is edited without a requalification following.
review_after:  the first task dispatched through a binding
---

# Ticket #43 — role bindings: decision record

Resolves [Role bindings — palette kind to runtime](https://github.com/Akamel01/Alfred/issues/43),
a child of [wayfinder:map — Alfred × ECC: one factory](https://github.com/Akamel01/Alfred/issues/41).

## Two facts that made the ticket smaller than it looked

**The territory was already claimed.** `docs/tier3/agent-definition-standard.md` is a
32-line stub whose Purpose is verbatim this ticket — *"the schema every agent definition
must satisfy: input contract, output contract, tools, permissions, criteria, escalation"* —
and which carries one already-decided line: **"Roles are not valid agent definitions."** The
palette holds roles. A binding is exactly what turns a role into a definition.
`docs/tier3/agent-catalog.md` owns the instances.

**The fingerprint already had a slot for it.** `harness/fingerprint/record.py`'s **D19**
group — *"what tiered requalification reads to decide which component moved"* — is
`capability_id`, `model_version`, `prompt_version`, `tool_version`,
`context_strategy_version`. Those are not fields a binding *affects*. They **are** the
binding.

The ticket body proposed `policy/role-bindings.json` **or** `orchestration/role-bindings.json`
as though the home were open. It largely was not.

## The seven decisions

### D1 — Graduate one stub, not two

`docs/tier3/agent-definition-standard.md` graduates now and owns the **schema**.
`policy/role-bindings.json` (protected) is the **executable form**.
`docs/tier3/agent-catalog.md` stays a stub.

The schema's evidence exists today: 21 palette kinds, 68 installed ECC agent definitions
with their real frontmatter shape (`name` / `description` / `tools` / `model`), and Alfred's
own permission and fingerprint constraints. That is enough to say what fields a definition
must carry.

The catalog's evidence does not exist. Its own text forbids writing it from *"an imagined
org chart,"* and nothing has been observed because no palette kind has ever dispatched work.

`policy/` is the right home for the executable form for one reason: **an agent may never
edit which model reviews its own work.**

### D2 — `bindable: agent | unbound | never`, cross-checked against the palette

Eight `operator` kinds — `criterion-runner`, `evidence-store`, `worker-port`,
`operator-gate`, `fingerprint-capture`, `mutation-controller`, `restore-drill`,
`harness-runner` — must **never** be delegated to an agent. Six more (`wayfinder`,
`product-manager`, `drafter`, `domain-expert`, `tester`, `verifier`) have no implementation
but could.

An explicit `never` is a **statement a reviewer sees in the diff**. Deriving it from
`category == "operator"` is an **inference** that breaks silently the day a non-agent kind
is added outside that category.

Both are kept: the lint asserts `category == "operator"` ⟺ `bindable == "never"` and fails
on disagreement. Two independent expressions of one fact, cross-checked, is not two homes
for it.

### D3 — Seven bindings, not twenty-one

Bind only the kinds the seven-phase lifecycle actually dispatches: `researcher` (Discover),
`examiner` (Grill), `architect`, `planner`, `code-writer` (Execute), `reviewer` (Review),
`validator` (Validate).

Twenty-one bindings written today would be the org chart `agent-catalog.md` forbids. Seven
have a *dispatch requirement* behind them. The remaining fourteen are declared in the schema
with their `bindable` state and carry no binding record.

*Also beat:* binding none — purer, but leaves [#42](https://github.com/Akamel01/Alfred/issues/42)'s
lifecycle unexecutable.

### D4 — The binding carries the name mapping; upstream is never renamed

AutoForge's `discovery` and `investigator` both map to palette `researcher`; `worker` →
`code-writer`; `griller` → `examiner`.

Renaming ECC's files to palette names is the fork ruled out of scope on the map — §27 wants
drift **detectable, not absorbed**. Renaming the palette is worse: it is protected under
ADR-0039 and it covers eight operator kinds ECC has no concept of.

**One kind binds to several agents, keyed by phase.** `researcher → [{autoforge-discovery,
phases:[Discover]}, {autoforge-investigator, phases:[Validate]}]` records something true —
one role, two differently-tuned prompts — rather than flattening it.

### D5 — The field set, and `model` is a reference

```
kind                 palette kind id — the join to node-palette.json
bindable             agent | unbound | never
capability_id        the fingerprint's identity for this binding
agents[]             [{ agent, harness, phases[] }]
model                a routing key resolved against the routing policy — NOT a literal
tools[]              hashed into tool_version
permissions{}
context_budget
prompt_version, tool_version, context_strategy_version
```

**`model` is a reference, never a literal.** [#46](https://github.com/Akamel01/Alfred/issues/46)
owns model routing; a literal here would be a second authoritative answer to "which model
runs this role," which is what [#45](https://github.com/Akamel01/Alfred/issues/45) spent a
ticket forbidding. The binding says which routing key applies; #46 says what it resolves to.
A model-policy change then touches no binding record.

### D6 — The lint extends `lint_topology.py` and lands in the same commit

`lint_topology.py` already loads the palette, builds a kind map, validates port
compatibility, detects cycles, and carries a `self_test()`. D2's cross-check is inherently a
two-file check; splitting it across two lints means duplicating the palette loader or
leaving the invariant unowned.

`scripts/` is protected, so this is a **Gate D** change — line-by-line review plus an ADR —
either way. Extending costs one reviewed diff instead of a new file plus CI wiring.

**The same rule as #45's D6:** the lint extension lands in the same commit as
`policy/role-bindings.json`, or the file ships unenforced and says so. No
specifying-without-building.

### D7 — A binding edit is a requalification event

`capability_id`, `model_version`, `prompt_version`, `tool_version` and
`context_strategy_version` are the fingerprint's D19 group. A binding change moves at least
one of them, and tiered requalification follows through machinery that already exists.

*Beat:* "only some fields trigger" — which invites the argument you least want during an
incident, over which half of the binding changed and whether it counted. And *"bindings are
configuration, not runs"* is wrong on the register's own terms:
`tool-specification-standard.md` hashes tool **descriptions** into the fingerprint *"because
descriptions alone can change behaviour."* If a description moves the needle, a permission
set does.

**This is a feature.** It makes *"why did this agent's measured merge rate move?"* answerable
as *"its binding changed on this date, and here is the requalification that followed."*
Without it, a silent binding edit is indistinguishable from genuine capability drift — and
capability drift is the one number the autonomy gates read.

**The accepted cost:** binding edits are not cheap. They are requalification events. That is
the correct price for editing which model reviews work, and the same reason `policy/` is
protected.

## What this hands off

1. Graduate `docs/tier3/agent-definition-standard.md` from stub to the schema above.
2. `policy/role-bindings.json` with seven records (protected → **Gate D**).
3. The `lint_topology.py` extension, in the same commit as (2), plus its `self_test()` case.
4. `docs/tier3/agent-catalog.md` stays a stub until capability boundaries are observed.

Nothing here is blocked on [#46](https://github.com/Akamel01/Alfred/issues/46) except the
routing keys' *values*; the binding's reference-shaped `model` field can be written before
they resolve.
