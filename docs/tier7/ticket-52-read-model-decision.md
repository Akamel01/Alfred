---
status:        provisional
owner:         human
enforcement:   none
evidence:      A read of docs/tier1/mission-control-specification.md — the boundary split, the read-model section's no-cache rule, and the decision-critical panel rule — against the brief's §18 snapshot contracts and §19 failure list. Neither Mission Control program exists as code; nothing here rests on an observed render.
falsifies_if:  A stored aggregate, materialized view or cache appears in the read model; or a decision-critical fact is found rendered from the read model rather than from the command surface; or a degraded state renders as a normal one.
review_after:  the first screen that exists
---

# Ticket #52 — Mission Control's read model

Resolves [issue #52](https://github.com/Akamel01/Alfred/issues/52). Five decisions.

**This record contradicts the brief's §18, deliberately and with the operator's agreement.**
That is stated first because a contradiction discovered later reads as an oversight.

## D1 — Queries at request time. No snapshots, and no event stream either

`mission-control-specification.md` § *The read model* forecloses §18 outright:

> **Every screen is a query executed at request time.** No denormalized dashboard table, no
> materialized view, no application-level cache, no background refresh job. … **A cache is a
> source of truth with a shorter memory.** If a query is too slow, the fix is an index or a
> narrower query. It is never a stored aggregate.

§18's eight versioned snapshot contracts — `MissionStateSnapshot`, `ExecutionNodeSnapshot`,
`AgentSessionSnapshot`, `ArtifactSnapshot`, `ValidationSnapshot`, `ReviewSnapshot`, `RiskSnapshot`,
`NotificationSnapshot` — **are** the denormalized tables that rule forbids. Persisting them would
create a second source of truth able to disagree with the evidence chain, on the one surface where
disagreement means an operator approves the wrong thing in good faith.

**The event stream goes too, and for a cheaper reason.** §19's duplicate, partial and reordered
event requirements exist *only because there are events*. Removing the stream removes the failure
class rather than handling it.

**What is lost, stated rather than glossed: liveness.** A request-time query cannot push. The
replacement is polling, with the chain head as the freshness marker — the specification already
requires *"Every page states the chain head it was built from"*. Worse interaction than a
websocket; strictly better epistemics, because every rendered page names exactly the chain state it
describes.

**The eight names are not retained.** They named stored objects, and no stored object survives.

**`RiskSnapshot` is refused twice over** — #45 gave risk score no home, and #51 measured ECC2's as a
sum of hand-tuned constants against hardcoded thresholds.

## D2 — Provenance is which program served the fact, enforced structurally, not a field

A provenance *field* would be a claim the read model could write, and the read model is the
agent-writable half. The specification's control is physical instead:

- `alfred_readmodel` holds SELECT and nothing else, with **no grant at all on `heldout`**.
- The decision-critical panel — verdict triple, which criteria executed, held-out class label, the
  twelve Definition-of-Done states, budget consumption, anomaly flags — is rendered **by the
  command surface from its own queries**.
- No import path between the two programs, CI-checked.

Provenance is therefore already true by construction. The UI's only job is to make it *visible*: a
persistent visual distinction between command-surface and read-model regions, so an operator can
see at a glance which half drew a number.

Same shape as #43's D2 — state it explicitly *and* derive it structurally, and let the structure be
what enforces it.

## D3 — Runtime state enters through a third, labelled path that neither authority uses

The read model does not read runtime state. The command surface does not read it either.

ADR-0047 says runtime state owns nothing and is never cited by a gate, verdict or audit. Mission
Control must still show in-flight liveness, so a path exists — it simply must not be either
authoritative one.

`CONTEXT.md` § *State Authority Terms* already names the rule: **display-only**, carrying
provenance that says it is unverified, and *"a missing display-only fact renders as **unknown**,
never as **none**"*.

When the boundary is unavailable the answer is **unknown**, and the surface stays fully usable —
because nothing an action depends on came from there.

## D4 — Versioning mostly dissolves under D1

With no stored snapshots there is no persisted shape to migrate. What remains is the wire shape
between the two programs, and the specification already supplies the mechanism: pages state the
chain head they were built from and post it back with any action, so a stale page fails optimistic
concurrency and is re-rendered.

`operator_action` keeps its own `field_set_version`, which the ownership router already assigns to
the Mission Control specification.

## D5 — The degradation contract

*"Fails gracefully"* is not a specification. This is:

| §19 failure | Required rendered behaviour |
|---|---|
| Agent crash mid-run | Last `phase_end`, then **unknown**. Never *complete*, never *failed* |
| Backend restart | Page re-queries; chain head changes; any in-flight action fails concurrency and is re-shown |
| Stale session | Rendered with its age, marked stale. Never hidden — a hidden stale session is indistinguishable from none |
| Missing session | **unknown**. Never *none* |
| Partial / duplicate / reordered events | **Cannot occur.** There is no event stream (D1) |
| Malformed state | The panel refuses to render and names the query that failed. Never a partial panel — a partial decision-critical panel is the failure the boundary split exists to prevent |
| Orphaned worktree | Listed as orphaned, with its ref. Never auto-cleaned from a read-only surface |
| Harness failure | Queue renders; dispatch actions disabled with the reason shown. Read stays up when write is down |

The through-line: **every degraded state renders as itself, and no degraded state renders as a
normal one.**

## Consequences

- The read model is a set of query shapes, not a schema. Nothing to migrate, nothing to invalidate.
- One class of bug — duplicate, partial and reordered events — is designed out rather than handled.
- The brief's §18 does not survive contact with the specification, and this record says so where a
  reader will find it.
- Liveness is degraded on purpose. If that proves intolerable in use, the amendment is a shorter
  poll interval, never a stored aggregate.
