# PLAN-M1 — the harness has no type gate and no lint gate

> Historical module work plan — the decision lives in ADR-0029 on main; retained for the O9 review's provenance.

**Module** M1 · **ADR assigned** 0029 · **Base** `main` @ `fa62b4b` · **Branch**
`m1-harness-verification-gate`

The finding: `[tool.ruff].include` (`pyproject.toml:50`) and `[tool.pyright].include`
(`pyproject.toml:97`) both name `src` and `tests` only. `harness/` — the tree that verifies
every other tree — is verified by neither. Two OBSERVER decisions gate the expensive half of
the fix; this plan does everything that does not depend on them and stops at the boundary.

---

## Step 0 — baseline, before anything changes

**What changes:** nothing. Measurement only.

**What is measured:**

- `uv run pytest tests bench harness` — pass/skip/fail counts.
- `uv run ruff check` (product gate, as configured) — violation count.
- `uv run pyright` (product gate, as configured) — error count.
- The doc/lint script row from `_COMMON.md`.
- `uv run ruff check harness` — the claim under test ("No Python files found").
- `uv run pyright harness` — the claim under test (~300 errors).

**Negative control:** none needed; this step asserts nothing. But the baseline itself is the
control for every later step — if a number moves and I did not intend it, I stop.

**What would show it vacuous:** a baseline taken with a venv missing `--all-extras` would
report skips or import errors that are environmental, not real, and would mask a later
regression. Mitigation: `uv sync --frozen --all-extras --dev` before measuring, and assert
`0 skipped`.

---

## Step 1 — prove the gap empirically, not by reading config

**What changes:** nothing in the tree. A planted-defect probe run by hand and reverted.

**Method:** plant `def broken(x: int) -> str: return x` into a `harness/` module, run the two
product gates (`uv run ruff check`, `uv run pyright`), record that both stay green, revert.

**Negative control:** plant the same line into a `src/` module and confirm both gates go red.
Without this, "the gates passed it" could mean the gates are broken everywhere, not that
`harness/` is uncovered. The `src/` arm distinguishes *scoped-out* from *inert*.

**What would show it vacuous:** if the planted line were syntactically inert (e.g. inside a
`TYPE_CHECKING` block, or in a file no config path reaches even in `src/`), both arms would
agree for the wrong reason. Mitigation: plant at module top level in a file that is
demonstrably imported.

---

## Step 2 — classify the pyright errors by kind and count

**What changes:** nothing in the tree. A classification, reported (not committed as a doc
unless the ADR needs it inline).

**Method:** `uv run pyright harness --outputjson`, group by `rule` and by directory, then read
a sample of each group by hand and sort into three buckets:

1. **Volume** — missing annotations on test helpers, `Unknown` leaking from untyped fixtures,
   strict-mode reporting that is noise at this strictness.
2. **Config artefacts** — errors that exist only because `harness/` was never on the path
   (unresolved imports, missing stubs), i.e. they disappear with configuration, not edits.
3. **Real type defects** — a value that cannot be what the signature says it is; the class the
   planted line belongs to.

Bucket 3 is the finding. Buckets 1 and 2 are the cost estimate.

**Negative control:** the planted `def broken` line must land in bucket 3 when the
classification is applied to a run that contains it. A classification that cannot recognise
the one error we know is real is not a classification. I run the classifier over a
planted-defect run and check the planted line is bucketed as a real defect.

**What would show it vacuous:** if every error falls into bucket 1, the classification has
told the observer nothing and the ~300 number is pure annotation debt — which is itself a
finding, and must be reported as such rather than dressed up. Equally vacuous: bucketing by
pyright rule name alone without reading any code, which relabels the counts and adds nothing.

---

## Step 3 — the cheap gate: `ruff check harness`

**What changes:** `pyproject.toml` — extend `[tool.ruff].include` to cover `harness/**/*.py`,
plus whatever per-file-ignores the harness tree honestly needs (it is a test-shaped tree;
`S101` applies as it does for `tests/`). Fix the residual violations if the count is small
and the fixes are mechanical and non-semantic; if any fix would change harness behaviour, it
does not land here — it becomes an O9 item and a reported blocker instead.

The comment at `pyproject.toml:50` is rewritten. It currently rationalizes the gap by
conflating two claims — *D20 forbids agents editing the inspector* and *therefore the
inspector is not checked*. Checking is not editing. The new comment says which trees are
excluded and why, without borrowing D20's authority for a decision D20 did not make.

**Negative control:** Step 5's harness. A `ruff` include that matches nothing reports success
in exactly the same way as a clean tree — this is the ADR-0007 vacuity class, and it is
precisely how the current state hid. So the gate must be *seen red*.

