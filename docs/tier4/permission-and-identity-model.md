---
status:        frozen
owner:         executable
enforcement:   schema
evidence:      Graph-level visibility controls were verified not to constitute a boundary — private state schemas do not hide channels from stream, output_keys is caller-side, and the checkpointer persists everything. The security property has to come from physical separation.
falsifies_if:  An agent-role connection succeeds against a held-out, verdict or policy table, or any identity is found holding a permission not listed here.
review_after:  Phase 2
---

# Permission and Identity Model

Who may do what, and what enforces it. Every boundary here is physical — a separate
process, a separate OS user, a separate database role. **Runtime field-name checks are
never a boundary.**

## Identities

| Identity | Is | Holds |
|---|---|---|
| Operator (interactive) | the human | no write access to `harness/`, policy config, or the Postgres data directory |
| `alfred-svc` (OS user) | owns the harness | `harness/`, `policy/`, Postgres data; not writable by the operator account |
| Container process | the agent | no credentials of any kind; a fixed read mount, a narrow write mount, deny-by-default network |
| Patch validator | uncontaminated | the fine-grained VCS token; never runs agent code |
| `alfred_harness` (DB role) | writes evidence | evidence, verdicts, run history; cannot read held-out values |
| `alfred_criterion` (DB role) | computes verdicts | held-out values at verdict time; writes verdict rows |
| `alfred_agent` (DB role) | exists to be denied | nothing in evidence, verdict, held-out or policy schemas |
| `alfred_migrator_*` | applies migrations | one role per schema directory |

## Why the operator is constrained too

The operator cannot write `harness/` or the policy configuration from their interactive
account. This is not distrust; it is the same argument applied consistently. The failure
this architecture is guarding against is a change that looks like an improvement and
quietly weakens a check — and the operator, under time pressure, is exactly as capable of
making that change as an agent is.

Changing the inspector requires switching to the service account deliberately, and every
such change carries a mandatory ADR.

## Held-out isolation

Held-out values are isolated by **SQL grant**, in a separate schema owned by a separate
role, materialized only at verdict time. They are never placed in graph state.

This is a correction to an approach that looked sufficient and was not: `private` state
schemas do not hide channels from stream, `output_keys` is a caller-side argument rather
than a graph-level guarantee, the checkpointer persists everything, and a filter predicate
on an index is not a boundary.

Every human read of a held-out artifact is logged to the evidence store. Held-out failure
diagnosis emits only a pass/fail class label into task context — never the trace.

If subagent isolation ever becomes part of the design, sibling messaging is explicitly
denied and context forks are forbidden. A sibling roster is a lateral channel.

## Verdict ownership

Verdict fields are owned by deterministic nodes. Agent nodes are schema-forbidden from
writing them, and a CI lint asserts that no agent-invoking node's return annotation
includes a verdict field — because the graph engine raises only on *concurrent*
unreducered writes, and a sequential write to a verdict field raises nothing at all.

The verdict module has no import path from any agent module. That is checked, not assumed.

## The advisory judge

An LLM judge may raise escalations and flag suspected reward hacking. It is treated as a
capability with its own golden tasks, its own measured false-escalation rate, and its own
fingerprint.

It receives **harness-extracted structural features** — files touched, criterion deltas,
tolerance changes, test-file edits — with agent-authored comments and commit messages
stripped, so it cannot be argued with by the thing it is judging. Its golden set includes
adversarial-suppression cases.

It can only *add* escalations. Structural triggers fire deterministically regardless, so
the judge can never be the reason an escalation did not happen.
