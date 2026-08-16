---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  An agent run terminates without either a verdict or a structurally triggered escalation.
review_after:  Phase 2
---

# Escalation Protocol

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

The structural triggers that raise an escalation and the attempt bundle each carries. Agent-initiated escalation is permitted as a budget optimization but never load-bearing.

## Enforcement

`schema` — owned by `executable`.

## Falsification condition

An agent run terminates without either a verdict or a structurally triggered escalation.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
