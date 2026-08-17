---
status:        provisional
owner:         executable
enforcement:   ci-gate
evidence:      Every headline number in this project has been wrong on first read, four for four, each time because the instrument was trusted before it was checked. The ACS-1 mutation control is the worked precedent: 47 mutants, worst margin 10 checks, with a negative control that reports UNDETECTED on a no-op mutant and aborts on a mutation that fails to apply.
falsifies_if:  A suite specified here passes while the control it guards is disabled; or a seeded defect at a delta just outside a declared tolerance is not red; or the null-agent floor scores above zero; or an injected fault produces `pass`.
review_after:  Phase 1
---

# Harness Self-Test Specification

The inspector's inspector (major-fix #1). Every suite here tests the machinery that
produces verdicts, not the product.

**The organizing rule: a passing suite and a vacuous suite report the same thing.** Each
section therefore states three things — what the suite asserts, what it *cannot*
establish, and the mutation that would expose it as empty. A suite specified without the
third is not specified.

---

## 1. The seeded-defect ladder

Deliberately wrong metric implementations at known deltas from a reference value, which
`CriterionRunner` must grade correctly.

**Two-sided, and this is the load-bearing change.** `testing-strategy.md` and
`failure-semantics.md` both describe this suite entirely in terms of what must go **red** —
and a suite of red-expectations alone is passed by a `CriterionRunner` that fails
unconditionally. Nothing in the register ruled that out.

| Rung | Delta from reference | Expected |
|---|---|---|
| R0 | δ = 0 (the reference implementation itself) | **green** |
| R1 | δ = τ/2 | **green** |
| R2 | δ = τ·(1−ε) | **green** |
| R3 | δ = τ·(1+ε) | **red** |
| R4 | δ = 10τ | red |
| R5 | δ = O(1) — a structurally wrong implementation | red |

**R3 is the only rung that constrains the tolerance's calibration.** R4 and R5 passing
with R3 absent means τ could be ten times looser and nothing would notice. A ladder
missing R3 tests that the runner detects gross error, which was never in doubt.

**ε is measured, never chosen.** It comes from the criterion's own noise floor — the
run-to-run spread of the reference implementation under the declared tolerance. A τ that
cannot resolve ε is a finding about τ, not a reason to soften the rung. Record the
measured ε alongside each criterion.

**What this cannot establish.** Nothing about a criterion that awards partial credit for a
nonempty-but-wrong patch (R5 bounds it only at O(1)); nothing about criteria added later,
hence the coverage rule in §7.

**Mutation control.** Criterion always returns pass → R3–R5 fire. Criterion always returns
fail → R0–R2 fire. Tolerance widened 10× → R3 fires alone, which is the point of R3.

---

## 2. The null-agent floor (A1)

A run that takes no actions. Its score is the harness's floor, asserted permanently.

| Id | Construction | Is it the floor? |
|---|---|---|
| **F0** | `WorkerClaim.patch is None`, `tree_sha256_final == tree_sha256_initial`, zero mutating tool calls, `outcome = AGENT_STOPPED` | **Yes.** |
| F1 | a well-formed diff with zero hunks emitted to the patch volume | No — the tree is unchanged but an artifact exists and the validator runs |
| F2 | a diff touching only whitespace, EOL or trailing space | No — the tree *did* change |
| F3 | F0 plus a `conftest.py` / `sitecustomize.py` / `.pth` forcing collection to report success | No — this is the A1 test |

**F0 asserts two things, not one:** score exactly zero on **every** criterion in the golden
set, **and** verdict `fail` — not `indeterminate`. An agent that did nothing is a real
capability result and belongs in the merge-rate denominator. If F0 returns `indeterminate`,
every do-nothing run silently leaves the denominator and merge rate is inflated by exactly
the runs that most deserve to depress it. **This is the assertion most likely to be missing
and the most damaging to omit.**

**F1's expected result is declared, not discovered.** Either an empty diff is a valid
no-change patch (score 0, verdict `fail`, identical to F0) or it is unparseable (patch
rejected, verdict `fail`). Both defensible. Not permitted: `indeterminate`, which
attributes a validator limitation to the harness's health metric, or nonzero, which is an
empty diff earning credit.

**F2 must score exactly F0's score.** Above zero means a criterion is sensitive to
formatting, so merge rate is partly measuring the formatter. This is the rung most likely
to fire against a real criterion set.

**F3 must be byte-identical to F0**, because `CriterionRunner` materializes from declared
source paths and ignores everything else. Without F3 this is a floor test; with it, it is
the test of A1's architectural claim — the one closing the `conftest.py` / `.pth` /
`sitecustomize` / binary-trojan class by construction rather than by enumeration.

