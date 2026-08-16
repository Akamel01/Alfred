---
status:        frozen
owner:         executable
enforcement:   schema
evidence:      The schedulability rule is the mechanism behind every credible agent coding result; the interface-signature requirement comes from SWE-bench Pro, which had to add human-authored interface specs because valid solutions were failing as false negatives.
falsifies_if:  A task passes validation, dispatches, and its criterion turns out to be unexecutable or to admit a solution that does not solve the stated problem.
review_after:  Phase 2
---

# Task Specification Standard

The schema a work item must satisfy to be schedulable. Enforced by Pydantic validation
in the control plane, not by review.

## The rule

**A task is only schedulable if it carries an executable acceptance criterion.**

Prose-only tasks are not tasks. They fail validation, are marked unschedulable, and
escalate to a human for criterion authoring. There is no override — a task dispatched
without an executable criterion has no verdict mechanism, and a run with no verdict
mechanism produces a claim nobody can check.

## One criterion, one task

A task carries exactly one criterion. Work needing several criteria is several tasks.

Agents may create subtasks freely, each receiving its own budget allocation. The
accepted exposure — that budget ceilings become advisory because an agent near its cap
can split — is recorded as R5 in the Risk Register with its revisit trigger.

## Required fields

| Field | Notes |
|---|---|
| `id` | UUIDv7. Sortable, typed distinctly from every other entity ID. |
| `org_id`, `project_id` | Tenancy scope. Present from the first migration even with one tenant. |
| `title`, `intent` | What the change is for. The reviewer reads intent before anything else. |
| `capability` | The capability this dispatches to. Never a role. |
| `criterion` | See below. Must validate as executable. |
| `held_out_criterion_ref` | Reference only. The value lives behind a separate DB role and is materialized at verdict time. |
| `readable_paths` | Fixed by the harness at dispatch, enforced by the filesystem mount. Never chosen by the agent mid-run. |
| `writable_paths` | Must not intersect the protected set. |
| `budget` | Turn cap, token cap, wall-clock cap. All three are escalation triggers. |
| `retry_budget` | Bounded. Retries select against visible criteria only. |
| `fingerprint` | The full identity the resulting measurement will describe. |
| `parent_task_id` | Null for roots. Present for agent-created subtasks. |
| `schema_version` | Tasks will change shape; unversioned records cannot be replayed. |
| `idempotency_key` | Every mutating operation carries one. Retries are inevitable from Phase 3. |

## What a criterion is

A criterion is **(assertion + interface signature + threshold provenance)**.

**Assertion** — an executable check producing pass or fail on a clean checkout. Run by
`CriterionRunner`, outside the agent's tree, from trusted provenance.

**Interface signature** — the callable shape the solution must expose. This exists
because under-determined criteria reject valid solutions as false negatives; SWE-bench
Pro had to bolt human-authored interface specs onto every task for exactly this reason.
This component cannot fully graduate to agent authorship, since it is the thing
preventing those false negatives.

**Threshold provenance** — where any numeric threshold came from: citation, version,
and the fact that a human declared it. Thresholds are configuration inputs, never
agent-authored, never presented as facts.

## Visible and held-out

Every task carries a visible criterion and references a held-out one.

- **Visible** — tests the unit in isolation. The agent sees it and retries against it.
- **Held-out** — composes operations end-to-end across scenario families. The agent
  never sees it, never retries against it, and acceptance requires it to pass.

Held-out failure returns only a pass/fail class label into task context. Never the
trace, never the failing values — a diagnostic detailed enough to be useful is
detailed enough to be optimized against.

## Escalation, not self-assessment

The agent cannot write `blocked` or `complete`. Status transitions on structural
triggers only: iteration cap, budget exhaustion, criterion red after N attempts,
protected-path attempt, tool unavailable, turn count, token spend, wall-clock.

Every escalation carries a structured attempt bundle: what was tried, what was read,
what the criterion said. Agent-initiated escalation is permitted as a budget
optimization and is never load-bearing.

## Authorship ladder

Criteria start human-authored. They graduate to agent-authored **per task-class**,
only after paired data shows agent-authored criteria are equivalent — calibrated on
held-out pass rate, never on visible pass rate, because calibrating on visible would
certify exactly the agents that saturate the visible suite by hacking it.
