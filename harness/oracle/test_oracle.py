"""Tests for the oracle boundary. Most run without the image; the slow one needs it.

The controls here are the point of the file. Every refusal in `load.py` gets a test that
plants the condition and asserts the refusal, because a validator nobody has watched
reject anything is a validator that might accept everything.
"""

from __future__ import annotations

import subprocess
import uuid
from typing import Any

import pytest

from harness.oracle import pins
from harness.oracle.load import (
    LOADER_ROLE,
    TIER_PRODUCED,
    LoadRefused,
    _admissibility,
    _validate,
    question_hash,
)
from harness.oracle.points import MINIMUM_POINTS, PHASE0_SCENARIOS, POINTS, scenarios_covered


def _record(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "point_id": "p1",
        "measure_id": "THW",
        "scenario_ref": "ZAM_Urban-3_3_Repair",
        "ego_id": 8,
        "args": [6, 0],
        "kwargs": {},
        "config_overrides": {},
        "mutations": [],
        "tolerance": 1e-2,
        "quantum": 1e-2,
        "status": "ok",
        "value_kind": "defined",
        "value": 2.4,
    }
    base.update(over)
    return base


def _report(*records: dict[str, Any], findings: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "environment": {"oracle_commit_sha": pins.ORACLE_COMMIT_SHA},
        "findings": findings or [],
        "records": list(records),
    }


# --------------------------------------------------------------------- the point set


def test_point_ids_are_unique() -> None:
    ids = [p.point_id for p in POINTS]
    assert len(ids) == len(set(ids))


def test_point_set_clears_its_own_vacuity_floor() -> None:
    assert len(POINTS) >= MINIMUM_POINTS


def test_phase0_scenarios_are_all_reached() -> None:
    """The exit criterion names six scenarios. Being able to say so is not covering them."""
    assert PHASE0_SCENARIOS <= scenarios_covered()


def test_every_point_carries_an_oracle_pinned_literal() -> None:
    for p in POINTS:
        if p.expected.kind == "defined":
            assert p.expected.value is not None, p.point_id
        elif p.expected.kind == "infinite":
            assert p.expected.infinite_sign in (-1, 1), p.point_id


def test_ttc_star_and_ttr_are_labelled_as_the_source_labels_them() -> None:
    """Guards the two labels the plan's prose has wrong.

    2.4 comes from `TTCStar`, and 1.25 from `TTR` on the set-based scenario. Recording
    either as `TTC` would mean reproducing a different measure and calling it a pass.
    """
    by_id = {p.point_id: p for p in POINTS}
    assert by_id["ttcstar-base"].measure == "TTCStar"
    assert by_id["ttr-setbased"].measure == "TTR"
    assert by_id["ttr-setbased"].expected.value == 1.25


# ------------------------------------------------------------------- the input hash


def test_question_hash_ignores_the_answer() -> None:
    a = question_hash(_record(value=2.4))
    b = question_hash(_record(value=99.0, value_kind="defined"))
    assert a == b


def test_question_hash_separates_different_questions() -> None:
    assert question_hash(_record(ego_id=8)) != question_hash(_record(ego_id=9))
    assert question_hash(_record(args=[6, 0])) != question_hash(_record(args=[7, 0]))
    assert question_hash(_record(mutations=[])) != question_hash(
        _record(mutations=["remove_static_obstacles"])
    )


# ------------------------------------------------------- every refusal, exercised


def test_validate_accepts_a_clean_extract() -> None:
    assert len(_validate(_report(_record()))) == 1


def test_findings_refuse_the_whole_load() -> None:
    with pytest.raises(LoadRefused, match="findings"):
        _validate(_report(_record(), findings=["point set shrank"]))


def test_a_single_mismatch_refuses_every_row() -> None:
    """Partial loads are the failure mode: 24 of 28 looks like a successful 24."""
    with pytest.raises(LoadRefused, match="pinned literal"):
        _validate(_report(_record(), _record(point_id="p2", status="mismatch")))


def test_an_error_refuses_every_row() -> None:
    with pytest.raises(LoadRefused, match="pinned literal"):
        _validate(_report(_record(point_id="p2", status="error")))


def test_unknown_quantum_is_refused() -> None:
    with pytest.raises(LoadRefused, match="quantum"):
        _validate(_report(_record(quantum=None)))


def test_tolerance_finer_than_the_oracle_rounding_is_refused() -> None:
    with pytest.raises(LoadRefused, match="finer than"):
        _validate(_report(_record(tolerance=1e-9, quantum=1e-2)))


def test_empty_extract_is_refused() -> None:
    with pytest.raises(LoadRefused, match="zero records"):
        _validate(_report())


# --------------------------------------------------------------- D49 admissibility


def test_admissibility_separates_one_point_from_two() -> None:
    report = _admissibility(
        [
            _record(measure_id="TET", point_id="a"),
            _record(measure_id="TET", point_id="b", value=0.9),
            _record(measure_id="TTZ", point_id="c", value=1.05),
            _record(measure_id="TTK", point_id="d", value_kind="infinite", value=None),
        ]
    )
    assert report.measures_with_two_nondegenerate == ("TET",)
    assert report.measures_with_one_nondegenerate == ("TTZ",)
    assert report.degenerate_only == ("TTK",)
    assert report.admissible == ("TET",)


def test_tier_produced_is_p1_and_the_others_are_named_absent() -> None:
    """P3 needs the seeded resampler, which does not exist. The absence is data."""
    assert TIER_PRODUCED == "P1"
    from harness.oracle.load import TIERS_NOT_PRODUCED

    assert "P3" in TIERS_NOT_PRODUCED


def test_loader_role_is_not_the_reading_role() -> None:
    assert LOADER_ROLE != "alfred_criterion"


# ------------------------------------------------------------------ the pins hold


def test_platform_is_amd64_and_the_finding_says_why() -> None:
    assert pins.PLATFORM == "linux/amd64"
    for name, platforms in pins.WHEEL_PLATFORMS_OBSERVED.items():
        for tag in platforms:
            for banned in pins.NO_WHEEL_PLATFORM_SUBSTRINGS:
                assert banned not in tag, f"{name} now ships {tag}; reopen the platform choice"


def test_python_is_below_the_reach_ceiling() -> None:
    """commonroad-reach declares requires_python <3.12. 3.11 is forced, not chosen."""
    major, minor = (int(x) for x in pins.PYTHON_VERSION.split("."))
    assert (major, minor) < (3, 12)


# --------------------------------------------------------------------- integration


def _image_present() -> bool:
    return (
        subprocess.run(
            ["docker", "image", "inspect", pins.IMAGE_TAG],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


@pytest.mark.skipif(not _image_present(), reason="oracle image not built on this host")
def test_the_oracle_agrees_with_its_own_pinned_literals() -> None:
    """The end-to-end control: the oracle re-derives every value the enumeration records.

    This is what makes the point set trustworthy. A wrong ego id or scenario produces a
    number that disagrees with the literal transcribed beside it, and this fails.
    """
    from harness.oracle.run import run_oracle

    result = run_oracle()
    assert result.findings == [], result.findings
    assert result.report["counts"]["error"] == 0
    assert result.report["counts"]["mismatch"] == 0
    assert result.report["counts"]["ok"] >= MINIMUM_POINTS
