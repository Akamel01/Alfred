---
kind: adr
id: "adr:ADR-0068"
title: "The harness lint debt window gets a ceiling, and growth past it fails the gate"
status: "accepted"
shape: "heading"
date: "2026-10-18"
source: "docs/tier1/adr-log.md:7005"
extractor: "adrs"
aliases:
  - "ADR-0068"
  - "The harness lint debt window gets a ceiling, and growth past it fails the gate"
generated: true
---

# The harness lint debt window gets a ceiling, and growth past it fails the gate

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:7005`

## Statement

**Date:** 2026-10-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** `scripts/lint_harness_gate.py` (check C gains `DEBT_CEILING` and its comparison; the floor stays 0, the detection check and the vacuity guard are unchanged) · **See also:** ADR-0029 (which recorded the floor and held the scope call for OBSERVER-1), ADR-0007 (the vacuity class), #87 (the measured growth this answers) · **D28 waiver:** no — `scripts/` is code and the ADR log is `frozen` with `enforcement: none` and append-only by construction; neither is the frozen `ci-gate` shape #78 ruled on (ADR-0066's declaration form; ADR-0064 is the contrast where a frozen document forced a yes)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0029|The tree that verifies every other tree is verified by nothing]]

## Enforced by (code)

- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — # ADR-0068.
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — # naming ADR-0068.
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — "ADR-0068"
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — "C ceiling did not fire alone, naming ADR-0068, one file above the ceiling: "
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — "recorded value, and fires alone naming ADR-0068 one file above it; D reports the "