**What this cannot establish.** Nothing about a criterion added tomorrow — hence the
per-criterion assertion and the coverage rule in §7. A single aggregate "floor = 0" is
satisfied by a set where one criterion awards +0.3 and another −0.3. It also asserts the
*declared* floor; it does not derive it.

**Mutation control.** Criterion returns fixed 1.0 → F0 fires. Declared-source-path filter
disabled → F3 fires. Whitespace normalization removed → F2 fires. `patch is None` mapped
to `indeterminate` → F0's verdict assertion fires.

---

## 3. Fault injection for three-valued verdicts

Every row of `failure-semantics.md`'s fail-closed table (`F1`…`F27`) is an injected fault
with a test.

**The assertion differs by disposition, and this is the section's whole content.** The
table carries three dispositions plus one deliberate fail-open, and compressing them into
"must produce `indeterminate`" loses the property on more than half the rows:

- *Run does not start* — assert **no verdict row exists at all**, and the run appears on
  **neither** side of the merge rate. A differently shaped and stronger claim than
  `verdict == indeterminate`.
- *`indeterminate`* — assert the verdict, and assert exclusion from both sides of the rate.
- *Halt or reject* — assert **the next side effect did not occur**, not merely that an
  exception was raised.
- *Fail-open* (`F27`, backup unreachable) — assert dispatch **continued and** an escalation
  was raised. A test asserting only "continued" passes on a system ignoring the condition
  entirely.

**Every injection carries a witness.** The injecting double records that it was invoked; a
test whose witness is unset **fails**. An injector that silently failed to apply produces a
green test reading as a working control — the same defect class as a mutation that fails to
apply reading as a suite hole, which is why `mutate.py` aborts rather than reporting.
Fault injection is unusually easy to write vacuously and this rule is what stops it.

**Injections are supplied through port boundaries, never by in-place monkeypatching.**

Sharpest individual assertions:

- **Held-out schema unreachable** must run with **all visible criteria passing**. Otherwise
  a visible `fail` masks the property under test — that the run is `indeterminate` and
  never a `pass` on visible criteria alone. Injection: revoke `alfred_criterion`'s `USAGE`
  on `heldout` on the throwaway cluster. Runnable today.
- **Killed criterion runner** — SIGKILL after the first criterion completes and before the
  last; assert the completed criterion is **not** promoted to a partial pass.
- **Chain head unreadable** — assert **no second row was appended**. The property is the
  absence of a fork, not the presence of an error.
- **Containment `not_executed`** — a three-way assertion on the enum: not collapsed into
  `FAILED`, not into `PASSED`.
- **Verdict-vocabulary field on a claim** — two independent assertions, runtime
  `indeterminate` **and** the CI lint failing, because the lint fires first and a
  runtime-only test passes on a system whose lint has been deleted.

**Coverage is enforced, not hoped for.** CI asserts a one-to-one mapping between the row
ids `F1`…`F27` and the injection ids. A row with no injection fails the build, because a
table growing faster than the suite exercising it describes a system nobody has checked.

**What this cannot establish.** It demonstrates the mapping from a **simulated** fault to a
verdict. It does not demonstrate that a real fault of that class presents the way the
double presents it: a SIGKILL is not an OOM-killed runner whose partial output was flushed;
a revoked grant is not a network partition mid-transaction. **Each injection therefore
carries a recorded note naming the real fault it stands in for and how the real thing could
differ.** That note is the honest part of the suite and the part that gets dropped first.

---

## 4. Boot-control negative tests

Specified in full in `docs/tier4/sandbox-specification.md`. The rule that belongs here:

**The negative tests run against a real difference, never a patched call.** A canary test
that mocks the network layer proves the mock. A variant image identical to the runtime
except that default-drop is lifted is a real difference. Where a real difference cannot be
constructed, the control is recorded **unproven** rather than substituted with a mock and
recorded as proven.

**Expected-miss cases are asserted as misses.** Each hole named in D54 — a renamed vendored
copy, a non-Python path, a compromised base image — gets a case asserting the probe
*does not* catch it. A control whose documented limits are untested drifts into being
described as complete.

---

## 5. Adaptor admission (D52)

A `Worker` adaptor is admitted on four demonstrations, not on a passing integration test:

1. **Assertion coverage** — every containment assertion the port requires is present and
   reports `passed`; `not_executed` is a failure.
2. **Instrumentation completeness** — a scripted agent performing a known set of actions
   produces a read log and event stream matching that set, checked against the executor's
   own durable event count.
