---
kind: module
id: "module:harness.selftest.replay_fixtures"
title: "A synthetic source and a synthetic metric, so the replay harness can be exercised."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/selftest/replay_fixtures.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "A synthetic source and a synthetic metric, so the replay harness can be exercised."
  - "harness.selftest.replay_fixtures"
generated: true
---

# A synthetic source and a synthetic metric, so the replay harness can be exercised.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/selftest/replay_fixtures.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/selftest/replay_fixtures.py |
| `tree` | harness |

## Binds

- [[module__harness_selftest|harness.selftest]] **contains** → this
- [[module__harness_selftest_test_replay|Byte-identical deterministic replay, and the control that stops it being trivial.]] **imports** → this
