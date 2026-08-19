---
status:        provisional
owner:         executable
enforcement:   ci-gate
evidence:      ADR-0022, 2026-08-19. Phase 0's criteria are written out here because the narrowing decision forced an enumeration of them; before that they existed only as prose in an orchestrator-owned plan file and no check read them. Phase 1 and later remain unwritten and say so — content written before the evidence exists cannot be current. The register this document commits to is `harness/selftest/stage_gate_register.json` and the check is `scripts/lint_stage_gates.py`.
falsifies_if:  A phase is exited with a gate red and no waiver ADR recorded; or a criterion is marked met with evidence that does not resolve; or this document names a criterion the register does not carry, in either direction.
review_after:  Phase 1 exit
---

# Stage Gate Definitions

Each phase's exit criteria, and the conditions that forbid advancing. Overriding one requires
an immutable waiver ADR.

**Promoted from stub 2026-08-19.** The stub said content written before the evidence exists
cannot be current, and that was right until ADR-0022 made the criteria a decision rather than
a restatement. What promoted it was not new confidence but a discovered gap: this document
carried `enforcement: ci-gate` while naming no check in `.github/workflows/gates.yml`, and
`gates.yml` states the rule that makes that a falsification — *"if a check a document names is
not in this file, that document's enforcement value is a wish."* It was a wish for as long as
it stood. Only Phase 0 is written out below; the later phases stay stubs, deliberately.

## Phase 0 — exit criteria, as narrowed by ADR-0022

Seven criteria. The narrowing cut along the ownership rule: the domain half — CriMe's asserted
values on the six named scenarios, and everything downstream of D49's P3 rung — is moved to a
dated residue at **2026-10-07** and is the local models' work, not the factory's. Nothing is
weakened in place; what left this table has a date and an owner.

| id | Criterion | Kind | Evidence |
|---|---|---|---|
| P0-1 | The null-agent floor test runs and the floor holds | automatic | `harness/selftest`, in CI |
| P0-2 | The seeded-defect suite reddens correctly, with its controls | automatic | `harness/selftest`, in CI |
| P0-3 | Deploy and rollback verified by what is serving, not by exit code | automatic | `harness/deploy`, in CI |
| P0-4 | The egress canary fires against real `nftables` default-drop in the host netns | attested | a recorded run on the host |
| P0-5 | Byte-identical deterministic replay, end to end on a synthetic trajectory | automatic | `harness/selftest`, in CI |
| P0-6 | A recorded D-production restore, compared against the live anchor | attested | a recorded run against the off-machine target |
| P0-7 | No unreviewed inspector patch enforces any criterion above | attested | the O9 queue, empty of enforcing patches |

**`automatic` means a check in CI decides it. `attested` means a human records the evidence and
the register carries a pointer that must resolve.** The distinction is written down because
collapsing it would let an attested criterion read as machine-verified, which is the exact
over-reading the evidence header on every document in this register exists to prevent.

### What each criterion is guarding, where that is not obvious

- **P0-4 is not the probe.** C6 exists and passes; what it proves today is that the canary
  itself works. Until `nftables` default-drop exists in the host network namespace there is
  nothing for it to verify against, and the module says so by reporting FAILED on any
  unfiltered host. Environment-variable proxy configuration is advisory and bypassable, which
  is why the enforcement layer is named rather than assumed.
- **P0-6 is D-production, not D-synthetic.** A green CI run proves the *mechanism* — dump,
  restore into a second throwaway cluster, re-walk the chain under stock Node. Only a drill
  against the actual off-machine backup proves the *artifact*. The two are different claims and
  the criterion is the second one.
- **P0-7 is a criterion rather than a note** because every other criterion here is enforced by
  inspector machinery, and unreviewed inspector machinery is ADR-0007's vacuity class one level
  up: the check executed, the check passed, and nobody established the check was right. Review
  is batched by subsystem rather than by commit.

### Forbidden advancement

- Exiting with any criterion above not `met`, absent a waiver ADR naming the criterion.
- Marking an `attested` criterion met with evidence that does not resolve. The check reads the
  pointer; a pointer to nothing is a failure, not an absence.
- Exiting on a subset without recording the subset. This is the failure the narrowing is
  written against, and ADR-0022 is the record that makes the subset legible.

### Known blocked criterion

**P0-6 cannot be evaluated at all today.** No Tier 0 recovery objective exists (D43), so a
restore drill yields a duration with nothing to compare it to. The register carries P0-6 as
`blocked` with that reason, and `blocked` fails — F25 applies to gates as much as to
containment assertions: a criterion that could not be evaluated is not a criterion that passed.
Tier 0 authorship is permanently outside the agent boundary, so this is owed by the operator.

## Phase 0 residue — due 2026-10-07

Moved by ADR-0022, not dropped. Tracked here so the two halves stay visible together.

| id | Criterion | Owner |
|---|---|---|
| R0-1 | CriMe's asserted values reproduced on the six named scenarios, within a documented tolerance | local models, under the ownership rule |
| R0-2 | D49's P3 rung validated, or its stated degradation to the 10 strong P1 measures taken (O3) | operator decision, then local models |

R0-1 carries a defect that is not this document's to fix: the plan's exit-criterion prose
labels `ttc_1≈2.4` and `ttc_4≈1.25` as TTC values on `ZAM_Urban-7_1_S-2`, and they are
`TTCStar` and `TTR` respectively. `bench/tasks/phase1_tasks.json` has both right. Reproducing
"TTC = 1.25" would be reproducing a different measure and calling it a pass, so the prose must
be corrected before R0-1 is judged. The plan file is orchestrator-owned.

## Phases 1 and later

**Stub, and deliberately so.** Phase 1's exit criteria depend on measurements Phase 1 exists to
take — per-task human minutes, per-task merge rate as a Wilson interval, held-out pass rate
stratified by provenance tier. Writing them out now would be writing numbers before the
instrument that produces them, which is the defect this document was a stub to avoid and which
ADR-0022 removed only for Phase 0.

What is already fixed and is not a guess: the dated milestones in the risk register, and K3's
form — the criterion fires when the Wilson interval's lower bound sits below 0.50, read as an
interval and never as a point estimate.

## Enforcement

`scripts/lint_stage_gates.py`, wired into `.github/workflows/gates.yml`.

Two modes, and the split is the point:

- **Default — register integrity.** Every criterion id in this document has exactly one entry
  in `harness/selftest/stage_gate_register.json` and every entry names a live criterion; every
  entry marked `met` carries evidence that resolves; every status is legal. Runs on every push.
  It is green today and says nothing about whether Phase 0 may be exited.
- **`--gate phase0` — the exit gate.** Every criterion must be `met`. Run when exit is claimed,
  not on every push: a gate that reports red from the day it is written until the day the phase
  ends would be red for reasons nobody reads, and a check nobody reads is off.

Both modes fail on zero criteria scanned. A gate with nothing to evaluate reports what a passed
gate reports, and that confusion has been paid for here before.

## Falsification condition

A phase is exited with a gate red and no waiver ADR recorded; or a criterion is marked met with
evidence that does not resolve; or this document names a criterion the register does not carry,
in either direction.
