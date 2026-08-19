"""The two suites. They are one module because they are each other's vacuity control.

Replace every criterion with `return 0.0` and the floor suite still passes while the
ladder's green rungs fail. Make the runner fail unconditionally and the ladder's red rungs
all pass while the floor suite still passes. Neither suite alone distinguishes a working
runner from a broken one; together they do, and built separately there is a window in
which each looks correct because the other is absent.

The ladder is two-sided for the same reason: a suite of red-expectations is satisfied by a
runner that reds everything, and **the rung just outside tolerance is the only one that
constrains τ's calibration** — pass the far rungs without it and τ could be ten times
looser with nothing noticing.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from harness.criterion.materialize import MaterializationSpec
from harness.criterion.runner import CriterionSpec, Evaluation, HeldOutPoint, evaluate
from harness.selftest import synthetic
from harness.selftest.noise import NoiseFloor, measure_noise_floor

# Chosen once and then checked: `tau_resolves_epsilon` must hold for it, and the ladder
# refuses to run when it does not. A tolerance inside the criterion's own noise floor
# fails correct work at a rate set by summation order.
TOLERANCE: Final = 0.05

# The oracle's rounding, for a criterion that has none of its own. Kept below TOLERANCE so
# the schema's `tolerance >= quantum` relation holds for the synthetic point too.
QUANTUM: Final = 1e-9

Expectation = Literal["green", "red"]


@dataclass(frozen=True)
class Rung:
    name: str
    delta: float
    expected: Expectation
    # The one rung that constrains calibration rather than merely exercising the runner.
    calibrating: bool = False


@dataclass(frozen=True)
class RungResult:
    rung: Rung
    verdict: str
    observed: Expectation
    detail: str

    @property
    def agreed(self) -> bool:
        return self.observed == self.rung.expected


@dataclass(frozen=True)
class LadderResult:
    noise: NoiseFloor
    epsilon: float
    tolerance: float
    results: tuple[RungResult, ...]

    @property
    def disagreements(self) -> tuple[RungResult, ...]:
        return tuple(r for r in self.results if not r.agreed)

    @property
    def green_rungs(self) -> tuple[RungResult, ...]:
        return tuple(r for r in self.results if r.rung.expected == "green")

    @property
    def red_rungs(self) -> tuple[RungResult, ...]:
        return tuple(r for r in self.results if r.rung.expected == "red")


@dataclass(frozen=True)
class FloorResult:
    verdict: str
    score: float | None
    indeterminate_reason: str | None

    @property
    def holds(self) -> bool:
        # Score zero AND verdict fail. A do-nothing run belongs in the merge-rate
        # denominator, so `indeterminate` — which is excluded from both sides — would let
        # a null agent vanish from the measurement rather than score at the floor.
        return self.verdict == "fail" and self.score == 0.0 and self.indeterminate_reason is None


def rungs_for(*, tolerance: float, epsilon: float, reference: float) -> tuple[Rung, ...]:
    return (
        Rung("delta-0", 0.0, "green"),
        Rung("half-tau", tolerance / 2.0, "green"),
        Rung("just-inside", tolerance * (1.0 - epsilon), "green", calibrating=True),
        Rung("just-outside", tolerance * (1.0 + epsilon), "red", calibrating=True),
        Rung("ten-tau", tolerance * 10.0, "red"),
        # O(1) relative to the quantity itself, not to the tolerance: an error the size of
        # the answer. Scaled from the reference so the rung stays meaningful if the
        # synthetic measure is ever changed.
        Rung("order-one", abs(reference), "red"),
    )


def _spec() -> CriterionSpec:
    return CriterionSpec(
        criterion_ref="harness.selftest.synthetic.sum",
        criterion_version=1,
        materialization=MaterializationSpec(
            candidate_paths=("solution.py",),
            trusted_paths=("run_visible.py", "run_harvest.py"),
        ),
        visible_command=("python3", "run_visible.py"),
        harvest_command=("python3", "run_harvest.py"),
        timeout_s=120.0,
    )


def _point() -> HeldOutPoint:
    return HeldOutPoint(
        measure_id=synthetic.MEASURE_ID,
        input_hash="synthetic",
        value_version=1,
        value_kind="defined",
        tolerance=TOLERANCE,
        quantum=QUANTUM,
        provenance_tier="P1",
        value=synthetic.reference_value(),
    )


def _evaluate(delta: float | None) -> Evaluation:
    """One run. `delta is None` means the null agent produced no file at all."""
    with tempfile.TemporaryDirectory(prefix="alfred-selftest-") as tmp:
        base = Path(tmp)
        candidate, trusted, workspace = base / "cand", base / "trust", base / "work"
        if delta is None:
            synthetic.write_null_candidate(candidate)
        else:
            synthetic.write_candidate(candidate, delta=delta)
        synthetic.write_trusted(trusted)
        return evaluate(
            spec=_spec(),
            candidate_root=candidate,
            trusted_root=trusted,
            workspace=workspace,
            held_out_points=(_point(),),
        )


# An evaluator maps a rung's delta to a verdict. `None` means the null agent. It is a
# parameter so the controls below can be committed beside the suite rather than described
# in prose: a suite nobody has watched fail is a suite that might not be able to.
Evaluator = Callable[[float | None], Evaluation]


def always_pass_evaluator(delta: float | None) -> Evaluation:
    """Control. A runner that greens everything must fail every red rung."""
    return _forced("pass", score=1.0)


def always_fail_evaluator(delta: float | None) -> Evaluation:
    """Control. A runner that reds everything must fail every green rung.

    This is the one that matters most: `testing-strategy.md` and `failure-semantics.md`
    both specify the seeded-defect suite entirely in terms of what must go red, and
    nothing in the register rules out a runner that reds unconditionally.
    """
    return _forced("fail", score=0.0)


def constant_zero_evaluator(delta: float | None) -> Evaluation:
    """Control. Every criterion replaced by `return 0.0`.

    The floor suite still passes under this — which is precisely why the floor cannot be
    the only suite. The ladder's green rungs are what notice.
    """
    with tempfile.TemporaryDirectory(prefix="alfred-selftest-zero-") as tmp:
        base = Path(tmp)
        candidate, trusted, workspace = base / "cand", base / "trust", base / "work"
        if delta is None:
            synthetic.write_null_candidate(candidate)
        else:
            candidate.mkdir(parents=True, exist_ok=True)
            candidate.joinpath("solution.py").write_text(
                "def compute() -> float:\n    return 0.0\n"
            )
        synthetic.write_trusted(trusted)
        return evaluate(
            spec=_spec(),
            candidate_root=candidate,
            trusted_root=trusted,
            workspace=workspace,
            held_out_points=(_point(),),
        )


def _forced(verdict: str, *, score: float) -> Evaluation:
    from harness.criterion.execute import CriterionReport, Execution, ExecutionOutcome

    stub = Execution(
        outcome=ExecutionOutcome.PASSED,
        exit_code=0,
        reason=None,
        report=CriterionReport(checks_run=1, checks_passed=1, score=score),
        duration_ms=0,
        stdout="",
        stderr="",
    )
    return Evaluation(
        verdict=verdict,  # type: ignore[arg-type]
        score=score,
        held_out_result=verdict,  # type: ignore[arg-type]
        held_out_provenance_tier="P1",
        indeterminate_reason=None,
        visible=stub,
        harvest=stub,
        point_results=(),
        manifest={},
    )


def run_ladder(
    *, tolerance: float = TOLERANCE, evaluator: Evaluator | None = None
) -> LadderResult:
    run = evaluator or _evaluate
    noise = measure_noise_floor()
    if not noise.tau_resolves_epsilon(tolerance):
        # Not widened here. A tolerance that cannot resolve the criterion's own noise is a
        # finding about the tolerance, and a suite that quietly corrected it would report
        # a calibration it had just invented.
        raise ValueError(
            f"tolerance {tolerance:.6g} is inside the criterion's noise floor "
            f"{noise.spread:.6g}; this is a finding about the tolerance, not about the runner"
        )

    epsilon = noise.epsilon_for(tolerance)
    results: list[RungResult] = []
    for rung in rungs_for(tolerance=tolerance, epsilon=epsilon, reference=noise.reference):
        ev = run(rung.delta)
        observed: Expectation = "green" if ev.verdict == "pass" else "red"
        detail = ev.point_results[0].detail if ev.point_results else (ev.indeterminate_reason or "")
        results.append(RungResult(rung, ev.verdict, observed, detail))

    return LadderResult(noise=noise, epsilon=epsilon, tolerance=tolerance, results=tuple(results))


def run_floor(*, evaluator: Evaluator | None = None) -> FloorResult:
    ev = (evaluator or _evaluate)(None)
    return FloorResult(
        verdict=ev.verdict, score=ev.score, indeterminate_reason=ev.indeterminate_reason
    )
