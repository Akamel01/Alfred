---
status:        directional
owner:         executable
enforcement:   ci-gate
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A grant is issued on visible-criterion pass rate, or survives a fingerprint change.
review_after:  Phase 4
---

# Autonomy Graduation Policy

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

The thresholds and evidence required to grant unattended operation per task-class, and the conditions that revoke it. Calibrated on held-out pass rate only.

## Enforcement

`ci-gate` — owned by `executable`.

## Falsification condition

A grant is issued on visible-criterion pass rate, or survives a fingerprint change.

## Promotion

Promote this stub to full content when Phase Phase 4 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
