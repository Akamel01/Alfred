---
status:        directional
owner:         executable
enforcement:   review-cadence
evidence:      Reads the frozen task specification standard, the glossary's Capability and Autonomy-grant definitions, the run fingerprint module's stated design properties, the run instrumentation specification's attempt_start assertion, and the vendored AutoForge model policy as it exists on this machine. No measurement of any model against any Alfred capability exists yet; the decisions that would need one are deliberately deferred rather than guessed.
falsifies_if:  A model is selected for an Alfred capability by a path this document does not describe, or a factory merge rate is quoted without a fingerprint it is measured on.
review_after:  Phase 2
---

# Ticket #46 — Model routing policy: home and content

Resolves [issue #46](https://github.com/Akamel01/Alfred/issues/46). Six decisions.
Downstream of #42 (which needs the `trivial` class defined) and #43 (whose binding
`model` field is a reference into this policy).

## Why this ticket was smaller in some places and larger in others than it looked

Three of the five questions were already answered by frozen documents, and the ticket
did not know it. One was answered *wrongly* by the ticket's own proposed definition.
And one fact nobody had connected reframes the whole thing.

**The reframing fact.** `docs/tier0/glossary.md`:

> **Autonomy grant** — permission for a task-class to run unattended. Reads *"X% merge,
> Y wall-clock per success, on fingerprint Z."* **Suspended by any fingerprint change**;
> expires.

`model_version` is a D19 field. D19 is in the fingerprint. Therefore **a model change
suspends every autonomy grant measured on that fingerprint.** Model routing is not a
configuration knob that happens to have a cost. It is the identity autonomy is measured
against. Every decision below follows from taking that literally.

## D1 — A factory run produces a `FactoryFingerprint`, sharing the D19 group verbatim

`RunFingerprint` cannot describe a factory agent. Its `lane` and `D40` groups are
self-hosted-inference fields — `quantization`, `loaded_context_length`, `parallel_slots`,
`quant_artifact_sha256`, `inference_runtime_version`, `server_version`. None has a value
for an API-served model. And `harness/fingerprint/record.py` forbids the obvious patch:

> **A missing field is an error, not a default.** A record that cannot state a field
> cannot assert on it, and a field defaulted at construction is a field that silently
> stops discriminating.

So adding nullable lane fields is disqualified by the module's own stated design
property — it would weaken the record for the product runs it was built for, in order to
admit runs it was not.

**The decision:** a second record type. It shares the D19 group **verbatim**
(`capability_id`, `model_version`, `prompt_version`, `tool_version`,
`context_strategy_version` — already harness-agnostic; they describe an agent, not a GPU),
carries a third group for API-served identity (`provider`, `model_id`, `api_version`,
`routing_key`, `harness_identity`), and carries **no lane or quantization group at all**.

Same ACS-1 hashing, same construct-complete-or-not-at-all rule, same both-directions
comparison — the three properties `record.py` names as what stops a fingerprint from
being one.

**What this buys.** #43's D7 — *a binding edit is a requalification event* — becomes true
rather than aspirational, because the binding's version fields now hash into something.
And a factory merge rate can be quoted in the sentence shape the glossary already
defines: *"X% merge, on fingerprint Z."* Without D1, factory autonomy is unmeasurable on
exactly the work this coupling exists to accelerate.

**Rejected: extend `RunFingerprint`.** See above.
**Rejected: no factory fingerprint at all.** Cheapest, and it leaves #43's D7 attached to
nothing and factory evidence bound to no declared identity.

## D2 — Home is `policy/model-routing.json`; ECC gets an explicit per-spawn override, not a projection

