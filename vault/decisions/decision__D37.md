---
kind: decision
id: "decision:D37"
title: "Single execution lane, 24/7 queue"
shape: "table-row"
number: "37"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:81"
extractor: "decisions"
aliases:
  - "D37"
  - "Single execution lane, 24/7 queue"
generated: true
---

# Single execution lane, 24/7 queue

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:81`

## Statement

**Single execution lane, 24/7 queue.** One agent at a time; the dispatcher feeds one inference lane from the Postgres queue around the clock. Phase 3's parallel-sandbox plan is amended to parallel *preparation* (checkout, seeding, criterion setup) with serialized inference. Horizontal scaling later = second machine, another lane on the same queue.

## Fields

**rationale**

> Honest answer to the memory arithmetic: one ~60 GB resident model is one worker. Throughput comes from uptime, not parallelism — tasks/day = f(prefill speed, turns, retries). The Postgres `SKIP LOCKED` queue is already multi-host-aware, so a second Mac Studio is a capital decision, not an architectural one.
