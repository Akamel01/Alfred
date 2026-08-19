---
kind: module
id: "module:harness.stamp.verdict_map"
title: "ADR-0006's verdict table, as data rather than as prose."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/stamp/verdict_map.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "ADR-0006's verdict table, as data rather than as prose."
  - "harness.stamp.verdict_map"
generated: true
---

# ADR-0006's verdict table, as data rather than as prose.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/stamp/verdict_map.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/stamp/verdict_map.py |
| `tree` | harness |

## Binds

- [[module__harness_stamp|harness.stamp]] **contains** → this
- [[module__harness_stamp_test_verdict_map|The verdict table's own tests, including its vacuity control.]] **imports** → this
- [[module__tests_test_stamp_verify|The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """ADR-0006's verdict table, as data rather than as prose.

The table maps what a stamp verifier concluded onto Alfred's
- [[decision__D16|Verdict fields are owned by deterministic nodes]] **enforced_by** → this — """ADR-0006's verdict table, as data rather than as prose.

The table maps what a stamp verifier concluded onto Alfred's
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — """ADR-0006's verdict table, as data rather than as prose.

The table maps what a stamp verifier concluded onto Alfred's
