---
kind: module
id: "module:src.metrics.port"
title: "The `Metric` port — what a measure is, and the one shape it may return in."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/metrics/port.py:1"
extractor: "code"
aliases:
  - "The `Metric` port — what a measure is, and the one shape it may return in."
  - "src.metrics.port"
generated: true
---

# The `Metric` port — what a measure is, and the one shape it may return in.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/metrics/port.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/metrics/port.py |
| `tree` | src |

## Binds

- [[module__src_metrics|src.metrics]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """The `Metric` port — what a measure is, and the one shape it may return in.

One of the three S5 ports. Factory: this 
- [[adr__ADR-0037|`arity` Semantics in Replay Harness]] **enforced_by** → this — """The number of independent observations a metric aggregates.

        This is the declared arity, not inferred from th
