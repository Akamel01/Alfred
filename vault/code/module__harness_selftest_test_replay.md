---
kind: module
id: "module:harness.selftest.test_replay"
title: "Byte-identical deterministic replay, and the control that stops it being trivial."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/selftest/test_replay.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Byte-identical deterministic replay, and the control that stops it being trivial."
  - "harness.selftest.test_replay"
generated: true
---

# Byte-identical deterministic replay, and the control that stops it being trivial.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/selftest/test_replay.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/selftest/test_replay.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_selftest_replay_fixtures|A synthetic source and a synthetic metric, so the replay harness can be exercised.]]
- [[module__harness_selftest|harness.selftest]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """ADR-0001: degeneracies are values, contract violations are exceptions.

    A single-track scenario has no counterpar
- [[adr__ADR-0022|Phase 0's exit, narrowed along the ownership seam, with the residue dated]] **enforced_by** → this — """Byte-identical deterministic replay, and the control that stops it being trivial.

**P0-5 of the narrowed Phase 0 exi
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Byte-identical deterministic replay, and the control that stops it being trivial.

**P0-5 of the narrowed Phase 0 exi
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """D57 at the product boundary.

    A metric over zero tracks still returns something, and that something would be stam
