---
kind: decision
id: "decision:D34"
title: "Thresholds are declared, cited, versioned configuration inputs"
shape: "table-row"
number: "34"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:78"
extractor: "decisions"
aliases:
  - "D34"
  - "Thresholds are declared, cited, versioned configuration inputs"
generated: true
---

# Thresholds are declared, cited, versioned configuration inputs

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:78`

## Statement

**Thresholds are declared, cited, versioned configuration inputs** with explicit provenance — never agent-authored, never presented as facts.

## Fields

**rationale**

> Threshold *selection* is a contested judgment with no standard; only threshold *application* is checkable. Westhofen et al. exists precisely because selection is unresolved. Treating thresholds as cited configuration preserves schedulability under decision 4 and converts a contested parameter into ground truth the agent did not author.

## Enforced by (code)

- **enforced_by** → [[module__migrations_harness_control_versions_0001_control_base|control: work items, fingerprints, protected paths, thresholds.]] — # D34: thresholds are declared, cited, versioned configuration inputs — never
