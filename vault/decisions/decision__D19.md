---
kind: decision
id: "decision:D19"
title: "Autonomy grants are keyed to a fingerprint"
shape: "table-row"
number: "19"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:63"
extractor: "decisions"
aliases:
  - "Autonomy grants are keyed to a fingerprint"
  - "D19"
generated: true
---

# Autonomy grants are keyed to a fingerprint

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:63`

## Statement

**Autonomy grants are keyed to a fingerprint** — `(capability, model_version, prompt_version, tool_version, context_strategy_version)`. Any change suspends the grant until re-measured, tiered: smoke subset for prompt/context changes, full golden set for model or tool changes.

## Fields

**rationale**

> Every measurement describes a specific system. Model deprecation is scheduled by the provider, not by you — without standing re-qualification, every grant eventually rests on a model that can no longer be run. Fingerprint tracking must therefore exist from Phase 2, not Phase 4.

## Enforced by (code)

- **enforced_by** → [[module__bench_bench_infer|Phase -1 local-model benchmark.]] — """Phase -1 local-model benchmark.

Measures the three things that decide Alfred's inference lane:

  1. prefill through
- **enforced_by** → [[module__bench_bench_infer|Phase -1 local-model benchmark.]] — """D19/D40 fields obtainable without loading the weights ourselves."""
- **enforced_by** → [[module__bench_bench_infer|Phase -1 local-model benchmark.]] — # into a fingerprint that autonomy grants are keyed on (D19/D40).
- **enforced_by** → [[module__harness_containment_denylist|Load the oracle denylist and give it a digest the fingerprint can carry.]] — """Load the oracle denylist and give it a digest the fingerprint can carry.

The denylist is versioned protected policy 
- **enforced_by** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]] — # D19: what tiered requalification reads to decide which component moved.
- **enforced_by** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]] — "D19"
- **enforced_by** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]] — # D19.
- **enforced_by** → [[module__harness_fingerprint_test_record|The run fingerprint record, and the control that the hash covers every field.]] — """A record field with no column is a field the register cannot answer *what changed* on.

    D19's tiered requalificat
- **enforced_by** → [[module__harness_lane_lane_fingerprint|Fail-closed fingerprint assertion for the inference lane (D19/D40).]] — """Fail-closed fingerprint assertion for the inference lane (D19/D40).

The serving stack auto-unloads an idle model and
- **enforced_by** → [[module__migrations_harness_control_versions_0001_control_base|control: work items, fingerprints, protected paths, thresholds.]] — # changed*. D19's tiered requalification is a decision about which component moved,
- **enforced_by** → [[module__migrations_harness_control_versions_0001_control_base|control: work items, fingerprints, protected paths, thresholds.]] — # D19.
- **enforced_by** → [[module__migrations_harness_control_versions_0002_fingerprint_run_fields|control: the run-fingerprint fields the register had no column for.]] — """control: the run-fingerprint fields the register had no column for.

Revision ID: 0002_fingerprint_run_fields
Revises
- **enforced_by** → [[module__scripts_capture_run_fingerprint|Factory-owned script that collects all RunFingerprint fields from live sources,]] — # D19
- **enforced_by** → [[module__scripts_lint_model_routing|MR001-MR005: model routing policy conformance, checked before any spawn.]] — """MR001-MR005: model routing policy conformance, checked before any spawn.

**Why a static lint can enforce this at all

## Stated in prose — unverified

- [[amendment__A6|Extend the decision 19 fingerprint]] **amends** → this — D19 named in A6
