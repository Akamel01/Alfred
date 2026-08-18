---
status:        provisional
owner:         human
enforcement:   review-cadence
evidence:      Derived from the eight completed handoffs (H1–H8) and a repository inventory verified 2026-08-17. Every "does not exist" below was checked against the filesystem, not recalled.
falsifies_if:  Any stage below is completed out of the stated order without a waiver ADR and the stage it was said to block proceeds unaffected — meaning the dependency was asserted rather than real.
review_after:  Phase 0 exit
---

# Execution Order

What gets built, in what order, and what each thing blocks.

**This is not `READING-MAP.md`.** That maps documents to the phase in which they are read.
This maps *work* to the order in which it can be done. A document being written does not
make the thing it specifies exist, and as of 2026-08-17 the gap between those two is the
single most important fact about this project's state.

## The ordering principle

Stages are ordered by **what unblocks what**, never by what is interesting or what is
nearly done. A stage may start when every stage it depends on has completed, and not before.
Where two stages are mutual controls on each other, they are one stage — splitting them
produces a period during which each appears to pass because the other is absent.

## Verified inventory — 2026-08-17

Checked against the filesystem. This is the honest starting position.

| Area | State |
|---|---|
| Documentation register | **63 documents**, both gates green. The most complete asset. |
| ACS-1 (encoder, JS second implementation, 343 vectors, 47 mutants) | **Built and mutation-controlled.** |
| `MetricValue` / `MetricSeries` / reason codebook | **Built.** 98 tests, `pyright --strict` clean. |
| Result stamping (`src/provenance/`) | **Built**, missing the schema version and upstream toolchain fields. |
| Lane controls (`harness/lane/`) | **Built**, no mutation harness, no parallel-slot fingerprint field. |
| Throwaway DB cluster fixture (`harness/db/`) | **Built.** Roles and grants apply against a real cluster. |
| CI (5 jobs) | **Built and green.** |
| `EvidenceStore` (append-only, hash-chained) | **Built 2026-08-17.** ADR-0010. |
| `CriterionRunner` (materialize, execute, compose, record) | **Built 2026-08-17.** ADR-0011. |
| **Remaining inspector ports** — `PolicyEngine`, `AutonomyGate`, `Worker`, `Sandbox`, `VcsGateway` | **None exists.** Zero classes. |
| **Migration versions** — product, control, evidence, heldout | **Built 2026-08-17.** Fourteen tables. ADR-0009. |
| `src/thresholds`, `src/ingest`, `src/replay`, `src/api` | **Empty directories.** |
| `tests/heldout`, `tests/reference` | `__init__.py` only. **No held-out criterion exists.** |
| Oracle environment (D54) | **Does not exist.** |
| Seeded resampler (D49 P3) | **Does not exist and has never been specified.** |
| `assert_grants.py` | **Built 2026-08-17**, set equality both directions, mutation-controlled. ADR-0009. |
| `lint_verdict_boundary.py` (D16/D39) | **Built 2026-08-17**, with a committed self-test. ADR-0012. |
| C6 egress canary, C7 oracle-absence probe | **Built 2026-08-17.** ADR-0013. Enforcement (`nftables`, build-time closure) outstanding. |
| Chain re-walk (JS), anchor, D-synthetic restore drill | **Built 2026-08-17.** ADR-0014. WAL archiving, PITR, off-machine target and D-production outstanding. |
| `lint_invariants.py`, `lint_tier0_adr.py`, `harness/lane/mutate.py` | **Absent**, all three specified as enforcement somewhere. |

## The calendar finding, stated plainly

Phase 0 exit is **2026-09-09** — 23 days from this inventory, roughly **66 working hours** at
the declared 20 hrs/week. Its exit criteria require: CriMe's asserted values reproduced on six
named scenarios; the null-agent floor test; the seeded-defect suite reddening correctly; the
egress canary firing; byte-identical deterministic replay; deploy and rollback verified; and
an off-machine backup with a verified restore drill.

Every one of those depends on components that do not exist, and several depend on a database
that has no tables. **Phase 0 as specified does not fit in 66 hours.** This document does not
resolve that — it is an operator decision under D28, and the honest options are to move the
date with a waiver ADR, or to narrow Phase 0's exit the way D36 narrows a task class. What is
not available is arriving at 2026-09-09 and declaring exit on a subset without saying so.

---

## Stages

### S0 — Land the decided-but-unapplied text · *blocks nothing, decays if deferred* · **DONE 2026-08-17**

