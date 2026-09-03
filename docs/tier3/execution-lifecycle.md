---
status:        provisional
owner:         human
enforcement:   review-cadence
evidence:      The decisions in docs/tier7/ticket-42-execution-lifecycle-decision.md, taken against the Definition of Done's twelve conditions, failure-semantics' three-valued verdict, AutoForge's protocol.md and stages/ directory, and the ECC capability audit. No task has walked these seven phases end to end; the phase set rests on a reduction of AutoForge's twelve names, not on observed execution.
falsifies_if:  A task completes the seven phases and the merge gate still catches a class of defect this lifecycle claims to prevent upstream; or the front half is observed to be skipped without the task class declaring it; or a re-entry sends work downstream of the static default.
review_after:  the first ten tasks that walk it
---

# Execution Lifecycle

The sequence a task walks from intent to merge. It owns the **order**; it owns no gate.
Where the work becomes gated, this document cites the home of the gate rather than
restating it.

Decided in [ticket #42](https://github.com/Akamel01/Alfred/issues/42); the alternatives and
why each lost are in `docs/tier7/ticket-42-execution-lifecycle-decision.md`.

## The two halves

| | Phases | Enforcement |
|---|---|---|
| **Front half** | Discover · Grill · Architect · Plan | **Method.** Nothing gates it, and nothing ever has. Saying so is a description, not a weakening. |
| **Back half** | Execute · Review · Validate | **Gated**, by `docs/tier2/definition-of-done.md`. This document does not restate those twelve conditions; duplicating them would create a second home for the merge gate. |

The front half may collapse for a declared task class. **The back half never collapses.**

The header of this document reads `review-cadence` and that is honest: the document itself
gates nothing. Definition of Done and `docs/tier1/failure-semantics.md` do.

## The seven phases

### 1 · Discover

Establish what is already true. Read the register, the code, and the prior art before
proposing anything.

*Terminates when:* a findings artifact exists naming what was read and what it constrains.

### 2 · Grill

Interrogate the requirement until the ambiguity that would have been discovered during
Execute is discovered here instead. Alternatives are recorded with the reason each lost.

*Bound capability:* `council`.
*Terminates when:* a decision artifact exists, each decision carrying the alternative it beat.

### 3 · Architect

Choose the boundaries. Which module owns which fact, which seam carries which contract.

*Bound capability:* `council`.
*Terminates when:* an architecture artifact exists naming the seams and the facts each side owns.

### 4 · Plan

Sequence the work and decompose it. Plan carries a **required independent critique pass** —
the reviewer role applied to a plan rather than to a diff. That pass is what makes plan
auto-approval safe; it is not an optional review.

*Terminates when:* a plan exists **and** the critique pass has run against it.
*Approval:* automatic. See *The one human gate*.

### 5 · Execute

Write the change.

*Bound capability:* `tdd-workflow`.
*Terminates when:* the change exists and its visible criterion executes.
*Gated by:* Definition of Done 4 and 5.

### 6 · Review

Independent review of the diff, by a party that did not write it.

*Bound capability:* `santa-method` — **two independent reviewers, both must pass.**
*Terminates when:* both reviews return a verdict.

### 7 · Validate

Run the checks that decide whether the change merges.

*Bound capabilities:* `verification-loop`, `eval-harness`.
*Terminates when:* the verdict exists.
*Gated by:* the full Definition of Done, and the three-valued verdict in
`docs/tier1/failure-semantics.md`.

## Phase termination

**A phase terminates when its required artifact exists and validates. It does not terminate
because the executing agent says it is done.**

**The check belongs to the orchestrator, never to the child that produced the artifact.**

This is not a stylistic preference. On 2026-09-02 two child sessions holding complete
contracts — objective, scope, inputs, constraints, output paths, acceptance criteria —
returned `completed` having created no branch, written no file and posted no comment, at a
combined ~136k tokens across 4 tool calls. The contracts were not the defect. Nothing
checked the artifacts before the completion was accepted.

**The three-valued verdict stays at the merge gate and appears nowhere in this document.**
`indeterminate` means *a check did not run*, and its entire meaning is that it is excluded
from the ratio the autonomy gates read. Upstream phases feed no ratio. Using the word here
would borrow precision these phases do not have.

## Task class

The task class scales the front half. **It is assigned by the orchestrator before dispatch
and is never chosen by the executing agent** — the party that wants to skip the review is
the wrong party to decide the work is small enough to skip it.

The `trivial` class is defined by `policy/model-routing.json` and
`docs/tier7/ticket-46-model-routing-decision.md`, which is one definition serving both this
document and model selection. **At Phase 0 that class is empty**: no capability carries it
until measurement supports it, so today no task collapses its front half.

## Re-entry

> **Re-entry is a phase moving backward. Escalation is the run stopping.**

These are different events with different homes. Escalation belongs to
`docs/tier3/escalation-protocol.md` (`enforcement: schema`), not here.

### The static default

| Failing phase | Default re-entry |
|---|---|
| Execute | Execute |
| Review | Execute |
| Validate | Execute |
| Architect (found later) | Architect |
| Plan (found later) | Plan |

### Override

The reviewer or validator **that found the failure** may override the default, and must
record the reason. It is the only party holding the information that distinguishes the
cases — when Validate fails, whether the cause is bad execution, a wrong plan, or a wrong
architectural boundary *is the finding itself*.

**Overrides are upstream-only.** A finder that could send work downstream of the default
could wave work past its own gate.

Absent an override the table applies. The table is never catastrophically wrong; it is only
sometimes wasteful.

## Capability bindings

| Phase | Capability |
|---|---|
| Grill, Architect | `council` |
| Execute | `tdd-workflow` |
| Review | `santa-method` |
| Validate | `verification-loop`, `eval-harness` |

Two capabilities are deliberately **unbound**:

- **`delivery-gate`** — the capability is real. Its rationalization-phrase detector catches
  an agent *stating in its own output* that it skipped or excused work, a signal orthogonal
  to anything an execution-based harness produces. But it functions only as a Stop hook, and
  the hook runtime was declined on security grounds
  ([#49](https://github.com/Akamel01/Alfred/issues/49)). It is a candidate for
  reimplementation Alfred-side over agent transcripts, with no hook.
- **`agent-self-evaluation`** — **never authoritative.** An agent rating its own output is a
  self-reported verdict from the executing session. It may inform a reviewer; it may never
  be a gate.

Phase-to-capability binding is lifecycle work and lives here. Agent-to-model-and-permission
binding does not — that is `policy/role-bindings.json`, decided in
[ticket #43](https://github.com/Akamel01/Alfred/issues/43).

## The one human gate

**One gate, at merge**, criterion-first, per Definition of Done 11. Plan auto-approves after
its critique pass.

The argument this beat: an architectural boundary chosen wrongly is the most expensive error
available, and is exactly the class a harness cannot check. It lost to capacity. O1 caps
human review at 1200 min/week against 5 merges/day, and Phase 1 already gates every one of
20+ tasks; a second per-task gate doubles consumption of the resource the factory is
rate-limited by. `docs/tier4/human-in-the-loop-policy.md` is falsified by *"a human approval
required for something the harness could have decided deterministically"* — and the
independent critique pass is a reviewer role that can perform this check.

A declared high-risk class carrying its own gate is the natural first amendment if evidence
warrants one. It was not taken now because it needs a second risk-class definition, and the
one class definition on this map belongs to model routing.

## Known gap

`human-in-the-loop-policy.md` is also falsified by *"a human decision is taken that the
evidence chain does not record."* The gate retained above therefore requires an
operator-action row in the evidence chain.

That instrument is specified in `docs/tier1/mission-control-specification.md` and **does not
exist as code**. The single human gate in this lifecycle has no recorder today. This is a
dependency carried by [Mission Control read model](https://github.com/Akamel01/Alfred/issues/52),
not a reason to add a second gate.
