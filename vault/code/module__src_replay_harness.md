---
kind: module
id: "module:src.replay.harness"
title: "The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/replay/harness.py:1"
extractor: "code"
aliases:
  - "The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on."
  - "src.replay.harness"
generated: true
---

# The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/replay/harness.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/replay/harness.py |
| `tree` | src |

## Binds

- [[module__src_replay|src.replay]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.

Domain-neutral throughout.
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.

Domain-neutral throughout.
- [[adr__ADR-0037|`arity` Semantics in Replay Harness]] **enforced_by** → this — # (per ADR-0037 / ACS-1 MetricValue docstring). len(series) is the actual
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — """The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.

Domain-neutral throughout.
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — # D57 at the product boundary. A metric over zero tracks returns something, and
