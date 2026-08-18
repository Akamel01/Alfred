---
kind: module
id: "module:src.metrics"
title: "src.metrics"
shape: "package"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/metrics:1"
extractor: "code"
aliases:
  - "src.metrics"
generated: true
---

# src.metrics

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/metrics:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | src |

## Binds

- **contains** → [[module__src_metrics___init__|Metric representation types (ADR-0001, ADR-0002).]]
- **contains** → [[module__src_metrics_reasons|The global reason codebook (ADR-0001 consequences, ADR-0002).]]
- **contains** → [[module__src_metrics_series|`MetricSeries` — the internal, vectorized form (ADR-0001).]]
- **contains** → [[module__src_metrics_value|`MetricValue` — the tagged form every metric result takes on every boundary (ADR-0001).]]
