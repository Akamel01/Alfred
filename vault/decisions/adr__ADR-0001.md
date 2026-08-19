---
kind: adr
id: "adr:ADR-0001"
title: "Representation of undefined and infinite metric values"
status: "accepted"
shape: "heading"
date: "2026-08-12"
source: "docs/tier1/adr-log.md:20"
extractor: "adrs"
aliases:
  - "ADR-0001"
  - "Representation of undefined and infinite metric values"
generated: true
---

# Representation of undefined and infinite metric values

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:20`

## Statement

**Date:** 2026-08-12 · **Status:** Accepted · **Supersedes:** none · **Amended by:** ADR-0002 (encoding clause) · **See also:** ADR-0006 (the tagged-union pattern gains a third use, for upstream toolchain provenance)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amended_by** → [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]]
- **see_also** → [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]]
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **amends** → this
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **see_also** → this
- [[adr__ADR-0016|`StampedResult` takes its schema version from the stamp it contains]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]] — """ACS-1 float grammar: normalized scientific, shortest round-tripping digits.

        sign? digit "." digit+ "e" "-"? 
- **enforced_by** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]] — # ---- the ADR-0001 tagged metric value, which is why any of this exists
- **enforced_by** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]] — "the ADR-0001 tagged form, which is what actually gets hashed"
- **enforced_by** → [[module__harness_selftest_test_replay|Byte-identical deterministic replay, and the control that stops it being trivial.]] — """ADR-0001: degeneracies are values, contract violations are exceptions.

    A single-track scenario has no counterpar
- **enforced_by** → [[module__migrations_product_versions_0001_product_base|product: scenarios, trajectories, metric results, result stamps.]] — # ADR-0001's tagged union, stored as its three arms rather than as one float.
- **enforced_by** → [[module__migrations_product_versions_0001_product_base|product: scenarios, trajectories, metric results, result stamps.]] — # ADR-0001 exists to prevent.
- **enforced_by** → [[module__scripts_gen_reading_map|Generate docs/READING-MAP.md — what to read, when, and what it binds.]] — "ADR-0001 to 0008 constrain every metric signature, every hashed record, and the operator surface"
- **enforced_by** → [[module__src_domain_arrays|Array-valued fields for Pydantic boundary models.]] — """Array-valued fields for Pydantic boundary models.

The domain is vectorized on purpose. ADR-0001 measured per-timeste
- **enforced_by** → [[module__src_domain_trajectory|Trajectory schemas — the load-bearing abstraction everything downstream reads.]] — """Trajectory schemas — the load-bearing abstraction everything downstream reads.

One `AgentTrack` per observed road us
- **enforced_by** → [[module__src_metrics___init__|Metric representation types (ADR-0001, ADR-0002).]] — """Metric representation types (ADR-0001, ADR-0002).

`MetricSeries` inside computation, `MetricValue` on every boundary
- **enforced_by** → [[module__src_metrics_port|The `Metric` port — what a measure is, and the one shape it may return in.]] — """The `Metric` port — what a measure is, and the one shape it may return in.

One of the three S5 ports. Factory: this 
- **enforced_by** → [[module__src_metrics_reasons|The global reason codebook (ADR-0001 consequences, ADR-0002).]] — """The global reason codebook (ADR-0001 consequences, ADR-0002).

One enum for the whole system. Codes enumerate *kinds 
- **enforced_by** → [[module__src_metrics_reasons|The global reason codebook (ADR-0001 consequences, ADR-0002).]] — """Decode a stored integer. Unrecognized codes become `UNKNOWN_CODE`, never `DEFINED`.

    This is the single most impo
- **enforced_by** → [[module__src_metrics_series|`MetricSeries` — the internal, vectorized form (ADR-0001).]] — """`MetricSeries` — the internal, vectorized form (ADR-0001).

`values: float64[]` alongside `reasons: uint8[]` over a s
- **enforced_by** → [[module__src_metrics_series|`MetricSeries` — the internal, vectorized form (ADR-0001).]] — """Convert one sample to its boundary form.

        The single declared conversion point of ADR-0001. Undefined samples
- **enforced_by** → [[module__src_metrics_value|`MetricValue` — the tagged form every metric result takes on every boundary (ADR-0001).]] — """`MetricValue` — the tagged form every metric result takes on every boundary (ADR-0001).

```json
{"kind": "defined", 
- **enforced_by** → [[module__src_provenance_stamp|Result stamping — the shape in which a number leaves the system.]] — # `value` uses the ADR-0001 tagged form because ACS-1 refuses a raw
- **enforced_by** → [[module__src_replay_harness|The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.]] — """The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.

Domain-neutral throughout.
- **enforced_by** → [[module__tests_test_metric_series|`MetricSeries`, the internal form, and the single conversion point (ADR-0001).]] — """`MetricSeries`, the internal form, and the single conversion point (ADR-0001)."""
- **enforced_by** → [[module__tests_test_metric_value|`MetricValue`, the boundary form (ADR-0001).]] — """`MetricValue`, the boundary form (ADR-0001).

The measurements that decided ADR-0001 are re-asserted here rather than
- **enforced_by** → [[module__tests_test_metric_value|`MetricValue`, the boundary form (ADR-0001).]] — """ADR-0001's decisive measurement, re-run.

    If this ever stops holding, the ADR's reasoning changes and someone sho
- **enforced_by** → [[module__tests_test_s5_ports|The three S5 ports as types: `TrajectorySource`, `Metric`, `ReplayHarness`.]] — """ADR-0001. A bare float has one channel for three meanings, and two of them then
    travel as `NaN` or `None` and cha
