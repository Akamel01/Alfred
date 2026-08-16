---
status:        provisional
owner:         generated
enforcement:   generated
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  The generated model diverges from what the ingest adapters actually produce.
review_after:  Phase 1
---

# Domain Model

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

The canonical trajectory and scenario schemas, generated from the Pydantic definitions. It is the load-bearing abstraction every metric and adapter depends on.

## Enforcement

`generated` — owned by `generated`.

## Falsification condition

The generated model diverges from what the ingest adapters actually produce.

## Promotion

Promote this stub to full content when Phase Phase 1 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
