"""Verdict composition, with the two collapses that would make the number meaningless.

**How this suite would be shown vacuous** (D57). The three-valued tests would all pass
against a composer that returned `indeterminate` unconditionally, so `test_both_halves_
passing_is_a_pass` and `test_held_out_mismatch_is_a_fail` are the controls that keep the
other value reachable. And the whole file would be satisfied by a `grade_point` that
returned `matched=False` always, which is why the tolerance tests come in pairs.

Two tests carry more weight than the rest:

- `test_unreachable_held_out_is_never_a_pass_on_visible_alone` is F4. A held-out check
  that could not run has not passed, and reporting the visible result when the held-out
  half is unavailable produces exactly the number the autonomy gates must not read.
- `test_held_out_values_never_enter_the_environment` asserts the structural decision: the
  subprocess computes and the runner compares, so nothing knowing an expected value ever
  runs beside the code being measured.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

from harness.criterion.execute import REPORT_FILENAME
from harness.criterion.materialize import MaterializationSpec
from harness.criterion.runner import (
    HARVEST_FILENAME,
    CriterionError,
    CriterionRunner,
    CriterionSpec,
    HeldOutPoint,
    evaluate,
    grade_point,
)
from harness.db.cluster import SUPERUSER, ThrowawayCluster
from harness.evidence.store import EvidenceStore

ORG = uuid.UUID("018f0000-0000-7000-8000-000000000011")
PROJECT = uuid.UUID("018f0000-0000-7000-8000-000000000012")


def _point(**overrides: object) -> HeldOutPoint:
    base: dict[str, object] = {
        "measure_id": "ttc",
        "input_hash": "a" * 64,
        "value_version": 1,
        "value_kind": "defined",
        "value": 2.4,
        "tolerance": 0.01,
        "quantum": 0.01,
        "provenance_tier": "P1",
    }
    base.update(overrides)
    return HeldOutPoint(**base)  # pyright: ignore[reportArgumentType]


# ------------------------------------------------------------------------- grading


def test_value_inside_tolerance_matches() -> None:
    assert grade_point(_point(), {"kind": "defined", "value": 2.405}).matched


def test_value_outside_tolerance_does_not_match() -> None:
    assert not grade_point(_point(), {"kind": "defined", "value": 2.42}).matched


def test_zero_against_an_undefined_reference_is_a_mismatch() -> None:
    """The E1/E7 collapse, caught because both sides carry their arm.

    A comparison that coerced both to floats would score a `0.0` against an undefined
    reference as a near miss, and "the quantity is undefined" is not a small error from
    zero — it is a different claim.
    """
    reference = _point(value_kind="undefined", value=None, reason_name="PARALLEL_PATHS")
    assert not grade_point(reference, {"kind": "defined", "value": 0.0}).matched


def test_infinite_sign_is_compared() -> None:
    reference = _point(value_kind="infinite", value=None, infinite_sign=1)
    assert grade_point(reference, {"kind": "infinite", "sign": 1}).matched
    assert not grade_point(reference, {"kind": "infinite", "sign": -1}).matched


def test_nan_never_matches() -> None:
    assert not grade_point(_point(), {"kind": "defined", "value": float("nan")}).matched


def test_untagged_output_does_not_match() -> None:
    assert not grade_point(_point(), 2.4).matched
    assert not grade_point(_point(), None).matched


# --------------------------------------------------------------------- evaluation


def _spec(*, visible_exit: int, visible_report: object, harvest: object | None) -> CriterionSpec:
    return CriterionSpec(
        criterion_ref="crime.ttc.v1",
        criterion_version=1,
        materialization=MaterializationSpec(
            candidate_paths=("src/ttc.py",), trusted_paths=("run_visible.py", "run_harvest.py")
        ),
        visible_command=(sys.executable, "run_visible.py"),
        harvest_command=(sys.executable, "run_harvest.py"),
        timeout_s=30,
    )


def _trees(
    tmp_path: Path,
    *,
    visible_exit: int,
    visible_report: object,
    harvest: object | None,
    harvest_exit: int = 0,
) -> tuple[Path, Path, Path]:
    candidate = tmp_path / "candidate"
    trusted = tmp_path / "trusted"
    (candidate / "src").mkdir(parents=True)
    trusted.mkdir()
    (candidate / "src/ttc.py").write_text("def ttc() -> float:\n    return 2.4\n", encoding="utf-8")

    (trusted / "run_visible.py").write_text(
        "import pathlib, sys\n"
        f"pathlib.Path({REPORT_FILENAME!r}).write_text({json.dumps(visible_report)!r})\n"
        f"sys.exit({visible_exit})\n",
        encoding="utf-8",
    )
    harvest_body = (
        ""
        if harvest is None
        else f"pathlib.Path({HARVEST_FILENAME!r}).write_text({json.dumps(harvest)!r})\n"
    )
    (trusted / "run_harvest.py").write_text(
        "import pathlib, sys\n"
        + harvest_body
        + f"pathlib.Path({REPORT_FILENAME!r}).write_text("
        f"{json.dumps({'checks_run': 1, 'checks_passed': 1})!r})\n"
        f"sys.exit({harvest_exit})\n",
        encoding="utf-8",
    )
    return candidate, trusted, tmp_path / "env"


def test_both_halves_passing_is_a_pass(tmp_path: Path) -> None:
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=0,
        visible_report={"checks_run": 3, "checks_passed": 3, "score": 1.0},
        harvest={"ttc": {"kind": "defined", "value": 2.4}},
    )
    result = evaluate(
        spec=_spec(visible_exit=0, visible_report=None, harvest=None),
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(_point(),),
    )
    assert result.verdict == "pass"
    assert result.held_out_result == "pass"
    assert result.held_out_provenance_tier == "P1"
    assert result.score == 1.0


def test_held_out_mismatch_is_a_fail(tmp_path: Path) -> None:
    """The SpecBench shape: visible green, held-out red, no exploit anywhere."""
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=0,
        visible_report={"checks_run": 3, "checks_passed": 3, "score": 1.0},
        harvest={"ttc": {"kind": "defined", "value": 9.9}},
    )
    result = evaluate(
        spec=_spec(visible_exit=0, visible_report=None, harvest=None),
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(_point(),),
    )
    assert result.verdict == "fail"
    assert result.held_out_result == "fail"


def test_unreachable_held_out_is_never_a_pass_on_visible_alone(tmp_path: Path) -> None:
    """F4, and the single most important line in this file.

    Visible criteria all green. If the composer reported that result while the held-out
    half was unavailable, every merge gate would read a number computed from the half the
    agent retries against.
    """
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=0,
        visible_report={"checks_run": 3, "checks_passed": 3, "score": 1.0},
        harvest={"ttc": {"kind": "defined", "value": 2.4}},
    )
    result = evaluate(
        spec=_spec(visible_exit=0, visible_report=None, harvest=None),
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(),
        held_out_available=False,
    )
    assert result.verdict == "indeterminate"
    assert result.held_out_result is None
    assert result.indeterminate_reason is not None
    assert "F4" in result.indeterminate_reason


def test_visible_failure_is_a_fail_and_skips_the_harvest(tmp_path: Path) -> None:
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=1,
        visible_report={"checks_run": 3, "checks_passed": 1, "score": 0.33},
        harvest={"ttc": {"kind": "defined", "value": 2.4}},
    )
    result = evaluate(
        spec=_spec(visible_exit=1, visible_report=None, harvest=None),
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(_point(),),
    )
    assert result.verdict == "fail"
    assert result.harvest is None


def test_a_criterion_that_did_not_run_is_indeterminate(tmp_path: Path) -> None:
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=0,
        visible_report={"checks_run": 0, "checks_passed": 0},
        harvest={"ttc": {"kind": "defined", "value": 2.4}},
    )
    result = evaluate(
        spec=_spec(visible_exit=0, visible_report=None, harvest=None),
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(_point(),),
    )
    assert result.verdict == "indeterminate"


def test_a_task_without_a_held_out_point_is_refused(tmp_path: Path) -> None:
    """D49: a task the visible half alone would accept is not schedulable."""
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=0,
        visible_report={"checks_run": 1, "checks_passed": 1},
        harvest={},
    )
    with pytest.raises(CriterionError, match="not schedulable"):
        evaluate(
            spec=_spec(visible_exit=0, visible_report=None, harvest=None),
            candidate_root=candidate,
            trusted_root=trusted,
            workspace=workspace,
            held_out_points=(),
        )


def test_held_out_values_never_enter_the_environment(tmp_path: Path) -> None:
    """The structural decision, asserted rather than described.

    The harvest command reads every file in its own directory and reports whether the
    reference value appears anywhere. It must not. A stub that read an injected
    expected-value file and returned it would pass every held-out point with a clean
    transcript, which is the D50 delegation failure one layer in.

    The probe skips its own source, and that exclusion is the whole reason this test is
    written this way: the first version scanned everything, found the sentinel in the
    comparison literal it was itself compiled from, and reported a leak. A probe that
    reads its own source measures the probe.
    """
    sentinel = "2.4071331"
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=0,
        visible_report={"checks_run": 1, "checks_passed": 1},
        harvest=None,
    )
    (trusted / "run_harvest.py").write_text(
        "import json, pathlib, sys\n"
        "seen = ''\n"
        "for p in sorted(pathlib.Path('.').rglob('*')):\n"
        "    if p.is_file() and p.name != 'run_harvest.py':\n"
        "        seen += p.read_text(errors='replace')\n"
        f"pathlib.Path({HARVEST_FILENAME!r}).write_text(json.dumps("
        f"{{'ttc': {{'kind': 'defined', 'value': {sentinel}}}, "
        f"'leaked': {sentinel!r} in seen}}))\n"
        f"pathlib.Path({REPORT_FILENAME!r}).write_text(json.dumps("
        "{'checks_run': 1, 'checks_passed': 1}))\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    (candidate / "src/ttc.py").write_text("VALUE = 1\n", encoding="utf-8")
    result = evaluate(
        spec=_spec(visible_exit=0, visible_report=None, harvest=None),
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(_point(value=float(sentinel)),),
    )
    harvested = json.loads((workspace / HARVEST_FILENAME).read_text(encoding="utf-8"))
    assert harvested["leaked"] is False, "the reference value was readable inside the environment"
    # The control: the grading still happened, outside, and reached a verdict. Without
    # this the test would pass against an `evaluate` that never ran the harvest at all.
    assert result.verdict == "pass"


def test_a_do_nothing_run_fails_and_is_not_indeterminate(tmp_path: Path) -> None:
    """The null-agent floor's shape, asserted here so the runner has no branch for it.

    Score exactly zero **and** verdict `fail`. If a do-nothing run were `indeterminate` it
    would leave the merge-rate denominator, and merge rate would be inflated by exactly
    the runs that most deserve to depress it. The full floor suite is S4's; this is the
    part the composer owns.
    """
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=1,
        visible_report={"checks_run": 3, "checks_passed": 0, "score": 0.0},
        harvest={},
    )
    result = evaluate(
        spec=_spec(visible_exit=1, visible_report=None, harvest=None),
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(_point(),),
    )
    assert result.verdict == "fail"
    assert result.score == 0.0
    assert result.indeterminate_reason is None


# --------------------------------------------------------------------- the runner


@pytest.mark.db
def test_fetch_reads_the_highest_version(cluster: ThrowawayCluster) -> None:
    """A corrected reference value is a new row, never an UPDATE.

    Reading the maximum is what makes the correction take effect without making last
    week's verdict unreproducible: the superseded row is still there.
    """
    input_hash = uuid.uuid4().hex * 2
    with psycopg.connect(cluster.url(SUPERUSER), autocommit=True) as admin, admin.cursor() as cur:
        for version, value in ((1, 2.0), (2, 2.4)):
            cur.execute(
                "INSERT INTO heldout.reference_value "
                "(id, org_id, project_id, schema_version, created_at, measure_id, "
                " scenario_ref, input_hash, value_version, value_kind, value, tolerance, "
                " quantum, provenance_tier, oracle_name, oracle_commit_sha) "
                "VALUES (%s, %s, %s, 1, now(), 'ttc', 'ZAM_Urban-3_3_Repair', %s, %s, "
                "        'defined', %s, 0.01, 0.01, 'P1', 'commonroad-crime', '60bebed')",
                (uuid.uuid4(), ORG, PROJECT, input_hash, version, value),
            )

    with psycopg.connect(cluster.url("alfred_criterion")) as conn:
        points = CriterionRunner(conn).fetch_held_out(
            org_id=ORG, project_id=PROJECT, measure_ids=("ttc",), input_hash=input_hash
        )
    assert len(points) == 1
    assert points[0].value_version == 2
    assert points[0].value == 2.4


@pytest.mark.db
def test_verdict_is_written_and_chained(cluster: ThrowawayCluster, tmp_path: Path) -> None:
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=0,
        visible_report={"checks_run": 2, "checks_passed": 2, "score": 1.0},
        harvest={"ttc": {"kind": "defined", "value": 2.4}},
    )
    spec = _spec(visible_exit=0, visible_report=None, harvest=None)
    evaluation = evaluate(
        spec=spec,
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(_point(),),
    )
    chain = f"verdict-{uuid.uuid4().hex[:8]}"
    with psycopg.connect(cluster.url("alfred_criterion")) as conn:
        runner = CriterionRunner(conn)
        appended = runner.record(
            evaluation=evaluation,
            chain_id=chain,
            org_id=ORG,
            project_id=PROJECT,
            task_id=uuid.uuid4(),
            attempt_id=uuid.uuid4(),
            spec=spec,
        )
        conn.commit()
        report = EvidenceStore(conn).verify_chain(table="verdict", chain_id=chain)

    assert appended.prev_sha256 is None
    assert report.length == 1
    assert report.total


@pytest.mark.db
def test_the_verdict_body_carries_no_reference_value(
    cluster: ThrowawayCluster, tmp_path: Path
) -> None:
    """Class labels and a comparison detail, never the expected value.

    The verdict row is readable by roles the agent's context is assembled from, so a
    reference value written into it would leave the held-out half by a route no network
    policy and no grant closes.
    """
    candidate, trusted, workspace = _trees(
        tmp_path,
        visible_exit=0,
        visible_report={"checks_run": 2, "checks_passed": 2, "score": 1.0},
        harvest={"ttc": {"kind": "defined", "value": 9.9}},
    )
    spec = _spec(visible_exit=0, visible_report=None, harvest=None)
    evaluation = evaluate(
        spec=spec,
        candidate_root=candidate,
        trusted_root=trusted,
        workspace=workspace,
        held_out_points=(_point(),),
    )
    chain = f"verdict-{uuid.uuid4().hex[:8]}"
    with psycopg.connect(cluster.url("alfred_criterion")) as conn:
        CriterionRunner(conn).record(
            evaluation=evaluation,
            chain_id=chain,
            org_id=ORG,
            project_id=PROJECT,
            task_id=uuid.uuid4(),
            attempt_id=uuid.uuid4(),
            spec=spec,
        )
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("SELECT body::text FROM evidence.verdict WHERE chain_id = %s", (chain,))
            row = cur.fetchone()

    assert row is not None
    assert "2.4" not in str(row[0])