Merge-ready text from H3, H4, H5 and H8 that encodes decisions already made. It blocks no
build work, and it goes first anyway: unapplied decisions drift out of agreement with the
code, and this backlog is already three streams deep. Details in *Merge-ready backlog* below.

### S1 — Database foundation · *blocks S3, S4, S6, and all of Phase 1* · **DONE 2026-08-17**

Alembic versions for all four schemas — product, control, evidence, heldout — plus
`harness/db/assert_grants.py` asserting the grant matrix by **set equality, never subset**,
with negative tests asserting `SQLSTATE 42501` specifically rather than "an exception was
raised". A subset check passes on every extra grant, and an extra grant is the only kind that
fails silently in the safe-looking direction.

Nothing that stores a verdict, an evidence row, or a held-out value can be built before this.
It is the widest blocker on the board.

### S2 — Oracle environment · *blocks S5's reference values and the D49 P3 decision* · **ENVIRONMENT DONE 2026-08-18**

One offline environment, pinned at CriMe commit `60bebed`, that never executes agent-authored
code. Its outputs cross into `heldout` as data; its code never crosses at all (D54). Likely a
Linux container: CriMe's compiled dependencies declare POSIX/Linux, and whether macOS arm64
wheels exist is **unverified** — a build-time discovery that must be made before 2026-09-09,
not after.

This stage is gated by an operator decision (O3 below): validate D49's P3 rung, or take D49's
stated degradation now. The environment is required either way, because Phase 0's exit
criterion *is* reproducing oracle values.

**The wheel question is answered, and it forced the answer rather than informing it.**
Measured against the PyPI JSON API on 2026-08-18, not read from a classifier: no arm64
wheel has ever been published for `commonroad-drivability-checker`, `commonroad-reach` or
`commonroad-clcs`, on any operating system. The last two have never published a macOS wheel
of any kind; the first has published sixteen, every one `macosx_10_13_x86_64`, Intel only,
none since 2022 — while its classifiers declare `Operating System :: MacOS`. The classifier
is a claim by the publisher; the wheel list is the fact, and the question was answerable
either way from the metadata with only one of the two answers true. So the image is
`linux/amd64` under emulation, and Python 3.11 because `commonroad-reach` declares
`requires_python <3.12`. Both recorded in `harness/oracle/pins.py`.

**Environment closed 2026-08-18.** `harness/oracle/` holds the pinned image, the
in-container extractor, the driver and the loader. The run posture answers D50's
acquisition hole directly: `--network none`, `--read-only`, non-root, no repository mount
at all, and the pyximport build warmed into the image so the run compiles nothing. Two
things the build discovered that a future attempt to slim the image will rediscover: the
closure is **not wheels-only** (`polygon3` is sdist-only and needs a compiler), and
`commonroad_reach` **compiles a Cython module at import time**.

**What is done here is the mechanism, and the mechanism is the factory's.** The 28-point
set that proved it out — 28 ok, 0 mismatch, 0 error, every point agreeing with CriMe's own
pinned literal — is domain content and is a worked seed, not the deliverable. Extending it,
and everything downstream of it, is agent work under the ownership rule below.

**A labelling defect the extraction found in the plan's own exit criterion.** Read from
`tests/test_time_domain.py` at the pinned SHA: the value 2.4 recorded as `ttc_1` is computed
by **`TTCStar`**, and the value 1.25 recorded as `ttc_4` is returned by **`TTR`** on
`ZAM_Urban-7_1_S-2`, in a test whose local variable is named after the lines above it.
Phase 0's exit criterion quotes both as TTC values. Reproducing "TTC = 1.25" would be
reproducing a different measure and calling it a pass. `bench/tasks/phase1_tasks.json` has
both right; the prose does not.

### S3 — Inspector core · *blocks S4, and every verdict ever recorded* · **DONE 2026-08-17**

`EvidenceStore` (append-only, hash-chained per D43) and `CriterionRunner` (running outside the
agent tree, materializing its environment from trusted provenance per A1). Verdict writes live
in a module with **no import path from any agent module**, in a separate process, under a
separate DB role — physical separation, never a runtime field-name check (D39).

Ships with the D16 lint: no agent-invoking node's return annotation may include a verdict
field. LangGraph raises only on *concurrent* unreducered writes, so a sequential write to a
verdict field is silent, and convention alone does not hold this.

