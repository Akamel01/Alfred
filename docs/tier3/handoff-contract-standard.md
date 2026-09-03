---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      The seven phases fixed in docs/tier3/execution-lifecycle.md and the phase_end record added to docs/tier3/run-instrumentation-specification.md by ADR-0047, whose artifact_ref is a hash rather than a path (I3). Promoted ahead of its stated review_after because those two supplied the content it was waiting for; no handoff has yet been observed crossing a phase boundary.
falsifies_if:  A handoff carries prose the successor relies on without reading the underlying artifact.
review_after:  Phase 3
---

# Handoff Contract Standard

What passes between phases. The third of Alfred's three contracts, and the smallest:

| Contract | Home | Object |
|---|---|---|
| Task | `docs/tier2/task-specification-standard.md` | what the work *is* |
| Session | `docs/tier1/worker-port-contract.md` (`WorkerSpec`) | what a runtime invocation is *handed* |
| **Handoff** | **this document** | **what crosses a phase boundary** |

## The rule

**A handoff carries content-addressed references, never agent-authored summaries.**

A summary is lossy compression performed by an interested party. The successor phase that acts
on one is acting on the predecessor's account of the work rather than on the work.

## The mechanism

The rule is not advice; it is already unrepresentable to break it. `phase_end.artifact_ref` is a
**hash, never a path** (I3), so there is no field a summary could travel in.

| `phase_end` field | Obligation |
|---|---|
| `artifact_ref` | sha256 of the artifact the phase produced. Null only when `outcome` is `failed`. |
| `outcome` | `terminated` or `failed`. Two values; the three-valued verdict stays at the merge gate. |
| `checked_by` | `orchestrator`. The successor's entitlement to read the artifact rests on the orchestrator having checked it, not on the producer having claimed it. |

## What a successor is entitled to

The successor phase reads the artifact its predecessor's `phase_end` names, by hash, from the
evidence store. It is entitled to nothing else the predecessor produced.

In particular a successor is **not** entitled to the predecessor's turn transcript, its reasoning,
or any prose it emitted. Those exist in the run record stream for audit and for measurement. They
are not inputs.

## Why this is not the same as the seed

`WorkerSpec.seed_layers` is what a session is *seeded with* — ordered most-stable-first, because
prefix order is architecture. A handoff is what a phase *hands forward*. A handed-forward artifact
may become a seed layer for the next phase, and the ordering rule then applies to it as the last,
least-stable layer. The two documents describe different moments and neither re-declares the
other's fields.

## Enforcement

`schema` — owned by `executable`. The run-record validator rejects a `phase_end` whose
`artifact_ref` is not a sha256, whose `outcome` is outside the two values, or whose `checked_by` is
not `orchestrator`.

There is no lint for the *spirit* of the rule — that a successor did not silently rely on prose it
saw elsewhere — and there cannot be one from text alone. What is enforced is that the contract
provides no channel for it.
