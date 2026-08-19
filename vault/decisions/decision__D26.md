---
kind: decision
id: "decision:D26"
title: "Context = deterministic seed + free agent search + full read-recording"
shape: "table-row"
number: "26"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:70"
extractor: "decisions"
aliases:
  - "Context = deterministic seed + free agent search + full read-recording"
  - "D26"
generated: true
---

# Context = deterministic seed + free agent search + full read-recording

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:70`

## Statement

**Context = deterministic seed + free agent search + full read-recording.** Harness seeds (task, criterion, conventions, protected paths, prior artifacts); agent searches freely in the sandbox; every file read and search issued is recorded to the evidence store as the run's observed context.

## Fields

**rationale**

> Agentic retrieval is why agents work, but it is nondeterministic — which appears to break decision 19's fingerprint. Recording resolves it: reproducibility comes from the evidence store, not from constraining retrieval. Runs replay against the exact file set they saw. Side benefits: context becomes measurable (which reads correlate with success), and the read log is a *partial* forensic trail after an injection incident — **downgraded 2026-08-15, and the downgrade is the honest form of the original claim.** Completeness is demonstrated only against the executor's own durable event count (containment assertion C1), which proves no event was lost between the executor and the store and **cannot prove an event was emitted for everything the agent did**; the log's granularity is the action, not the file read, so files opened inside a shell command are recorded as one command. The log is therefore **positive evidence** — content it records did enter context, which suffices to identify a payload that arrived through a recorded read and to compute retrieval miss rate — and **not negative evidence**: the absence of a read from the log is not evidence the read did not happen. What bounds the set of bytes that could have been read is the asserted mount set (C9, C12), not the log, and that bound is the stronger forensic object in the direction an incident actually asks about. An independent observation channel — filesystem-level read auditing inside the container — was considered and **rejected on containment cost rather than effort**: the kernel audit subsystem is not namespaced and fanotify/eBPF attachment requires capabilities the sandbox must not hold, so completing the trail would mean enlarging the privilege set of the thing the trail exists to bound. Revisit if runs ever execute on a Linux host Alfred owns, where a host-side watcher sits outside the container's capability set. Read-recording must be in the `Worker` port from Phase 1 regardless — the downgrade is to what the log proves, never to whether it is kept.

## Enforced by (code)

- **enforced_by** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]] — """D26, and it is positive evidence only.

    Derived by the adaptor from the executor's action/observation stream, nev
