---
kind: decision
id: "decision:D38"
title: "Decision 9's named harness (Claude Agent SDK) demoted to provisional"
shape: "table-row"
number: "38"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:83"
extractor: "decisions"
aliases:
  - "D38"
  - "Decision 9's named harness (Claude Agent SDK) demoted to provisional"
generated: true
---

# Decision 9's named harness (Claude Agent SDK) demoted to provisional

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:83`

## Statement

**Decision 9's named harness (Claude Agent SDK) demoted to provisional.** Buy-the-loop stands; the candidate is reopened. Selection criteria for the worker harness: first-class local/OpenAI-compatible endpoint support, tool-calling format matching open-weights training, KV-cache-friendly context assembly, and ability to satisfy D5/D16/D26. Candidates under evaluation: devswarm, openclaw, opencode, plus SDK-via-proxy as a baseline.

## Fields

**rationale**

> The SDK's loop is Anthropic-shaped: tool-calling formats, caching behavior, internal assumptions. Terminal-Bench showed harness identity moves scores as much as the spread between leading submissions — driving gpt-oss-120b through a Claude-tuned harness is a silent capability tax of unknown size. The `Worker` interface exists precisely to make this swap cheap.
