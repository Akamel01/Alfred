---
kind: adr
id: "adr:ADR-0049"
title: "Agent-stated intent is rendered on the live view and nowhere a decision is taken"
status: "accepted"
shape: "heading"
date: "2026-09-03"
source: "docs/tier1/adr-log.md:4642"
extractor: "adrs"
aliases:
  - "ADR-0049"
  - "Agent-stated intent is rendered on the live view and nowhere a decision is taken"
generated: true
---

# Agent-stated intent is rendered on the live view and nowhere a decision is taken

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:4642`

## Statement

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier1/mission-control-specification.md` § *Deliberately hard to reach, and why* — the third bullet · **See also:** ADR-0047 (runtime state owns nothing), `docs/tier7/ticket-52-read-model-decision.md`, `docs/tier3/handoff-contract-standard.md`, D22 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0047|The ownership router gains the factory's facts, and runtime state is never evidence]]
- [[adr__ADR-0050|Mission Control is hosted off-host, and the loopback bind is replaced rather than relaxed]] **see_also** → this
- [[adr__ADR-0051|The live view is pulled forward ahead of its trigger, and the trigger's reasoning is not d]] **see_also** → this
