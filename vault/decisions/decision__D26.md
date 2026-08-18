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

| Field | Value |
|---|---|
| `rationale` | Agentic retrieval is why agents work, but it is nondeterministic — which appears to break decision 19's fingerprint. Recording resolves it: reproducibility comes from the evidence store, not from constraining retrieval. Runs replay against the exact file set they saw. Side benefits: context becomes measurable (which reads correlate with success), and the read log is a *partial* forensic trail afte |
