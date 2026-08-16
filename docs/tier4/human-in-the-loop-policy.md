---
status:        provisional
owner:         human
enforcement:   review-cadence
evidence:      none — written pre-Phase-0 as a register stub (D32). Its evidence is Phase 1's twenty-plus human gates and the review time they produce, which is why its review point moved from Phase 3 to Phase 1.
falsifies_if:  A human approval is required for something the harness could have decided deterministically; or a human decision is taken that the evidence chain does not record.
review_after:  Phase 1
---

# Human-in-the-Loop Policy

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

Where a human must act, what they are accountable for, what the harness must never
delegate to them, and what a human is never permitted to do. The human checks what the
harness structurally cannot — whether the criterion was the right criterion, whether the
agent solved the stated problem or a nearby easier one, future coupling cost, and whether
a metric's validity envelope is honestly stated.

**This document owns the policy. It does not own the surface.** The screens, the recorded
operator-action rows, the refusal rules and the review-timing instrument are specified in
[Mission Control Specification](../tier1/mission-control-specification.md).

## Why the review point moved

This stub carried `review_after: Phase 3` on the assumption that its evidence was Phase
3's capacity data. That was a structural error. Phase 1 puts a human gate on every one of
20+ tasks and is the phase that *produces* human minutes per task; major-fix #10 then
turns that number into an executable gate. The evidence arrives in Phase 1, so the policy
is answerable in Phase 1. Deferring it to Phase 3 deferred it past the phase that
generates the only data it rests on.

## Enforcement

`review-cadence` — owned by `human`. The mechanical half is not here: the operator-action
records, the grant separation and the approve-precondition refusals are schema-enforced in
the Mission Control Specification.

## Falsification condition

A human approval is required for something the harness could have decided
deterministically; or a human decision is taken that the evidence chain does not record.

## Promotion

Promote this stub to full content at Phase 1 exit, when review time, escalation-handling
time and the distribution of what humans actually caught are all recorded rather than
imagined. On promotion, replace `evidence:` with what the content actually rests on.