**What would show it vacuous:** `ruff check harness` printing "No Python files found" and
exiting 0 (today's behaviour); or the include landing but every rule that would fire being
added to `per-file-ignores` at the same time, so the gate is green by construction.

---

## Step 4 — pyright: measure and stop

**What changes:** nothing yet. **This is the OBSERVER boundary.**

I produce the classification (Step 2) and the three costed options from the handoff, and I
do not begin bulk fixes. The two decisions held back:

- **OBSERVER-1** — how much of the pyright error set to fix, and at what strictness.
- **OBSERVER-2** — whether raising `harness/` type coverage is itself a D20 crossing.

**Negative control for the fact that I stopped:** `git diff main --stat` must show no edits
under `harness/` other than what the ruff gate strictly required, and no `[tool.pyright]`
include change. The report names the files I deliberately left alone.

---

## Step 5 — the negative control harness: a gate that has been seen red

**What changes:** a new self-testing script, `scripts/lint_harness_gate.py` (inspector
machinery under D20 — an O9 review item, named as such).

**What it does:**

- **Default mode** — asserts the gate is *live*: that `ruff` actually collects a non-zero
  number of files under `harness/`, and that the collected count matches the number of `.py`
  files on disk under `harness/`. This is the D57 vacuity control: a check that scanned zero
  items fails. It is the assertion that would have failed on `main` today.
- **`--self-test` mode** — copies the harness tree to a scratch directory, plants
  `def broken(x: int) -> str: return x` plus a ruff-visible violation into the copy, runs the
  gate against the copy, and asserts it reports **red**. If the planted defect comes back
  green, the self-test fails. The original tree is never mutated.

Both modes are wired into `.github/workflows/gates.yml` in the `integrity` job, alongside the
existing `--self-test` pairs (`lint_verdict_boundary`, `lint_ci_coverage`,
`lint_stage_gates`), which is the established shape for "a lint and its own negative control".

**Negative control:** the `--self-test` mode *is* the negative control. Its own control is
that it must also fail if the plant is not made — i.e. running the gate against an unmodified
copy must come back green, so a self-test that reports red unconditionally is caught.

**What would show it vacuous:** the self-test planting into a directory the gate never
reaches (then it reports red for a reason unrelated to the plant); or asserting only on exit
code without checking that the *planted* violation is the one reported; or the file-count
control comparing a glob to itself.

**F25:** every mode exits 0 or 1. `not_executed` is not a state this script can produce — if
`ruff` cannot be invoked, that is a failure, not a skip.

---

## Step 6 — ADR-0029

**What changes:** `docs/tier1/adr-log.md` gains ADR-0029.

**Content:**

- The gap and its measurement.
- The distinction the `pyproject.toml:50` comment conflated: *D20 forbids agents editing the
  inspector; it does not say the inspector may not be checked.* Checking is a read; editing is
  a write. The comment borrowed D20's authority for a scope decision D20 never made.
- What landed (ruff) and what did not (pyright), and why the second is held.
- **OBSERVER-2 argued both ways, not settled:** editing ~300 sites inside the protected tree
  is the largest inspector patch proposed here — against which, annotations are non-semantic
  and a type gate is the check that would catch an inspector patch that lies.

**Negative control:** the ADR names a falsification condition — what observation would show
the decision wrong.

**What would show it vacuous:** an ADR that records the decision without the counter-argument,
or that quietly settles OBSERVER-2 by writing as though the answer were obvious.

---

## Step 7 — verify, and re-measure against Step 0

`uv run pytest tests bench harness && uv run ruff check && uv run pyright`, plus the doc/lint
row, plus the new gate and its self-test. Every number is compared to Step 0. **If the failure
count moves at all, I stop and report** rather than fixing forward.

---

## Commit units

1. `scripts/lint_harness_gate.py` + gates.yml wiring — the gate and its negative control.
2. `pyproject.toml` ruff include + comment rewrite + any mechanical violation fixes.
3. `docs/tier1/adr-log.md` — ADR-0029.

Order matters: the gate lands *before* the include change, so the repository contains a commit
in which the control demonstrably fails against the unfixed tree.

## Out of scope, deliberately

- `harness/patch/` — owned by a live agent on `bionic/protected-set`. Not touched.
- `harness/containment/` and `harness/selftest/` beyond what the ruff gate strictly requires —
  M2 and M3 own those. Files left to them are named in the report.
- Any pyright error fix. Held on OBSERVER-1.
- `docs/tier2/execution-order.md`, `docs/tier1/technology-selection-records.md`, Tier 0 —
  `owner: human`.
