---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  A record exists whose cause cannot be traced.
review_after:  Phase 2
---

# Observability Standard

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

Structured logging with trace and span IDs from the first commit, OpenTelemetry semantics, and causality recorded on every record. Correlation cannot be reconstructed retroactively.

## Enforcement

`ci-gate` — owned by `executable`.

## Falsification condition

A record exists whose cause cannot be traced.

## Promotion

Promote this stub to full content when Phase Phase 2 can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
