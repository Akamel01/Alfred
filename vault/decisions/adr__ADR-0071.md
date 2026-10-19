---
kind: adr
id: "adr:ADR-0071"
title: "OBSERVER-1's first slice collects `harness/patch/` and `harness/selftest/` under ruff, and both bounds move once"
status: "accepted"
shape: "heading"
date: "2026-10-19"
source: "docs/tier1/adr-log.md:7121"
extractor: "adrs"
aliases:
  - "ADR-0071"
  - "OBSERVER-1's first slice collects `harness/patch/` and `harness/selftest/` under ruff, and"
generated: true
---

# OBSERVER-1's first slice collects `harness/patch/` and `harness/selftest/` under ruff, and both bounds move once

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:7121`

## Statement

**Date:** 2026-10-19 · **Status:** Accepted · **Supersedes:** none · **Amends:** `pyproject.toml` (`[tool.ruff].include` and the two literal `S101` per-file patterns), `scripts/lint_harness_gate.py` (`COVERAGE_FLOOR` 0 to 12, `DEBT_CEILING` 92 to 80, and the prose that recorded the zero), `.github/workflows/gates.yml` (the coverage-step comment that still described the zero, no behaviour change) · **See also:** ADR-0029 (the measurement this slice starts to pay down), ADR-0068 (the ceiling and the one-edit rule), ADR-0007 (the vacuity class), #97 · **D28 waiver:** no — `pyproject.toml`, `scripts/` and the `.github/` workflow comment are protected code, and the ADR log is append-only by construction; the workflow carries no status header, so no frozen `ci-gate` register document is amended

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0029|The tree that verifies every other tree is verified by nothing]]
- **see_also** → [[adr__ADR-0068|The harness lint debt window gets a ceiling, and growth past it fails the gate]]

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — The coverage floor is 12 today and the run prints "12 of 92": the ADR-0071 first
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — # `harness/selftest/` (7), the OBSERVER-1 first slice (ADR-0071). It was 0 on
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — # `oc/97` (2026-10-19): 92 on disk minus the 12 the first slice collects (ADR-0071). It was