**Closed 2026-08-17.** `EvidenceStore` (ADR-0010), `CriterionRunner` (ADR-0011) and
`scripts/lint_verdict_boundary.py` (ADR-0012) exist and are gated in CI. The lint runs in
three directions rather than one — vocabulary, agent tree reaching a verdict module
transitively, and a verdict module reaching the agent tree — and **fails when a check
scans zero files**, because the V half has no agent-invoking node to look at until a graph
exists and would otherwise report green for a reason unrelated to the property.

One thing S3 settled that the stage description did not anticipate: held-out reference
values are graded **outside** the criterion environment. Injecting them into it would put
the expected answer in the same directory as the code being measured, which a stub reads
and returns — D50's delegation failure past the oracle-absence probe. ADR-0011.

### S4 — The two suites, together · *blocks Phase 0 exit; blocked by S1, S3* · **DONE 2026-08-18**

The null-agent floor suite and the seeded-defect ladder are **one stage because they are each
other's vacuity control**. Replace every criterion with `return 0.0` and the floor suite passes
while the ladder's green rungs fail; a ladder of red-expectations alone is passed by a runner
that fails unconditionally. Built separately, there is a window in which each looks correct
because the other is absent.

The ladder is two-sided: green inside tolerance at δ = 0, τ/2, τ·(1−ε); red outside at
τ·(1+ε), 10τ, O(1). **The rung just outside tolerance is the only one constraining τ's
calibration** — passing the far rungs with it absent means τ could be ten times looser and
nothing would notice. ε is measured from the criterion's noise floor, never chosen; a τ that
cannot resolve ε is a finding about τ.

**Closed 2026-08-18, and the S2 dependency dissolved on inspection.** The ladder measures
the *runner's* tolerance behaviour, not a metric's correctness, so calibrating it against a
domain metric would confound the two and make a factory gate depend on a domain that may be
written off. `harness/selftest/` uses a **synthetic** criterion instead: the sum of floats
spanning many magnitudes, chosen because it has a genuine, measurable noise floor —
summation is order-dependent, so two equally correct implementations disagree by a real
amount. Measured spread **1.02e-2** over 64 seeded permutations; at τ = 0.05 that gives
**ε = 0.203**, and `run_ladder` *refuses* a τ inside the noise floor rather than widening
it, because a suite that silently corrected the tolerance would report a calibration it had
just invented.

Six rungs, six agreements, both calibrating rungs correct. The three controls are committed
beside the suites and demonstrate the mutual claim rather than asserting it:

| Control | ladder green rungs | ladder red rungs | floor suite |
|---|---|---|---|
| always-pass | miss | **catch 3/3** | **catches** |
| always-fail | **catch 3/3** | miss | **fooled — passes** |
| every criterion `return 0.0` | **catch 3/3** | miss | **fooled — passes** |

That is the argument for one stage rather than two, on real data: a runner that fails
unconditionally passes the floor suite cleanly and is caught only by the ladder's green
rungs.

**The floor suite found a defect before it had ever passed** — `materialize` raised on an
absent candidate path, which a caller maps to a harness fault, which maps to
`indeterminate`, which is excluded from the merge rate on both sides. The null agent would
have left the denominator instead of scoring at the floor. Fixed and split by owner: a
missing *trusted* path still raises. ADR-0015, and it is an inspector patch awaiting O9.

### S5 — Product path to a reproduced number · *blocks Phase 0 exit; blocked by S1, S2*

