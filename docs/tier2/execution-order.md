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
| Documentation register | **61 documents**, both gates green. The most complete asset. |
| ACS-1 (encoder, JS second implementation, 343 vectors, 47 mutants) | **Built and mutation-controlled.** |
| `MetricValue` / `MetricSeries` / reason codebook | **Built.** 98 tests, `pyright --strict` clean. |
| Result stamping (`src/provenance/`) | **Built**, missing the schema version and upstream toolchain fields. |
| Lane controls (`harness/lane/`) | **Built**, no mutation harness, no parallel-slot fingerprint field. |
| Throwaway DB cluster fixture (`harness/db/`) | **Built.** Roles and grants apply against a real cluster. |
| CI (5 jobs) | **Built and green.** |
| **Every inspector port** — `CriterionRunner`, `EvidenceStore`, `PolicyEngine`, `AutonomyGate`, `Worker`, `Sandbox`, `VcsGateway` | **None exists.** Zero classes. |
| **Migration versions** — product, control, evidence, heldout | **All four empty.** No table exists anywhere. |
| `src/thresholds`, `src/ingest`, `src/replay`, `src/api` | **Empty directories.** |
| `tests/heldout`, `tests/reference` | `__init__.py` only. **No held-out criterion exists.** |
| Oracle environment (D54) | **Does not exist.** |
| Seeded resampler (D49 P3) | **Does not exist and has never been specified.** |
| `assert_grants.py`, `lint_invariants.py`, `lint_tier0_adr.py`, `harness/lane/mutate.py` | **Absent**, all four specified as enforcement somewhere. |

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

### S0 — Land the decided-but-unapplied text · *blocks nothing, decays if deferred*

Merge-ready text from H3, H4, H5 and H8 that encodes decisions already made. It blocks no
build work, and it goes first anyway: unapplied decisions drift out of agreement with the
code, and this backlog is already three streams deep. Details in *Merge-ready backlog* below.

### S1 — Database foundation · *blocks S3, S4, S6, and all of Phase 1*

Alembic versions for all four schemas — product, control, evidence, heldout — plus
`harness/db/assert_grants.py` asserting the grant matrix by **set equality, never subset**,
with negative tests asserting `SQLSTATE 42501` specifically rather than "an exception was
raised". A subset check passes on every extra grant, and an extra grant is the only kind that
fails silently in the safe-looking direction.

Nothing that stores a verdict, an evidence row, or a held-out value can be built before this.
It is the widest blocker on the board.

### S2 — Oracle environment · *blocks S5's reference values, the S4 ladder's calibration, and the D49 P3 decision*

One offline environment, pinned at CriMe commit `60bebed`, that never executes agent-authored
code. Its outputs cross into `heldout` as data; its code never crosses at all (D54). Likely a
Linux container: CriMe's compiled dependencies declare POSIX/Linux, and whether macOS arm64
wheels exist is **unverified** — a build-time discovery that must be made before 2026-09-09,
not after.

This stage is gated by an operator decision (O3 below): validate D49's P3 rung, or take D49's
stated degradation now. The environment is required either way, because Phase 0's exit
criterion *is* reproducing oracle values.

### S3 — Inspector core · *blocks S4, and every verdict ever recorded*

`EvidenceStore` (append-only, hash-chained per D43) and `CriterionRunner` (running outside the
agent tree, materializing its environment from trusted provenance per A1). Verdict writes live
in a module with **no import path from any agent module**, in a separate process, under a
separate DB role — physical separation, never a runtime field-name check (D39).

Ships with the D16 lint: no agent-invoking node's return annotation may include a verdict
field. LangGraph raises only on *concurrent* unreducered writes, so a sequential write to a
verdict field is silent, and convention alone does not hold this.

### S4 — The two suites, together · *blocks Phase 0 exit; blocked by S1, S2, S3*

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

### S5 — Product path to a reproduced number · *blocks Phase 0 exit; blocked by S1, S2*

`ingest` (CommonRoad adapters) → `metrics` (TTC and PET against Westhofen's formulas) →
`replay` (deterministic, byte-identical) → stamping wired through → `api`. Exit is CriMe's
asserted values reproduced on the six named scenarios within a documented tolerance, with the
documentation stating plainly that these are CriMe's self-consistency tests and are therefore
ground truth only for a reimplementation treating CriMe as an oracle.

### S6 — Containment · *blocks Phase 1 dispatch; blocked by S1*

Egress canary (A7) — the run refuses to start unless a known non-allowlisted connection
fails, enforced by `nftables` default-drop, because environment-variable proxy configuration
is advisory and bypassable. Plus the D54 oracle-absence probe in **both** the agent container
and the criterion environment, since agent-authored code executes in the latter; `find_spec`
rather than `import`, because importing a module to learn whether it is importable executes
its module-level code inside the sandbox.

Every failure path fail-closed, the probe erroring included. `not_executed` is a failure,
never a pass.

### S7 — Durability · *blocks Phase 0 exit; blocked by S1*

Continuous WAL archiving and base backups to an off-machine target; evidence rows
hash-chained with the head anchored off-machine daily; a restore drill as an executable check.

**"Restore verified" splits in two.** A synthetic drill in CI proves the *mechanism*; only a
drill against the actual off-machine backup proves the *artifact*. The chain re-walk must use
the **JavaScript** implementation — checking a chain the Python encoder wrote, using the Python
encoder, checks nothing — and must assert the walk is **total**: one head, no forks. A chain
check that verifies each link but never checks they form a single path passes on a forked
audit log.

### S8 — Deploy and rollback · *blocks Phase 0 exit*

`docker compose up` serves the API; deploy and rollback both execute and are verified.

### S9 — Phase 1 build · *blocked by S1–S8 and by O1*

`Worker` port and the OpenHands adaptor, pinned by commit SHA; the fifteen numbered boot
assertions (D53); patch validation on the privileged side with the A10 unicode scan; and the
mission-control command surface, which is inspector under D51 and therefore operator-built.

**The OpenHands source read (O5) must precede the containment assertions.** Their premises are
unverified first-hand, and an assertion resting on a *misnamed* config key or event class
reports `passed` while the control it names does nothing — executed, passed, and vacuous. That
is a third outcome the register does not currently name.

---

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
