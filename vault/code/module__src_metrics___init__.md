---
kind: module
id: "module:src.metrics.__init__"
title: "Metric representation types (ADR-0001, ADR-0002)."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/metrics/__init__.py:1"
extractor: "code"
aliases:
  - "Metric representation types (ADR-0001, ADR-0002)."
  - "src.metrics.__init__"
generated: true
---

# Metric representation types (ADR-0001, ADR-0002).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/metrics/__init__.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/metrics/__init__.py |
| `tree` | src |

## Binds

- [[module__src_metrics|src.metrics]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """Metric representation types (ADR-0001, ADR-0002).

`MetricSeries` inside computation, `MetricValue` on every boundary
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """Metric representation types (ADR-0001, ADR-0002).

`MetricSeries` inside computation, `MetricValue` on every boundary
