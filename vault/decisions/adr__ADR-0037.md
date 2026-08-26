---
kind: adr
id: "adr:ADR-0037"
title: "`arity` Semantics in Replay Harness"
status: "accepted"
shape: "heading"
date: "2026-08-24"
source: "docs/tier1/adr-log.md:3901"
extractor: "adrs"
aliases:
  - "ADR-0037"
  - "`arity` Semantics in Replay Harness"
generated: true
---

# `arity` Semantics in Replay Harness

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:3901`

## Statement

**Date:** 2026-08-24 · **Status:** Accepted · **Supersedes:** none

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Enforced by (code)

- **enforced_by** → [[module__src_metrics_port|The `Metric` port — what a measure is, and the one shape it may return in.]] — """The number of independent observations a metric aggregates.

        This is the declared arity, not inferred from th
- **enforced_by** → [[module__src_replay_harness|The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.]] — # (per ADR-0037 / ACS-1 MetricValue docstring). len(series) is the actual
