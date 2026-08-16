---
status:        frozen
owner:         human
enforcement:   ci-gate
evidence:      The visible/held-out split addresses a measured 43-48pp gap on composed operations with no exploit involved. The exclusion of mutation score follows a replication finding that mutation scores are meaningless in a bug-detection setting.
falsifies_if:  A composed property test is found that an agent could satisfy by special-casing, or held-out pass rate tracks visible pass rate across a full golden set.
review_after:  Phase 2
---

# Testing Strategy

## The adversary is deterministic tooling, not a second model

Hypothesis property tests are primary. Properties encode intent over generated inputs,
so the agent cannot special-case past inputs it never sees. An LLM adversary is reserved
for what deterministic tooling cannot reach: missing requirements.

## Property tests over composed operations are load-bearing

This is the inversion that matters. Property tests are not secondary hardening — they
are the only control that engages the failure mode where an honest agent, an honest
criterion and an honest harness still produce wrong code.

Isolated unit tests pass. Composed behaviour fails. The measured gap between visible and
held-out composed tests is 43–48pp **with no exploit involved**. Every anti-tampering
control in this architecture is orthogonal to it.

Properties the domain actually supports:

- metrics are bounded within their declared range
- monotone as closing speed increases or time-to-collision decreases
- invariant under rigid coordinate transforms — rotation and translation
- well-defined in degenerate cases: stationary ego, parallel paths, zero gap, coincident
  timestamps
- composition is consistent: a metric computed over a whole clip agrees with the same
  metric computed over its parts where the definition allows

## Three test classes

**Visible** — `tests/` generally. The agent sees these and retries against them.

**Held-out** — `tests/heldout/`, materialized only at verdict time from a separate DB
role. Composes operations end-to-end across scenario families. Never in agent context,
never in network reach.

**Reference** — `tests/reference/`. Reproduction of oracle values on named scenarios.
These are external ground truth only for a reimplementation treating the oracle as
authoritative, and the documentation says so plainly; they are the oracle's own
self-consistency regression tests, not independently published values.

Because published values are plausibly in training data and no network policy removes
that, held-out **perturbations** — recomputed values on resampled slices whose answers
were never published — carry the actual weight.

## The harness gets tested too

**Null-agent floor test.** A run taking no actions. Its score is the harness's floor,
asserted permanently. If it scores above zero, the harness is measuring itself. This
closes an entire class architecturally rather than by enumeration — a seven-line
`conftest.py` has forced a 100% resolve rate on a 500-instance benchmark without touching
a single test file.

**Seeded-defect suite.** Deliberately wrong implementations at known deltas that
`CriterionRunner` must red. Runs on every harness change.

**Negative tests.** The evidence store rejects agent-role writes. The policy engine
denies protected-path mutations. The agent-role connection fails on `SELECT` against the
held-out table.

`CriterionRunner` materializes the test environment itself from trusted provenance and
ignores everything outside declared source paths.

## What has no gating role

**Mutation score.** Mutants are generated from possibly-buggy code, and tests failing on
the original are excluded — which excludes precisely the bug-exposing tests, rendering
the resulting scores meaningless in a bug-detection setting. `mutmut` survives only as
regression on the trusted human-built skeleton, and never gates.

## Per-node checks, not only a terminal gate

A terminal verdict node is necessary but insufficient. Verification failure modes are not
rare, and sole reliance on final-stage, low-level checks is inadequate for the same
reason it is inadequate in ordinary software: robust systems need modular unit testing,
not just an end check. Checks sit at node boundaries as well as at the gate.