`policy/` is already a protected prefix in `policy/protected-paths.json` (*"machine-readable
Tier 4 — allowlist, denylist, and this set"*). So the file is protected on arrival and the
protected set itself needs no edit — the same shape #43 found for `agent-definition-standard.md`.

For the ECC seam, Alfred passes the model explicitly on every spawn. The vendored
`model-policy.yaml` default is never consulted. No generator, no sync obligation, no drift
check, no projection.

This is the stronger form of a question ADR-0035 already answered once, for the protected
set: *a projection is not a second authority, the single home is the file.* Choosing an
explicit override means there is no projection to reason about at all.

**The addition that makes it safe.** "Never consulted" is a claim, and it needs a floor.
If an Alfred spawn ever omits the override, the vendored default takes effect — and that
default is `gpt-5-nano`. The failure would land silently on the **permissive, cheap** side.
That is the direction this project has already paid for three times, enumerated in
`scripts/lint_ci_coverage.py`'s docstring: *"An enumeration drifts silently, in the
direction that reads green."*

So the vendored `model-policy.yaml` defaults are rewritten to a model that fails **loudly
and expensively** rather than cheaply and quietly. A wrong-but-expensive default surfaces
the omission on the invoice. A wrong-but-cheap one hides it until a validator has been
running on a trivial model for a month.

## D3 — `inherit` is forbidden. Every routing key resolves to a pinned model identity

The vendored policy resolves `architect`, `planner`, and `reviewer` to `inherit`, commented
*"→ orchestrator model (selected via desktop dropdown / `/models`)"*.

Under D1 that value lands in `model_version`, a D19 field, hashed into the fingerprint the
autonomy grant is bound to. So `inherit` means: **the fingerprint changes when someone
changes a dropdown, silently suspending every grant measured on it.**

**Rejected: permit `inherit` but resolve-and-record at spawn.** This is the reasonable-
sounding middle and it is the trap. It makes the *record* honest while leaving the *policy*
unable to answer "which model reviews this capability?" without knowing a UI state at a past
moment. That is a fact with no home — precisely what #45 spent a ticket eliminating.

Under D3, if the orchestrator model genuinely is the right answer for a capability, the
policy names it. When it changes, that is a visible diff to a protected file and a
deliberate requalification — which is what D1 makes it mean.

**The accepted cost, stated rather than glossed.** D3 makes changing your session model a
protected-file edit if you want the change to reach spawned agents. That is real friction on
something currently one dropdown away, and it will be felt weekly rather than theoretically.
It is the correct friction: the alternative is that the model reviewing Alfred's work is set
by an unversioned UI control.

## D4 — The routing key is `capability_id`. No override layer

The ticket offered three candidates. Two are foreclosed by frozen documents.

**Not palette kind.** `docs/tier2/task-specification-standard.md` (frozen,
`enforcement: schema`) requires the field `capability` — *"The capability this dispatches
to. **Never a role.**"* The glossary agrees: *"**Capability** — `(input contract, output
contract, tools, permissions, criteria, escalation)`. The unit an agent is scoped to.
**Never a job title.**"* Stated twice, in two binding documents. A palette kind is a job
title.

**Not task class.** The term already has exactly one meaning in this register — the
product's schedulable CriMe class (`sandbox-specification.md`, `risk-register.md`,
`charter-and-non-goals.md`, and the glossary's autonomy-grant entry). Autonomy is granted
per task-class against merge rate. A second factory-scoped meaning is one term with two
homes.

**So: `capability_id`.** It is the key the frozen schema already requires every task to
carry. It is the key the D19 group already carries. #43's bindings declare which
`capability_id` a palette kind resolves to per phase; this policy says what model that
capability runs on. One join, no precedence rules to document.

Note what this makes of #43's artifact: `role-bindings.json` carries `capability_id`,
`tools[]`, and `permissions{}` — three members of the glossary's capability tuple. It **is**
the capability definition, keyed by palette kind. This ticket supplies the fourth thing a
capability needs to run.

**Rejected: capability plus a task-class override layer.** This is the one I expect to want
later and it should still be refused now. A precedence rule between two keys is the
two-authorities-for-one-fact shape #45 eliminated. And the capability tuple already contains
`permissions` and `criteria`: if work is riskier, that is a **different capability**, not the
same capability with a modifier.

## D5 — `trivial` is a defined, currently empty class

**The ticket's own candidate definition is dead.** It proposed *"a task class whose
acceptance criteria are fully machine-checkable and whose blast radius is bounded by
`touches`."* Both halves are already universal:

> **A task is only schedulable if it carries an executable acceptance criterion.** …
> There is no override.

> `writable_paths` | Must not intersect the protected set.

Every schedulable task has both. A property all tasks share cannot pick out a subset.
(`touches` is AutoForge vocabulary; Alfred's equivalent is `writable_paths`, and it is
already constrained for everything.)

**The decision:** `trivial` exists in the schema as a capability attribute. **No capability
carries it at Phase 0.** A capability enters the class only through measurement, on the same
evidence path an autonomy grant uses. Until then, every capability routes to a capable model.

This is the register's own stance applied to itself.
`docs/tier3/autonomy-graduation-policy.md` is a deliberate stub whose evidence field reads
`none — written pre-Phase-0 as a register stub (D32)`, and whose body says: *"content written
before the evidence exists cannot be current, and a wrong document is worse than an absent
one."* A trivial-class allowlist authored today would rest on nothing. No measurement exists
of any model against any Alfred capability.

**Rejected: enumerate the trivial capabilities now.** This is how the vendored policy got
`validator: gpt-5-nano`, `requirements-griller: gpt-5-nano`, and `investigator: gpt-5-nano` —
six roles assigned to a trivial model by throughput reasoning rather than by evidence. The
mechanism that produced the bug is not the mechanism to standardize.

**The consequence, stated plainly.** Under D5, `gpt-5-nano` runs nothing on day one. That is
a real reduction against the brief's §11, which authorizes it for genuinely trivial
mechanical work. What is honored is the brief's **constraint** — never for architecture,
requirements, contracts, security, state machines, schema, refactors, debugging, validation
authority, final review, or conflict resolution. What is deferred is its **permission**, until
something measures it. The cheap-model savings arrive later with evidence, or they do not
arrive.

**This is the answer #42 was blocked on.** Its `trivial` task class is a defined, empty class.

## D6 — Enforcement: three checks (P, A, V), landing with the policy file

The ticket asked whether this is checkable at all, given that selection happens at spawn time
in a harness Alfred does not control. Two precedents say yes, and neither requires controlling
the harness.

`scripts/lint_verdict_boundary.py` states the principle: *"the boundary is physical … and the
security property comes from port separation, never from inspecting field names at runtime."*
And `attempt_start` already does the runtime half for the lane: `loaded_context_length` is
*"**asserted against the fingerprint, not read from it** … Mismatch is fail-closed: the attempt
does not start."*

**P — policy conformance (static, CI).** No `capability_id` in `role-bindings.json` resolves
to a model this policy forbids for it. Catches the `validator: gpt-5-nano` class of bug in the
diff, before any spawn. This is the check that does the work.

**A — assertion at attempt start (runtime, fail-closed).** The model the harness reports is
compared against the one the task's fingerprint declares; mismatch means the attempt does not
start. The identical rule `loaded_context_length` already gets, for the identical reason
stated in the instrumentation spec: *a fingerprint field the server can change unobserved is
not a fingerprint unless something checks it.*

**V — vacuity guard.** Both checks report how many records they scanned, and a check that
scanned zero **fails**. Taken verbatim from `lint_verdict_boundary.py`, whose docstring
explains why: today there is no agent node to look at, so without the guard the lint reports
green for a reason unrelated to the property — and keeps reporting green on the day the first
real one lands.

A is what keeps P non-vacuous once runs exist.

**Landing rule.** Per `gates.yml`, quoted in `lint_ci_coverage.py`: *"If a check a document
names is not in this file, that document's enforcement value is a wish."* So, as in #45's D6
and #43's D6: the lint ships in the same commit as the policy file, or the policy file
declares `review-cadence` and says out loud that it is unenforced. This document carries
`review-cadence` for exactly that reason — it specifies; it does not yet enforce.

## Handoff

Authoring, not deciding.

| Work | Gate |
|---|---|
| `policy/model-routing.json` — map `capability_id` to a pinned model; `trivial` attribute present and unset on every capability | Gate D (`policy/` prefix) |
| `scripts/lint_model_routing.py` — checks P and V; ships in the same commit as the policy file | Gate D (`scripts/` prefix) |
| `FactoryFingerprint` record beside `harness/fingerprint/record.py`, sharing the D19 group | Gate D (`harness/` prefix) |
| Check A in `attempt_start` validation — model asserted against the declared fingerprint, fail-closed | with the instrumentation validator |
| Rewrite vendored `~/.config/opencode/autoforge/model-policy.yaml` defaults to fail loudly; remove every `inherit` | outside the repo — not gated, record the change |

## Open, deliberately

**The measurement D5 defers to does not exist and is not scheduled.** Until it is, no
capability becomes trivial and the cheap-model path stays dormant. The lever for exercising
it sooner is commissioning that measurement — not enumerating a list.
