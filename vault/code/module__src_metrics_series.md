---
kind: module
id: "module:src.metrics.series"
title: "`MetricSeries` — the internal, vectorized form (ADR-0001)."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/metrics/series.py:1"
extractor: "code"
aliases:
  - "`MetricSeries` — the internal, vectorized form (ADR-0001)."
  - "src.metrics.series"
generated: true
---

# `MetricSeries` — the internal, vectorized form (ADR-0001).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/metrics/series.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/metrics/series.py |
| `tree` | src |

## Binds

- [[module__src_metrics|src.metrics]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """`MetricSeries` — the internal, vectorized form (ADR-0001).

`values: float64[]` alongside `reasons: uint8[]` over a s
- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """Convert one sample to its boundary form.

        The single declared conversion point of ADR-0001. Undefined samples
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """A metric evaluated over a timebase, with per-sample definedness.

    Not a Pydantic model: this type never crosses a
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — "reasons must be uint8 (ADR-0002)"
