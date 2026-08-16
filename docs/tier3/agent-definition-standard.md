---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  An agent is dispatched whose definition names a job title rather than a capability.
review_after:  Phase 2
---

# Agent Definition Standard

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

The schema every agent definition must satisfy: input contract, output contract, tools, permissions, criteria, escalation. Roles are not valid agent definitions.

## Enforcement

`schema` — owned by `executable`.

## Falsification condition

An agent is dispatched whose definition names a job title rather than a capability.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
