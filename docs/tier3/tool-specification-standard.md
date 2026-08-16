---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A tool's behaviour changes without its description hash changing.
review_after:  Phase 2
---

# Tool Specification Standard

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

The contract every tool declares: signature, side effects, blast radius, idempotency. Tool descriptions are hashed into the fingerprint because descriptions alone can change behaviour.

## Enforcement

`schema` — owned by `executable`.

## Falsification condition

A tool's behaviour changes without its description hash changing.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
