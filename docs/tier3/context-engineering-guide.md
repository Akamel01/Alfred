---
status:        provisional
owner:         human
enforcement:   review-cadence
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A context change invalidates cached prefixes without a context_strategy_version bump.
review_after:  Phase 2
---

# Context Engineering Guide

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

How context is assembled: minimal deterministic seed, most-stable-first ordering for prefix-cache reuse, retrieved content appended last, and full read-recording. Prefix order is architecture.

## Enforcement

`review-cadence` — owned by `human`.

## Falsification condition

A context change invalidates cached prefixes without a context_strategy_version bump.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
