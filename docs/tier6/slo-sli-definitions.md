---
status:        directional
owner:         executable
enforcement:   schema
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  An objective is breached repeatedly with no alarm configured for it.
review_after:  Phase 3
---

# SLO and SLI Definitions

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

Service level indicators and objectives, including wall-clock per merged task and review-backlog depth as first-class factory metrics.

## Enforcement

`schema` — owned by `executable`.

## Falsification condition

An objective is breached repeatedly with no alarm configured for it.

## Promotion

Promote this stub to full content when Phase Phase 3 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
