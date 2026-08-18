---
kind: decision
id: "decision:D44"
title: "The evidence store IS the memory; typed views + gated promotion. No extraction pipeline"
shape: "bold-paragraph"
number: "44"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:443"
extractor: "decisions"
aliases:
  - "D44"
  - "The evidence store IS the memory; typed views + gated promotion. No extraction pipeline"
generated: true
---

# The evidence store IS the memory; typed views + gated promotion. No extraction pipeline

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:443`

## Statement

**Decision 44 — The evidence store IS the memory; typed views + gated promotion. No extraction pipeline.** Memory = SQL/typed views over the append-only evidence store (failure taxonomy by metric class, per-capability merge history, prior artifacts by content hash). Anything worth injecting into future agent context graduates through the D32 register — human-reviewed, versioned, evidence-based, expiring — and its version joins the D19 fingerprint. In-task retrieval stays agentic (grep/read, D26-recorded). Rationale: an LLM-extraction memory layer (Mem0/Letta/Zep class) is (a) an unfingerprinta
