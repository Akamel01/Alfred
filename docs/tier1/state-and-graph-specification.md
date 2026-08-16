---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A state field is written by more than one node without a declared reducer.
review_after:  Phase 3
---

# State and Graph Specification

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

The typed state channels, their owning writers, and the reducers required for fan-in. Executable as the LangGraph state schema, not prose.

## Enforcement

`schema` — owned by `executable`.

## Falsification condition

A state field is written by more than one node without a declared reducer.

## Promotion

Promote this stub to full content when Phase Phase 3 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
