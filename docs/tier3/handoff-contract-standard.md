---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A handoff carries prose the successor relies on without reading the underlying artifact.
review_after:  Phase 3
---

# Handoff Contract Standard

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

What passes between nodes: content-addressed evidence refs, never agent-authored summaries. A summary is lossy compression by an interested party.

## Enforcement

`schema` — owned by `executable`.

## Falsification condition

A handoff carries prose the successor relies on without reading the underlying artifact.

## Promotion

Promote this stub to full content when Phase Phase 3 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
