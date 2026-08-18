---
kind: adr
id: "adr:ADR-0007"
title: "Executor-premise assertions may pass vacuously, and that is a third outcome"
status: "accepted"
shape: "heading"
date: "TBD"
source: "docs/tier1/adr-log.md:780"
extractor: "adrs"
aliases:
  - "ADR-0007"
  - "Executor-premise assertions may pass vacuously, and that is a third outcome"
generated: true
---

# Executor-premise assertions may pass vacuously, and that is a third outcome

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:780`

## Statement

**Date:** TBD · **Status:** Accepted · **Supersedes:** none

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]] — """Three outcomes for a containment assertion, and the third is the dangerous one.

`passed` and `failed` are obvious. *
- **enforced_by** → [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]] — """ADR-0007: an assertion may be executed, passed, and vacuous.

    Not representable in the three-valued outcome, so i
- **enforced_by** → [[module__policy_oracle-denylist_json|policy/oracle-denylist.json]] — "vacuity ADR-0007 named."
