"""S4. The inspector's inspector, and the controls that stop it reading green for free.

Every claim the two suites make about each other is exercised here against real runs, not
described. The three control tests are the reason the file is worth anything: a passing
suite and a vacuous suite report the same thing, and this project has paid for that lesson
more than once.
"""

from __future__ import annotations

import pytest

from harness.selftest.noise import measure_noise_floor
from harness.selftest.suites import (
    TOLERANCE,
    always_fail_evaluator,
    always_pass_evaluator,
    constant_zero_evaluator,
    run_floor,
    run_ladder,
    rungs_for,
)


# ------------------------------------------------------------------- the noise floor


def test_the_criterion_has_a_measurable_noise_floor() -> None:
    """ε is measured. A criterion reporting zero spread would collapse the two middle
    rungs onto the tolerance boundary and leave τ's calibration untested."""
    noise = measure_noise_floor()
    assert noise.spread > 0.0
    assert noise.samples >= 2


def test_noise_measurement_refuses_a_single_sample() -> None:
    """One sample has no spread and reports perfect precision — the most flattering
    possible wrong answer."""
    with pytest.raises(ValueError, match="at least two samples"):
        measure_noise_floor(samples=1)


def test_the_tolerance_in_force_resolves_the_noise_floor() -> None:
    noise = measure_noise_floor()
    assert noise.tau_resolves_epsilon(TOLERANCE), (
        f"tolerance {TOLERANCE} is inside the noise floor {noise.spread}"
    )


def test_a_tolerance_inside_the_noise_floor_is_refused_not_widened() -> None:
    """A τ that cannot resolve ε is a finding about τ. A suite that silently corrected it
    would report a calibration it had just invented."""
    with pytest.raises(ValueError, match="finding about the tolerance"):
        run_ladder(tolerance=1e-6)


# ------------------------------------------------------------------------ the shape


def test_the_ladder_is_two_sided() -> None:
    noise = measure_noise_floor()
    rungs = rungs_for(
        tolerance=TOLERANCE, epsilon=noise.epsilon_for(TOLERANCE), reference=noise.reference
    )
    assert sum(1 for r in rungs if r.expected == "green") == 3
    assert sum(1 for r in rungs if r.expected == "red") == 3


def test_exactly_one_green_and_one_red_rung_constrain_calibration() -> None:
    """The rungs just inside and just outside tolerance are the only two that say
    anything about where τ actually is. Without them τ could be ten times looser and
    every other rung would still agree."""
    noise = measure_noise_floor()
    rungs = rungs_for(
        tolerance=TOLERANCE, epsilon=noise.epsilon_for(TOLERANCE), reference=noise.reference
    )
    calibrating = [r for r in rungs if r.calibrating]
    assert len(calibrating) == 2
    assert {r.expected for r in calibrating} == {"green", "red"}


# ------------------------------------------------------------------ the suites hold


def test_the_ladder_agrees_at_every_rung() -> None:
    result = run_ladder()
    assert result.disagreements == (), [
        (r.rung.name, r.rung.expected, r.observed, r.detail) for r in result.disagreements
    ]


def test_the_null_agent_floor_scores_zero_and_fails() -> None:
    """Never `indeterminate`. That value is excluded from the merge rate on both sides,
    so a do-nothing run recorded as indeterminate leaves the denominator instead of
    landing in it at the floor."""
    result = run_floor()
    assert result.verdict == "fail"
    assert result.score == 0.0
    assert result.indeterminate_reason is None
    assert result.holds


def test_a_missing_candidate_file_is_the_candidates_failure_not_the_harness_fault() -> None:
    """The defect this suite found on its first run. `materialize` used to raise on an
    absent candidate path, which a caller maps to a harness fault, which maps to
    `indeterminate`. ADR-0015."""
    from harness.criterion.materialize import Materialization

    assert "missing_candidate_paths" in Materialization.__dataclass_fields__


# ------------------------------------------------------------------- the controls


def test_control_a_runner_that_greens_everything_is_caught_by_the_red_rungs() -> None:
    result = run_ladder(evaluator=always_pass_evaluator)
    assert all(not r.agreed for r in result.red_rungs)
    assert not run_floor(evaluator=always_pass_evaluator).holds


def test_control_a_runner_that_reds_everything_is_caught_only_by_the_green_rungs() -> None:
    """The asymmetry is the argument for two-sidedness. A red-only suite is satisfied by
    a runner that fails unconditionally — and the floor suite is *fooled* by it, passing
    cleanly, which is why neither suite may be owned without the other."""
    result = run_ladder(evaluator=always_fail_evaluator)
    assert all(not r.agreed for r in result.green_rungs)
    assert all(r.agreed for r in result.red_rungs)
    assert run_floor(evaluator=always_fail_evaluator).holds


def test_control_every_criterion_returning_zero_passes_the_floor_and_fails_the_ladder() -> None:
    """The mutual vacuity control, stated in the plan and demonstrated here."""
    assert run_floor(evaluator=constant_zero_evaluator).holds
    result = run_ladder(evaluator=constant_zero_evaluator)
    assert all(not r.agreed for r in result.green_rungs)
