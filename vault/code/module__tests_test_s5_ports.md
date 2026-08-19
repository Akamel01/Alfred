---
kind: module
id: "module:tests.test_s5_ports"
title: "The three S5 ports as types: `TrajectorySource`, `Metric`, `ReplayHarness`."
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/test_s5_ports.py:1"
extractor: "code"
aliases:
  - "The three S5 ports as types: `TrajectorySource`, `Metric`, `ReplayHarness`."
  - "tests.test_s5_ports"
generated: true
---

# The three S5 ports as types: `TrajectorySource`, `Metric`, `ReplayHarness`.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/test_s5_ports.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/test_s5_ports.py |
| `tree` | tests |

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """ADR-0001. A bare float has one channel for three meanings, and two of them then
    travel as `NaN` or `None` and cha
