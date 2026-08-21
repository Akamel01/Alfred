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

**rationale**

> A passing suite and a vacuous suite report the same thing, and this project has paid for that lesson twice: ADR-0004 recorded thin ACS-1 margins (3 checks, then 1) that only a mutation control surfaced, and the arity guard in `harness/lane/` rests on a **single** check today against salvage-disabled's 26. The hazard the two-sidedness answers is structural and previously unnamed: `testing-strategy.md` and `failure-semantics.md` both specify the seeded-defect suite entirely in terms of what must go red, and nothing in the register rules out a runner that reds everything. **The floor suite and the ladder are each other's vacuity control** — replace every criterion with `return 0.0` and the floor suite passes while the ladder's green rungs fail — so neither may be specified or owned without the other.

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_image|C4 — the runtime image is the one the fingerprint declares, and it came from local disk.]] — """C4 — the runtime image is the one the fingerprint declares, and it came from local disk.

Runs **outside** the contai
- **enforced_by** → [[module__harness_containment_reassert|C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.]] — """C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.

C7, C9, C12, C13, C16 and C17 are asserte
- **enforced_by** → [[module__harness_containment_reassert|C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.]] — """Re-asserted ids present in both reports that **neither side gave any observation for**.

    D57, aimed at this compa
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — """Every name a `CONFIG_KEY` hole holds — the reference set, derived, never typed out.

    Derived from the register so
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — """The ingress surface and the launch posture — the half of ADR-0019 nothing covered.

    ADR-0019 recorded four unhard
- **enforced_by** → [[module__harness_containment_source_hashes|The register C15 clause 3 compares against, and the reason it had nothing to compare.]] — # D57 at the loader rather than at the caller. A register that parsed to nothing is a
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """C1–C15 beyond the two probes, each paired with the control that stops it reading green.

**How this suite would be sh
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """D57. The loop above would pass over an empty register."""
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """The set is closed and written down. D57: the loops below pass over an empty tuple.

    Pinned as a literal rather th
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """D57 for this comparison. An empty `compare` over these ids is not evidence of stillness."""
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """The vacuity control (D57/F25).

    An argv nobody collected reports the same thing on a hardened launch and an unhar
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """D57. A register of nothing disables clause 3 while looking built.

    This is the test that would have failed on 202
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """D57 for this check. An empty reference set finds nothing and reports clean.

    Derived rather than typed out, so a 
- **enforced_by** → [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]] — """Containment assertions, each paired with the control that stops it reading green.

**How this suite would be shown va
- **enforced_by** → [[module__harness_containment_test_image_and_lane|C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.]] — """D57. A scan that enumerated zero images is the observation a broken probe produces."""
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
- **enforced_by** → [[module__harness_oracle_fingerprints|Runs INSIDE the oracle image. Emits digests and names, and never the source itself.]] — # D57. A register built from zero files would disable clause 3 while looking built.
- **enforced_by** → [[module__harness_oracle_run|Runs the oracle image. Outside the container, and it never imports the oracle.]] — # D57. Zero vectors answered is not agreement; it is a cross-check that did not run.
- **enforced_by** → [[module__harness_selftest_test_replay|Byte-identical deterministic replay, and the control that stops it being trivial.]] — """Byte-identical deterministic replay, and the control that stops it being trivial.

**P0-5 of the narrowed Phase 0 exi
- **enforced_by** → [[module__harness_selftest_test_replay|Byte-identical deterministic replay, and the control that stops it being trivial.]] — """D57 at the product boundary.

    A metric over zero tracks still returns something, and that something would be stam
- **enforced_by** → [[module__harness_stamp_test_verdict_map|The verdict table's own tests, including its vacuity control.]] — """D57. A mapping with no rows would pass every row-wise test below for free."""
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
- **enforced_by** → [[module__src_replay_harness|The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.]] — # D57 at the product boundary. A metric over zero tracks returns something, and
- **enforced_by** → [[module__tests_test_stamp_schema_contract|ADR-0006's enforcement clauses, as executable checks with their own controls.]] — """ADR-0006's enforcement clauses, as executable checks with their own controls.

The ADR's Consequences list names four
- **enforced_by** → [[module__tests_test_stamp_schema_contract|ADR-0006's enforcement clauses, as executable checks with their own controls.]] — """D57. Every check below iterates the registry and would pass on an empty one."""
- **enforced_by** → [[module__tests_test_stamp_schema_contract|ADR-0006's enforcement clauses, as executable checks with their own controls.]] — # D57: a scan of zero files is not a pass.
- **enforced_by** → [[module__tests_test_stamp_v1_vectors|The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).]] — """The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).

`harness/acs/gen_vectors.py` write
- **enforced_by** → [[module__tests_test_stamp_verify|The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).]] — """D57. Both directions above are set comparisons and would agree on two empty sets."""
- **enforced_by** → [[module__tests_test_stamp_verify|The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).]] — """D57. The parametrized check above would report nothing on an empty table."""
