---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A deploy occurs by any path other than CI on merge.
review_after:  Phase 2
---

# Branch, Release and Deploy Protocol

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

Branch naming, protected refs, release tagging, and the CI-triggered deploy path with rollback. Agent branches cannot trigger secret-bearing workflows.

## Enforcement

`ci-gate` — owned by `executable`.

## Falsification condition

A deploy occurs by any path other than CI on merge.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