3. **Fault fidelity** — under injected faults the adaptor raises the right exception class.
   **The most likely defect in any adaptor is reporting a killed executor as an agent
   failure**, which moves harness flakiness into the numerator of the only number the
   autonomy gates read.
4. **A declared epoch boundary** — the adaptor's identity and version are fingerprint
   fields, and adopting a new one invalidates prior grants.

**What this cannot establish.** A scripted agent exercises the actions someone thought to
script. It bounds the instrumentation's completeness *relative to that set* and no further
— which is the same downgrade D26 already took, and it is stated here rather than
rediscovered.

---

## 6. The restore drill (D43)

**Two drills, and conflating them is the failure.**

- **D-synthetic** — runs in CI on every change. A throwaway cluster seeded with a synthetic
  chain plus a throwaway artifact directory; destroyed, restored, compared. **Proves the
  mechanism.**
- **D-production** — scheduled and operator-gated. Restores the **actual off-machine
  backup** into a fresh throwaway cluster and compares against the live chain head and
  anchor. **Proves the artifact.** It cannot run in CI, which has no access to the
  off-machine target.

**"Restore verified" as a Phase 0 exit criterion means a recorded D-production run, not a
green CI job.** A green D-synthetic proves a procedure works on a cluster shaped like the
real one and says nothing about the bytes actually sitting off-machine.

**Never destroy the live cluster.** A drill whose failure mode is the incident is not a
drill.

**Restore to two targets, both required.** *Latest* — recovery to end of WAL, proving
continuity. *Point-in-time* — recovery to a timestamp strictly before the last few writes,
asserting rows after the target are **absent**. A drill restoring only to latest cannot
distinguish a working WAL archive from a working base backup with a broken archive, and
PITR is the capability that matters after the bad migration D43 names.

**Four comparisons, in increasing strength, all of them:** row counts per table (catches
truncation); set equality of primary keys (catches missing or extra rows); per-row content
hash recomputed against the stored `sha256` (catches a row whose content changed but whose
hash column came along); and the full chain re-walk.

**The re-walk is what proves the chain survived, and it has four rules:**

- Recompute each row's `sha256` over (ACS-1 canonical content ‖ `prev_sha256`) using the
  **independent implementation** — `harness/acs/acs1.mjs` under stock Node, not the Python
  one. A drill using the Python encoder to check a chain the Python encoder wrote is
  checking nothing.
- Assert the walk is **total**: every row visited exactly once, no row with two successors,
  exactly one head, walk count equal to table count. **A chain check verifying each link
  but never checking the links form one path passes on a forked chain**, and a forked audit
  log is the failure the architecture exists to prevent.
- Assert the restored **chain head equals the off-machine anchor** for that timestamp — the
  only comparison that is not self-referential. **Without it the drill proves the dump is
  internally consistent, which a competent attacker would also arrange.**
- **Artifact resolution** — every `ArtifactRef.sha256` referenced by a restored row resolves
  to bytes whose sha256 matches. A restore bringing back rows and not artifacts leaves a
  chain of references to nothing, and row counts do not notice.

**Record restore wall-clock and assert it against the Tier 0 recovery objective. If no
objective is stated, record the number and treat the absence as a finding, never a skip.**

**What this cannot establish.** That the backup will be restorable *tomorrow* — media
decay, credential rotation, format drift — hence D-production is scheduled and **its
last-success timestamp is itself an alarm**. And nothing about a compromise predating every
backup in retention; the anchor bounds this to the anchor's own retention and no further.

---

## 7. Vacuity controls, as a standing rule

**The floor suite and the seeded-defect ladder are each other's vacuity control.** Replace
every criterion with `return 0.0`: the floor suite passes while the ladder's green rungs
fail. Replace every criterion with `return 1.0`: the ladder's red rungs fail while the
floor suite catches it. **Neither may be specified, owned or modified without the other** —
which matters because they are the two most likely to be split across people or sessions.

Committed alongside every suite here:

- a **disable-all-injectors** control, under which the fault-injection suite must fail;
- an **always-pass** and an **always-fail** criterion stub, each of which must be caught;
- a **no-op mutant** that reports `UNDETECTED` rather than "ok";
- an **absent-mutation abort** — a mutation whose source text is not found aborts the run
  rather than reading as a suite hole.

Every suite states how it would be shown vacuous. A suite that does not is not admitted.

## What none of this establishes

These suites test the harness against faults someone thought of. They do not bound the
faults nobody thought of, and no suite can. What they buy is that the known controls are
demonstrably non-vacuous — which is strictly less than "the harness is correct", and is
stated that way here so that no downstream document quietly upgrades it.
