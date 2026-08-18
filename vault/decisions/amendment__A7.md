---
kind: amendment
id: "amendment:A7"
title: "Decision 12 becomes a machine-checkable criterion"
shape: "table-row"
number: "A7"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:181"
extractor: "amendments"
aliases:
  - "A7"
  - "Decision 12 becomes a machine-checkable criterion"
generated: true
---

# Decision 12 becomes a machine-checkable criterion

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:181`

## Statement

**Decision 12 becomes a machine-checkable criterion**, not a policy: egress canary on every sandbox boot attempting a known non-allowlisted connection; run refuses to start unless it fails. Enforce with nftables default-drop + REDIRECT — env-var proxy config is advisory and bypassable.

## Fields

**evidence**

> Anthropic's own eval harness: "A misconfiguration left the machines that Claude accessed as part of the evaluation with live internet access." That is the base rate for "we configured deny-by-default." CamoLeak (CVSS 9.6) exfiltrated through an allowlisted host.
