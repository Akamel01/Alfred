---
status:        provisional
owner:         human
enforcement:   none
evidence:      A read of policy/node-palette.json's port declarations, orchestration/topology.json as it stands (8 nodes, 7 edges), lint_topology.py's TOP003-TOP005 port-compatibility rule, and the nine edge kinds proposed in the brief's §8. The proposed topology in D4 was verified by running check_topology against a candidate tree, not asserted.
falsifies_if:  An edge kind rejected here is later needed to answer a question no existing edge answers; or the type graph is found being executed rather than validated against.
review_after:  Phase 2
---

# Ticket #47 — execution edge semantics

Resolves [issue #47](https://github.com/Akamel01/Alfred/issues/47). Five decisions, one of
which was already taken elsewhere and one of which uncovered a blocker.

## D1 — Two graphs. Already decided, before this ticket was opened

`CONTEXT.md` § *State Authority Terms*, and now ADR-0047's ownership router:

> The type graph is `policy/node-palette.json` + `orchestration/topology.json` — which roles
> exist and how they may connect. The instance graph is `control.work` — which tasks exist and
> what blocks what. **The instance graph is validated by the type graph; it is not a second
> authority.**

The proposal this ticket asked to test is the decision [#45](https://github.com/Akamel01/Alfred/issues/45)
already took. What remained was making it true rather than asserted — which is D3.

## D2 — Four contract types. Zero additions

The vocabulary is closed by the palette's port declarations: `delegates-to`, `feeds`,
`hands-off-to`, `reviews`. Plus `blocked_by` on the instance side.

Each of §8's nine, against the test *"name a question no existing edge answers"*:

| Proposed | Verdict | Why |
|---|---|---|
| dependency | duplicate | `blocked_by`, instance side |
| data | duplicate | `feeds` |
| handoff | duplicate | `hands-off-to` |
| review | duplicate | `reviews` |
| validation | **merge into `reviews`** | The distinction is which capability sits at the endpoint. That is the node's kind, not the edge's type |
| context | **reject** | Context flow is `WorkerSpec.seed_layers`, ordered most-stable-first. An edge would be a second, unordered description of a thing whose order is architecture |
| escalation | **reject** | `escalation-protocol.md` owns it (`enforcement: schema`), and #42's D8 is explicit: *"Re-entry is a phase moving backward. Escalation is the run stopping."* A stop is not a traversal |
| ownership | **reject** | This is the ownership router. A register fact wearing edge clothing |
| supersession | **reject** | ADR-log fact. `Supersedes:` is in every ADR header and `lint_adr_numbers.py` already reads it |

The ticket's own warning is the finding — *"do not create edges just because graph visualization
looks attractive."* Applied honestly it rejects five of nine and dedupes the other four.

## D3 — Instance edges live in `control.work`

Per ADR-0047 decision 2. AutoForge's `work-order.json` sits in `.autoforge/`, which the router
now says **owns nothing and is never evidence**. A dependency an audit reads cannot live there.

## D4 — The topology is rebuilt from the seven bindings, by the operator — and the palette blocks it first

The current file is a sample: **8 nodes, 7 edges**, using kinds that predate the bindings.

The real shape is knowable now: #43 bound seven capabilities and #42 fixed the phase order.
A candidate was built and run through `check_topology`, and it lints clean at 15 nodes+edges —
**but only against a palette with six port additions.**

**The blocker, measured rather than guessed.** An edge requires its contract type to appear in the
source kind's `out` *and* the target kind's `in` (TOP005). Four of the seven lifecycle links fail
that today. The worst case is `planner`, whose `in` is `[]` — it accepts nothing at all, so no
phase can hand it work.

```
examiner     in += hands-off-to    out += feeds
architect                          out += feeds
planner      in += feeds
reviewer                           out += hands-off-to
validator    in += hands-off-to
```

**`policy/node-palette.json` is protected and is the type system (ADR-0039).** A port addition is
heavier than a topology edit: it changes what connections are expressible anywhere.

**Resolved by ADR-0048**, after the operator chose `hands-off-to` for both links this record was
unsure about. The final shape is **seven additions, all `hands-off-to`** — cleaner than the six
mixed types drafted here, because every phase transition turned out to mean the same thing.

**The graph is eight roles, not seven.** `wayfinder` was `unbound` because its skill carried
`disable-model-invocation: true` and no agent could run it. The operator removed that flag on
2026-09-03, so the fact changed and the binding followed. It enters as the entry point
(`wayfinder --delegates-to--> researcher`) and **costs no port addition** — both ends already
declare `delegates-to`.

`orchestration/topology.json` is still not written here; it is operator-only, and the verified draft
is on the issue.

**`orchestration/` is operator-only.** The draft was written; the file was not.

## D5 — The type graph is never executed, and saying so is the answer

It is a *validation* artifact: `lint_topology.py` checks the instance graph against it. What
executes is the orchestrator walking `control.work`, which is Alfred code. Nothing in ECC executes
a graph — AutoForge's `work-order.json` DAG is read by a prose protocol, not by a runtime.

§8's four words map onto things that exist or are now specified:

| §8 word | What supplies it |
|---|---|
| inspectable | the canvas and the vault |
| auditable | the run record stream, now carrying `phase_start` / `phase_end` |
| recoverable | `control.work`, under the append-only and hash-chain properties |
| executable | **the orchestrator, not the graph** |

Only *executable* was ever ambiguous, and it belongs to the walker rather than to the thing walked.

## Consequences

- The edge vocabulary does not grow, so `lint_topology.py`'s compatibility matrix does not grow.
- The topology's staleness is now a named, sized piece of work with a verified draft behind it,
  blocked on one protected-file change the operator owns.
- Five proposed edge kinds are refused with reasons, so the proposal does not return unargued.
