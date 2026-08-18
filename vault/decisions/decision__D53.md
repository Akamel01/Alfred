---
kind: decision
id: "decision:D53"
title: "Executor containment is fifteen numbered boot assertions, split by placement, and the `Worker` port refuses to dispatch without them"
shape: "table-row"
number: "53"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:95"
extractor: "decisions"
aliases:
  - "D53"
  - "Executor containment is fifteen numbered boot assertions, split by placement, and the `Wor"
generated: true
---

# Executor containment is fifteen numbered boot assertions, split by placement, and the `Worker` port refuses to dispatch without them

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:95`

## Statement

**Executor containment is fifteen numbered boot assertions, split by placement, and the `Worker` port refuses to dispatch without them.** An assertion whose subject is *what the container is* — import path, mount set, environment, listening sockets, loaded configuration — runs **inside** it, because those are properties of the running namespace and are invisible from the image manifest. An assertion whose subject is *the container's account of itself* — image digest, the configuration that was sent, durable event counts, patch content — runs **outside** it. Four hazards are asserted rather than configured: persistence verified by end-of-run event count and not by a flag; every condenser disabled and zero condensation events in the stream; **the executor's own frontend and confirmation mode not exposed, with zero approval-class events in the stream**; and configuration hoisting closed by asserting the loaded configuration hash equals the harness-supplied one with no user- or project-level file at any search path.

## Fields

| Field | Value |
|---|---|
| `rationale` | An operator approving work inside the executor writes that approval into the executor's event stream — **inside the untrusted, disposable execution plane** — creating a second authorization path Alfred's evidence store and hash chain never see, which makes the most privileged actor (T10) the least audited one. Beneath the plumbing is a framing defect: the executor's surface is agent-conversation-c |
