---
kind: module
id: "module:scripts.lint_harness_gate"
title: "How much of `harness/` the lint gate actually collects, and whether it can go red."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_harness_gate.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "How much of `harness/` the lint gate actually collects, and whether it can go red."
  - "scripts.lint_harness_gate"
generated: true
---

# How much of `harness/` the lint gate actually collects, and whether it can go red.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_harness_gate.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_harness_gate.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_15|Harness lint coverage]] **runs** → this
- [[gate-step__integrity_16|Harness gate detects planted violations]] **runs** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- [[adr__ADR-0029|The tree that verifies every other tree is verified by nothing]] **enforced_by** → this — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- [[adr__ADR-0068|The harness lint debt window gets a ceiling, and growth past it fails the gate]] **enforced_by** → this — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- [[adr__ADR-0068|The harness lint debt window gets a ceiling, and growth past it fails the gate]] **enforced_by** → this — # ADR-0068.
- [[adr__ADR-0068|The harness lint debt window gets a ceiling, and growth past it fails the gate]] **enforced_by** → this — # naming ADR-0068.
- [[adr__ADR-0068|The harness lint debt window gets a ceiling, and growth past it fails the gate]] **enforced_by** → this — "ADR-0068"
- [[adr__ADR-0068|The harness lint debt window gets a ceiling, and growth past it fails the gate]] **enforced_by** → this — "C ceiling did not fire alone, naming ADR-0068, one file above the ceiling: "
- [[adr__ADR-0068|The harness lint debt window gets a ceiling, and growth past it fails the gate]] **enforced_by** → this — "recorded value, and fires alone naming ADR-0068 one file above it; D reports the "
- [[adr__ADR-0071|OBSERVER-1's first slice collects `harness/patch/` and `harness/selftest/` under ruff, and]] **enforced_by** → this — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- [[adr__ADR-0071|OBSERVER-1's first slice collects `harness/patch/` and `harness/selftest/` under ruff, and]] **enforced_by** → this — # `harness/selftest/` (7), the OBSERVER-1 first slice (ADR-0071). It was 0 on
- [[adr__ADR-0071|OBSERVER-1's first slice collects `harness/patch/` and `harness/selftest/` under ruff, and]] **enforced_by** → this — # `oc/97` (2026-10-19): 92 on disk minus the 12 the first slice collects (ADR-0071). It was
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
