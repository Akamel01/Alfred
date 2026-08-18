---
kind: module
id: "module:src.metrics.value"
title: "`MetricValue` — the tagged form every metric result takes on every boundary (ADR-0001)."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/metrics/value.py:1"
extractor: "code"
aliases:
  - "`MetricValue` — the tagged form every metric result takes on every boundary (ADR-0001)."
  - "src.metrics.value"
generated: true
---

# `MetricValue` — the tagged form every metric result takes on every boundary (ADR-0001).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/metrics/value.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/metrics/value.py |
| `tree` | src |

## Binds

- [[module__src_metrics|src.metrics]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """`MetricValue` — the tagged form every metric result takes on every boundary (ADR-0001).

```json
{"kind": "defined", 
