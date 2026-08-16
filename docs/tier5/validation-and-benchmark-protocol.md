---
status:        provisional
owner:         human
enforcement:   ci-gate
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A benchmark claim is made that its method cannot support.
review_after:  Phase 2
---

# Validation and Benchmark Protocol

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

How results are validated against the oracle and against held-out perturbations, and how benchmark runs are recorded immutably. Names what each comparison can and cannot establish.

## Enforcement

`ci-gate` — owned by `human`.

## Falsification condition

A benchmark claim is made that its method cannot support.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
