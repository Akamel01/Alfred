---
kind: adr
id: "adr:ADR-0029"
title: "The tree that verifies every other tree is verified by nothing"
status: "accepted"
shape: "heading"
date: "2026-08-19"
source: "docs/tier1/adr-log.md:2910"
extractor: "adrs"
aliases:
  - "ADR-0029"
  - "The tree that verifies every other tree is verified by nothing"
generated: true
---

# The tree that verifies every other tree is verified by nothing

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:2910`

## Statement

**Date:** 2026-08-19 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0007 (the vacuity class this is an instance of, found in the tooling rather than in an assertion), ADR-0027 and ADR-0028 (the D20 review this ADR incurs)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0027|An agent edited the inspector, and this record was drafted by the same agent]]
- **see_also** → [[adr__ADR-0028|The review ADR-0027 said was owed has been done]]

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — `not-yet-injected` rows above: raising it is OBSERVER-1 under ADR-0029, and until it
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — # ADR-0029 pending OBSERVER-1: closing the gap needs 120 hand edits, 55 suppressions and 17