`ingest` (CommonRoad adapters) → `metrics` (TTC and PET against Westhofen's formulas) →
`replay` (deterministic, byte-identical) → stamping wired through → `api`. Exit is CriMe's
asserted values reproduced on the six named scenarios within a documented tolerance, with the
documentation stating plainly that these are CriMe's self-consistency tests and are therefore
ground truth only for a reimplementation treating CriMe as an oracle.

### S6 — Containment · *blocks Phase 1 dispatch; blocked by S1* · **PROBES DONE 2026-08-17, enforcement outstanding**

Egress canary (A7) — the run refuses to start unless a known non-allowlisted connection
fails, enforced by `nftables` default-drop, because environment-variable proxy configuration
is advisory and bypassable. Plus the D54 oracle-absence probe in **both** the agent container
and the criterion environment, since agent-authored code executes in the latter; `find_spec`
rather than `import`, because importing a module to learn whether it is importable executes
its module-level code inside the sandbox.

Every failure path fail-closed, the probe erroring included. `not_executed` is a failure,
never a pass.

**Partly closed 2026-08-17** (ADR-0013). `harness/containment/` carries the assertion
vocabulary, the versioned denylist and network policy under `policy/`, the C6 canary with
its loopback control, and the C7 probe's layers 1–3. What remains is the enforcement half,
which is not code in this repository: `nftables` default-drop in the host network
namespace, and the image-build closure check wired to a real resolved lockfile. Until
those exist the canary is a verification with nothing to verify against — and it says so,
reporting FAILED on any unfiltered host.

### S7 — Durability · *blocks Phase 0 exit; blocked by S1* · **D-SYNTHETIC DONE 2026-08-17, archiving and PITR outstanding**

Continuous WAL archiving and base backups to an off-machine target; evidence rows
hash-chained with the head anchored off-machine daily; a restore drill as an executable check.

**"Restore verified" splits in two.** A synthetic drill in CI proves the *mechanism*; only a
drill against the actual off-machine backup proves the *artifact*. The chain re-walk must use
the **JavaScript** implementation — checking a chain the Python encoder wrote, using the Python
encoder, checks nothing — and must assert the walk is **total**: one head, no forks. A chain
check that verifies each link but never checks they form a single path passes on a forked
audit log.

**D-synthetic done 2026-08-17** (ADR-0014). `verify_chain.mjs` re-walks under stock Node
against the anchor; `export.py` computes nothing; the drill dumps and restores into a
*second* throwaway cluster and refuses to restore into its source. Two findings are asserted
for rather than tolerated: no Tier 0 recovery objective exists, and artifact resolution is
unexercised because no artifact store does.

**Outstanding, and it is most of the stage — none of it code in this repository:**
continuous WAL archiving, an off-machine target, the daily anchor job, **point-in-time
recovery**, and a recorded D-production run. PITR matters more than its omission looks: a
drill restoring only to latest cannot distinguish a working WAL archive from a working base
backup with a broken archive, and PITR is the capability that matters after the bad
migration D43 names.

### S8 — Deploy and rollback · *blocks Phase 0 exit* · **DONE 2026-08-18**

`docker compose up` serves the API; deploy and rollback both execute and are verified.

**Closed 2026-08-18.** `src/api/` is the deployable unit, `deploy/api.Dockerfile` builds
it, the compose file carries the service, and `harness/deploy/` holds the ledger, the
driver and the tests. Two releases were built, deployed and rolled back on this machine;
each transition was confirmed by reading `/version` from the running service.

**One decision carries the whole stage: the release identity is baked into the artifact.**
`/version` reports what the running image says it is, from build arguments promoted to
environment variables — never from the repository, a mount, or a `git` call at request
time. Read the identity from outside the artifact and a rollback reports the old release
while the new code keeps serving, with the verifier agreeing: the check passes in exactly
the situation it exists to detect. An image built without an identity fails at import
rather than serving anonymously.

Deploy goes **through** `docker compose` rather than around it, because the exit criterion
names that path and a mechanism verified on some other path has verified some other
mechanism. Rollback is the same code with a different target — a rollback running code a
deploy never exercises is a path first executed during an incident. The ledger is written
only *after* the intended release is observed serving; recording first would leave a
history claiming a deploy that never took, and the rollback target is chosen from that
history.

Three states are failures rather than no-ops, each with a test: rolling back with no
recorded release, rolling back when every recorded release is the one serving, and a
deploy whose service answers with a different release than the one intended. That last one
is the control the stage rests on — verified by exit code it passes, because
`docker compose up` succeeded.

The rollback target is found by scanning for a different `release_id`, not by taking the
second-to-last row. A positional rule oscillates: after deploy r1, deploy r2, rollback to
r1, the second-to-last row is r2, so the next rollback returns to r2, then r1, forever,
reporting success at every step.

`docs/tier2/branch-release-deploy-protocol.md` is promoted from stub. Its branch and patch
half remains unobserved and says so — no agent branch has ever been opened.

**Two things this stage does not do.** There is no rollback of the *database*: evidence
migrations are additive-only and their downgrade raises, so an application rollback across
a migration is not symmetric. Phase 0 does not hit it because the API holds no database
credential, and S7's point-in-time recovery is where it gets answered — still outstanding.
And a **technology selection record is owed** for FastAPI and uvicorn:
`docs/tier1/technology-selection-records.md` is `owner: human`, and its falsification
condition — "a technology is adopted with no corresponding record" — is met until the
operator writes one.

### S9 — Phase 1 build · *blocked by S1–S8 and by O1*

`Worker` port and the OpenHands adaptor, pinned by commit SHA; the fifteen numbered boot
assertions (D53); patch validation on the privileged side with the A10 unicode scan; and the
mission-control command surface, which is inspector under D51 and therefore operator-built.

**The OpenHands source read (O5) must precede the containment assertions.** Their premises are
unverified first-hand, and an assertion resting on a *misnamed* config key or event class
reports `passed` while the control it names does nothing — executed, passed, and vacuous. That
is a third outcome the register does not currently name.

---

## The ownership rule

Set by the operator on 2026-08-18, and it re-cuts several stages: **AV domain content —
metrics, reference values, the product path — is agent work. What is built, verified,
validated and tested here is the factory.**

The split is by layer, not by stage. The oracle *environment* is factory and is inspector
besides, since agents may never author their own ground truth; the *point set* is domain.
The *ports* — `TrajectorySource`, `Metric`, `ReplayHarness` — are factory; every
implementation behind them is domain. S4, S8 and the domain-neutral half of S9 are factory
throughout.

One dependency dissolved under the rule, and it had been recorded as real: S4 was listed as
blocked by S2 for the ladder's calibration. Calibrating the inspector against domain content
was the wrong instinct — see S4.

Tier 0 carries the authorship boundary and is permanently operator-authored, so this rule is
recorded here rather than there. Whether it belongs in Tier 0 is an operator edit.

## Operator-owned, non-delegable

These cannot be built by anyone else, and four of them block stages above.

| # | Item | Blocks | Date |
|---|---|---|---|
| O1 | `F` (fixed weekly obligations, min/week) and target `n` (tasks/day, **stated as dispatched or merged**) | The capacity gate; S9's sizing | Before Phase 1 |
| O2 | Defect-escape **observation window** | The 2026-12-31 anchor's pass condition | Before Phase 2 exit |
| O3 | D49 P3: validate, or take the stated degradation to the 10 strong P1 measures | S2's scope; Phase 1's exit shape | **2026-09-09** |
| O4 | Phase 0 exit: move the date under a waiver ADR, or narrow the exit | Everything | **2026-09-09** |
| O5 | Read OpenHands at the pinned SHA | S9's containment assertions | Before S9 |
| O6 | Company formation — entity, liability-capped pilot template, insurance quote | First prospect conversation | **2026-09-09** |
| O7 | EU 2022/1426 approval-register lookup (~1 hr) | Should precede conversation one | Before O8 |
| O8 | Three Track-1 discovery conversations | K1, K2 | **2026-10-07** |
| O9 | Line-by-line review of inspector patches — ACS-1 `operator_action` vector, `lint_tier0_adr.py` | Their landing | Rolling |

## Merge-ready backlog (S0)

Text that is decided and unapplied. Owners are the stream that drafted it; the orchestrator
applies.

- **H3** — D55; ADR-**0006** (renumbered: H1 took 0005); plan edits at the "One thing the pivot
  broke" paragraph and the "no recall path" clause; D30 "upstream toolchain identity" → "as
  declared"; forward pointers on ADR-0001 and ADR-0003.
- **H8** — D56 (defect-escape recording starts at first merge); the Phase 2 section
  replacement; the port-blueprint paragraph.
- **H5** — D57; the new `harness-self-test-specification.md` plus its one-line `PHASES` entry
  in `scripts/gen_reading_map.py`; stable row ids `F1`…`F24` on the fail-closed table, whose
  three dispositions (run does not start / `indeterminate` / halt-and-reject) must not be
  compressed into one.
- **H7** — ADR-**0007** on containment-assertion vacuity.
- **H4** — seven changes to `mission-control-specification.md`; a D51 amendment; the
  capacity-arithmetic paragraph; and the fix at `mission-control-design.md:60–63`, where the
  prose says 20 + 8 minutes and subtracts 33 while the table requires 25 — a `ci-gate`
  document whose central table cannot be reproduced from its own stated inputs.

## What must not be built yet

Named so that being ready is never mistaken for being due.

- **No orchestration** before per-task merge rate clears K3's Wilson lower bound. Orchestration
  multiplies throughput; it does not fix quality.
- **No workflow engine** before a work item genuinely spans multiple irreversible steps.
- **No retrieval index** before the miss rate measurably costs verdicts or the repo passes
  ~1000 files.
- **No graph editor.** The graph definition declares field ownership and verdict-node
  placement, so a GUI writing it is a second authoring path around the D16/D39 lint.
- **No AV-specific investment** if K2 fires — while factory stages proceed regardless.
