---
kind: decision
id: "decision:D12"
title: "Network deny-by-default with allowlist"
shape: "table-row"
number: "12"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:56"
extractor: "decisions"
aliases:
  - "D12"
  - "Network deny-by-default with allowlist"
generated: true
---

# Network deny-by-default with allowlist

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:56`

## Statement

**Network deny-by-default with allowlist** in the sandbox.

## Fields

**rationale**

> Everything the agent reads (issue text, dependency READMEs, error messages, web content) is attacker-reachable and enters its context. Egress control caps damage even when injection succeeds.
