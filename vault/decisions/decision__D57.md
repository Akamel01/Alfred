---
kind: decision
id: "decision:D57"
title: "The harness self-test suites are two-sided, and each carries a stated vacuity control"
shape: "table-row"
number: "57"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:103"
extractor: "decisions"
aliases:
  - "D57"
  - "The harness self-test suites are two-sided, and each carries a stated vacuity control"
generated: true
---

# The harness self-test suites are two-sided, and each carries a stated vacuity control

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:103`

## Statement

**The harness self-test suites are two-sided, and each carries a stated vacuity control.** A seeded-defect ladder asserts **green** inside the declared tolerance (δ = 0, τ/2, τ·(1−ε)) and **red** outside it (τ·(1+ε), 10τ, O(1)) — because a suite of red-expectations alone is passed by a `CriterionRunner` that fails unconditionally, and the rung just outside tolerance is the only one constraining the tolerance's *calibration*. ε is set from the criterion's **measured** noise floor, never chosen; a τ that cannot resolve ε is a finding about τ. The null-agent floor is `patch is None` with an unchanged tree, asserting **score zero and verdict `fail`, never `indeterminate`** — a do-nothing run belongs in the merge-rate denominator. Fault injection asserts by **disposition**: `indeterminate` for the seven rows disposed so, **no verdict row at all** for the fifteen disposed *run does not start*, and *the next side effect did not occur* for the five disposed *halt/reject*. Every injector carries a witness, and an uninvoked injector fails its own test. Every suite states how it would be shown vacuous, and the disable-all-injectors / always-pass / always-fail controls are committed alongside it.

## Fields

| Field | Value |
|---|---|
| `rationale` | A passing suite and a vacuous suite report the same thing, and this project has paid for that lesson twice: ADR-0004 recorded thin ACS-1 margins (3 checks, then 1) that only a mutation control surfaced, and the arity guard in `harness/lane/` rests on a **single** check today against salvage-disabled's 26. The hazard the two-sidedness answers is structural and previously unnamed: `testing-strategy. |

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]] — """Containment assertions, each paired with the control that stops it reading green.

**How this suite would be shown va
- **enforced_by** → [[module__harness_criterion_test_execute|Three outcomes, and the ways two of them get silently collapsed into one.]] — """Three outcomes, and the ways two of them get silently collapsed into one.

**How this suite would be shown vacuous** 
- **enforced_by** → [[module__harness_criterion_test_materialize|A1, asserted as an architectural claim rather than as a list of blocked filenames.]] — """A1, asserted as an architectural claim rather than as a list of blocked filenames.

**How this suite would be shown v
- **enforced_by** → [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] — """Verdict composition, with the two collapses that would make the number meaningless.

**How this suite would be shown 
- **enforced_by** → [[module__harness_db_test_grants|The grant matrix, asserted two ways: by set equality, and by being refused.]] — """The grant matrix, asserted two ways: by set equality, and by being refused.

**Every denial asserts `SQLSTATE 42501` 
- **enforced_by** → [[module__harness_evidence_test_restore_drill|The restore drill and the independent re-walk, each with the control that matters.]] — """The restore drill and the independent re-walk, each with the control that matters.

**How this suite would be shown v
- **enforced_by** → [[module__harness_evidence_test_store|The append-only chain, asserted from both sides.]] — """The append-only chain, asserted from both sides.

**How this suite would be shown vacuous** (D57). Every positive tes
