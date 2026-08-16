---
status:        directional
owner:         human
enforcement:   ci-gate
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A configuration change is accepted on an effect size below the set's resolution.
review_after:  Phase 3
---

# Agent Evaluation Protocol

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

How a capability is measured: golden set construction against parent commits, stratification, and the detectable effect size every comparison must report.

## Enforcement

`ci-gate` — owned by `human`.

## Falsification condition

A configuration change is accepted on an effect size below the set's resolution.

## Promotion

Promote this stub to full content when Phase Phase 3 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
