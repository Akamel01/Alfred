---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A prompt reaches an agent without a recorded version.
review_after:  Phase 2
---

# Instruction and Prompt Standard

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

Prompts are versioned, tested artifacts carrying their own identity in the fingerprint. An unversioned prompt cannot support an autonomy grant.

## Enforcement

`schema` — owned by `executable`.

## Falsification condition

A prompt reaches an agent without a recorded version.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
