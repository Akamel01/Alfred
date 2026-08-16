---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A phase is exited with a gate red and no waiver ADR recorded.
review_after:  Phase 2
---

# Stage Gate Definitions

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

Each phase's exit criteria and forbidden-advancement conditions, expressed as executable checks where measurable. Overriding one requires an immutable waiver ADR.

## Enforcement

`ci-gate` — owned by `executable`.

## Falsification condition

A phase is exited with a gate red and no waiver ADR recorded.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
