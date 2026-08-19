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

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — # Pinned here only so that a future reader who finds this name in D38 can see it was checked
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — "D38 names OpenHands/OpenHands. At 1916c904 that repository is 'Agent Canvas', "
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """ADR-0018. D38 names the repository that is now Agent Canvas, which is not the executor."""
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """D38 names this repository. At its HEAD it is Agent Canvas and holds no executor."""
