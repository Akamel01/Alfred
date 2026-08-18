---
kind: adr
id: "adr:ADR-0002"
title: "Reason-code width, and what the integer is allowed to be"
status: "accepted"
shape: "heading"
date: "2026-08-12"
source: "docs/tier1/adr-log.md:145"
extractor: "adrs"
aliases:
  - "ADR-0002"
  - "Reason-code width, and what the integer is allowed to be"
generated: true
---

# Reason-code width, and what the integer is allowed to be

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:145`

## Statement

**Date:** 2026-08-12 · **Status:** Accepted · **Amends:** ADR-0001 (encoding clause only)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0001|Representation of undefined and infinite metric values]]
- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **amended_by** → this

## Enforced by (code)

- **enforced_by** → [[module__migrations_product_versions_0001_product_base|product: scenarios, trajectories, metric results, result stamps.]] — # The reason *name* is what crosses a boundary and what gets hashed (ADR-0002);
- **enforced_by** → [[module__src_metrics___init__|Metric representation types (ADR-0001, ADR-0002).]] — """Metric representation types (ADR-0001, ADR-0002).

`MetricSeries` inside computation, `MetricValue` on every boundary
- **enforced_by** → [[module__src_metrics_reasons|The global reason codebook (ADR-0001 consequences, ADR-0002).]] — """The global reason codebook (ADR-0001 consequences, ADR-0002).

One enum for the whole system. Codes enumerate *kinds 
- **enforced_by** → [[module__src_metrics_reasons|The global reason codebook (ADR-0001 consequences, ADR-0002).]] — # The build fails here rather than at 254 (ADR-0002). A ceiling discovered at
- **enforced_by** → [[module__src_metrics_reasons|The global reason codebook (ADR-0001 consequences, ADR-0002).]] — """The codebook violates an ADR-0002 invariant. Fails the build, not a run."""
- **enforced_by** → [[module__src_metrics_reasons|The global reason codebook (ADR-0001 consequences, ADR-0002).]] — """Assert every ADR-0002 invariant. Raises `CodebookError` on the first breach.

    Both mappings are arguments so the 
- **enforced_by** → [[module__src_metrics_series|`MetricSeries` — the internal, vectorized form (ADR-0001).]] — """A metric evaluated over a timebase, with per-sample definedness.

    Not a Pydantic model: this type never crosses a
- **enforced_by** → [[module__src_metrics_series|`MetricSeries` — the internal, vectorized form (ADR-0001).]] — "reasons must be uint8 (ADR-0002)"
- **enforced_by** → [[module__tests_properties_test_metric_properties|Property tests over the representation types.]] — """The invariant ADR-0002 exists for: no integer decodes to DEFINED unless it is 0."""
- **enforced_by** → [[module__tests_test_reasons|The reason codebook invariants (ADR-0002).]] — """The reason codebook invariants (ADR-0002).

Each test here corresponds to a clause the ADR says CI asserts. Every one
- **enforced_by** → [[module__tests_test_reasons|The reason codebook invariants (ADR-0002).]] — # The point of ADR-0002: the failure lands at 80%, well before 254, so the
