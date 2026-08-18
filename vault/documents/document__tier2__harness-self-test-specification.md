---
kind: document
id: "document:tier2/harness-self-test-specification"
title: "Harness Self-Test Specification"
status: "provisional"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "2"
written: "full"
review_after: "Phase 1"
source: "docs/tier2/harness-self-test-specification.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier2]
aliases:
  - "Harness Self-Test Specification"
  - "tier2/harness-self-test-specification"
generated: true
---

# Harness Self-Test Specification

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/harness-self-test-specification.md:1`

## Falsifies if

> A suite specified here passes while the control it guards is disabled; or a seeded defect at a delta just outside a declared tolerance is not red; or the null-agent floor scores above zero; or an injected fault produces `pass`.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier2/harness-self-test-specification.md |
| `tier_name` | Build protocol |

**evidence**

> Every headline number in this project has been wrong on first read, four for four, each time because the instrument was trusted before it was checked. The ACS-1 mutation control is the worked precedent: 47 mutants, worst margin 10 checks, with a negative control that reports UNDETECTED on a no-op mutant and aborts on a mutation that fails to apply.

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
