---
status:        provisional
owner:         human
enforcement:   none
evidence:      A grilling session on 2026-09-02 against the register as it stands (Definition of Done's twelve conditions, failure-semantics' three-valued verdict and F1–F14 table, the human-in-the-loop and escalation stubs, AutoForge's protocol.md, and the ECC capability audit). No lifecycle has been run end to end; nothing here rests on an observed execution.
falsifies_if:  A task completes the seven phases and the merge gate still catches a class of defect the lifecycle claimed to prevent upstream; or the front half is observed to be skipped without the task class declaring it.
review_after:  the first ten tasks that walk it
---

# Ticket #42 — the one execution lifecycle: decision record

Resolves [The one execution lifecycle](https://github.com/Akamel01/Alfred/issues/42), a
child of [wayfinder:map — Alfred × ECC: one factory](https://github.com/Akamel01/Alfred/issues/41).

This is a **decision record**, not the lifecycle document. The lifecycle document is the
handoff (see *What this hands off* below). Nine decisions were taken; each is recorded
with the alternative it beat and why.

## The reframe that shaped everything

The ticket asked for "the one execution lifecycle," implying Alfred has none. That is half
wrong, and the half matters.

**Alfred already has phase-terminal semantics.** `docs/tier2/definition-of-done.md` carries
twelve executable merge conditions. `docs/tier1/failure-semantics.md` carries the
three-valued verdict — `pass` / `fail` / `indeterminate`, where `indeterminate` means *a
check did not run*, is excluded from merge rate on **both** sides, and is tracked instead
as a harness health metric — plus the F1–F14 fail-closed table.

What Alfred has is the **merge gate**: the end. What AutoForge has is **how the work gets
made**: the middle. They touch at exactly three points — DoD 4 and 5 (criterion execution)
and DoD 11 (criterion-first human review).

So the question was never "what are the phases." It was **how much of the middle is
load-bearing**.

## The nine decisions

### D1 — Enforcement is split: method in front, gated behind

The front half (Discover, Grill, Architect, Plan) is **method**. The back half (Execute,
Review, Validate) is **gated**, because Definition of Done already gates it.

*Beat:* enforcing the whole lifecycle as a state machine, and leaving the whole thing as
prose. The first builds machinery for the half where the value is judgment rather than
sequence, and makes the factory's own lifecycle a thing that can go `indeterminate`. The
second is what the two failed research dispatches on 2026-09-02 looked like in practice.

*Honesty note:* declaring the front half method is a description of what is already true.
Nothing has ever gated it.

### D2 — Seven phases

**Discover → Grill → Architect → Plan → Execute → Review → Validate.**

AutoForge's `protocol.md` lists twelve names for ten phases. Four are not phases:

| Dropped | Why |
|---|---|
| Critique | Folded into Plan as a required independent pass — the reviewer role applied to a plan rather than a diff |
| Approve | An output of Plan, not work performed |
| Decompose | A Plan output (the work-order DAG); nothing happens during it that isn't planning |
| Integrate, Reassess | Control flow — "check cross-module interaction" and "decide what to repeat" |

Seven is also exactly the count of AutoForge's own `stages/` directory, which suggests its
implementation had already made this reduction while its protocol document had not.

### D3 — Unconditional back half, scalable front half

Execute → Review → Validate always run. Discover/Grill/Architect/Plan may collapse for a
declared task class.

**The class is assigned by the orchestrator before dispatch, never chosen by the executing
agent.** The reason is structural: the party that wants to skip the review is the wrong
party to decide the work is small enough to skip it — the same shape as a validator
running on a trivial model.

*Beat:* an unconditional lifecycle (bureaucracy on a typo fix, and against Alfred's own
per-task-class autonomy thesis) and a fully per-class one (makes independent review
optional).

**Cross-ticket:** the `trivial` class definition is owned by
[Model routing policy](https://github.com/Akamel01/Alfred/issues/46), sub-question 3. It
is one definition serving both tickets. #42 is blocked by #46 for that fact.

### D4 — One document, `enforcement: review-cadence`, citing DoD rather than restating it

The header contract in `docs/tier7/documentation-standard.md` takes a **single** value:
`ci-gate | schema | generated | review-cadence | none`. A split-enforcement document cannot
be expressed. The fact was checked, and it broke D1's first phrasing.

Resolution: the lifecycle document is `review-cadence` throughout. Where it reaches the
back half it **cites** Definition of Done and `failure-semantics.md`. Its enforcement is
honestly `review-cadence` because the document itself gates nothing — the documents it
points at do.

*Beat:* two documents (splits one concept across two homes, against one-home-per-fact) and
one document at `schema` (a header that lies about four of seven phases).

### D5 — A phase terminates on artifact-exists-and-validates, checked by the orchestrator

The three-valued verdict stays **exclusively at the merge gate**.

*Beat:* per-phase three-valued verdicts. `indeterminate`'s entire meaning is "excluded from
the ratio the autonomy gates read." Upstream phases feed no ratio. Reusing the term there
borrows precision those phases do not have, and raises a merge-rate question nobody has
asked: does a `fail` at Architect count against an agent's measured merge rate?

**The check belongs to the orchestrator, never the child.** This is not a preference. On
2026-09-02 two child sessions with complete contracts — objective, scope, inputs,
constraints, output paths, acceptance criteria — returned `completed` having created no
branch, written no file, and posted no comment, at a combined ~136k tokens over 4 tool
calls. The contracts were not the defect. Nothing checked the artifacts before the
completion was accepted.

### D6 — ECC capability binding, and two refusals

| Phase | Bound capability |
|---|---|
| Grill, Architect | `council` |
| Execute | `tdd-workflow` |
| Review | `santa-method` (two independent reviewers, both must pass) |
| Validate | `verification-loop`, `eval-harness` |

Two are deliberately unbound:

- **`delivery-gate` — capability real, delivery mechanism closed.** The capability audit
  named its rationalization-phrase detector a genuine ECC strength: it catches an agent
  *saying in its own output* that it skipped or excused work, a signal orthogonal to
  anything Alfred's execution-based harness produces. But it functions only as a Stop hook,
  and `hooks-runtime` was declined on security grounds
  ([#49](https://github.com/Akamel01/Alfred/issues/49)). Logged as a candidate for
  reimplementation Alfred-side, over agent transcripts, with no hook.
- **`agent-self-evaluation` — never authoritative.** An agent rating its own output on five
  axes is a self-reported verdict from the executing session. It may inform a reviewer; it
  may never be a gate.

*Scope line:* phase-to-capability binding is lifecycle work and lives here.
Agent-to-model-and-permission binding is
[Role bindings](https://github.com/Akamel01/Alfred/issues/43)' and does not.

### D7 — Re-entry: static default, overridable upstream only, by the finder

A static table gives the default re-entry point per failing phase. The reviewer or
validator **that found the failure** may override it, and must record the reason.

The hard case is why: Validate fails, and the cause may be bad execution (re-enter
Execute), a wrong plan (re-enter Plan), or a wrong architectural boundary (re-enter
Architect). A static table cannot distinguish these, because the distinguishing
information *is the finding*. The finder is the only party holding it.

**Overrides are upstream-only.** A finder that could send work downstream of the default
could wave work past its own gate.

*Degradation:* absent an override you get the table, which is never catastrophically
wrong — only sometimes wasteful.

### D8 — Re-entry and escalation are different things, in different homes

> **Re-entry is a phase moving backward. Escalation is the run stopping.**

That line is the deliverable of this decision.

`docs/tier3/escalation-protocol.md` stays a stub. It keeps `enforcement: schema`,
`owner: executable`, and its own `review_after: Phase 2`. The lifecycle document cites it.

*Beat:* graduating it here (writing content the register's own stub policy says must wait
for evidence that does not exist) and superseding it (destroying a `schema`-enforced home
to feed a `review-cadence` one — the wrong direction for a register targeting ~60%
executable).

### D9 — One human gate, at merge

DoD 11, criterion-first. Plan **auto-approves** after the independent critique pass folded
into Plan by D2.

*The argument this beat:* an architectural boundary chosen wrongly is the most expensive
error available and is exactly the class a harness cannot check.

*Why it lost:* O1 caps human capacity at 1200 min/week against 5 merges/day, and Phase 1
already places a gate on every one of 20+ tasks. A second per-task gate doubles consumption
of the resource the entire factory is rate-limited by. `human-in-the-loop-policy.md` is
falsified by "a human approval required for something the harness could have decided
deterministically" — and the independent critique pass is a reviewer role that can perform
this check. This also matches AutoForge §16 (autonomous by default, escalate on structural
triggers) and Alfred's already-decided principle that agent-initiated escalation is a
budget optimization, never load-bearing.

*A declared high-risk class with its own gate* was rejected only because it needs a second
risk-class definition, and the one class definition on this map was just assigned to #46.
It is the natural first amendment if evidence warrants one.

## An open dependency this decision creates

`human-in-the-loop-policy.md` is also falsified by *"a human decision is taken that the
evidence chain does not record."* The one gate retained by D9 therefore requires an
operator-action row in the evidence chain.

That instrument is specified in `docs/tier1/mission-control-specification.md` and **does
not exist as code**. The single human gate in this lifecycle has no recorder today. This
is not a reason to revisit D9; it is a dependency carried by
[Mission Control read model](https://github.com/Akamel01/Alfred/issues/52).

## What this hands off

Decisions, not deliverables — the map's default. Remaining work, all authoring rather than
deciding:

1. Write the lifecycle document itself: Tier 3, `enforcement: review-cadence`, seven
   phases, the static re-entry table, the citation lines to DoD and
   `escalation-protocol.md`.
2. The per-phase artifact list. Its **homes** belong to
   [State authority](https://github.com/Akamel01/Alfred/issues/45), not here.
3. Register entry via `scripts/lint_docs.py` regeneration.

## Vocabulary

Nine terms were resolved and written into `CONTEXT.md` § Execution Lifecycle Terms in the
same commit: Execution Lifecycle, Phase, Phase termination check, Front half / back half,
Critique pass, Re-entry, Escalation, Task class, Never authoritative.
