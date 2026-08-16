---
status:        frozen
owner:         human
enforcement:   ci-gate
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A metric is emitted outside its stated validity envelope without a warning.
review_after:  Phase 1
---

# Model and Algorithm Cards

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

Per metric: assumptions, limits, and the published validity envelope stating when the output is meaningful. Shipped with the product, not internal.

## Enforcement

`ci-gate` — owned by `human`.

## Falsification condition

A metric is emitted outside its stated validity envelope without a warning.

## Promotion

Promote this stub to full content when Phase Phase 1 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
