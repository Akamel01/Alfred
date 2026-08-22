"""Compose one verdict, and keep the held-out half out of the environment that runs.

**The structural decision in this module, stated first because it is easy to miss.**
Held-out reference values are injected "at verdict time", and the obvious reading of
that is to write them into the criterion environment so the criterion can assert against
them. That reading is wrong, and it is wrong in the way this whole architecture exists to
prevent: **agent-authored code executes in the criterion environment.** A held-out value
placed there is a value the code under test can read and return, and a stub doing exactly
that passes every held-out point with a clean transcript and no dishonesty anywhere in
the loop — the D50 delegation failure, one layer in.

So the split is: **the subprocess computes, the runner compares.** The held-out command
is a *harvest* — it produces the candidate's outputs and asserts nothing. The comparison
against the reference values happens in this process, which holds the `alfred_criterion`
credential and sits outside the environment (A1). Nothing that knows an expected value
ever runs beside the code being measured.

The visible criterion is different and may assert inside the subprocess: visible values
are legitimately in agent context, which is the entire distinction D49 rests on.

**Three-valued composition, and the row that most wants to be got wrong.** F4 — the
held-out schema unreachable at verdict time — is `indeterminate`, **never a `pass` on
visible criteria alone.** A held-out check that could not run has not passed, and a
harness that reports the visible result when the held-out half is unavailable reports
exactly the number the gates must not read.

**There is no `patch is None` branch here, deliberately.** A do-nothing run takes the
same path as every other run and fails on the merits, scoring zero. Short-circuiting it
would make the null-agent floor a code path rather than a measurement, and F3 — the
floor run plus a collection-forcing `conftest.py` — has to traverse the identical code to
test A1's claim at all.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

import psycopg

from harness.criterion.execute import Execution, ExecutionOutcome, execute
from harness.criterion.materialize import (
    Materialization,
    MaterializationSpec,
    materialize,
)
from harness.evidence.store import Appended, EvidenceStore
from harness.verdicts import Verdict

HARVEST_FILENAME: Final = "criterion_harvest.json"

type VerdictValue = Verdict


class CriterionError(RuntimeError):
    """The criterion could not be run as specified. Never a verdict."""


@dataclass(frozen=True)
class HeldOutPoint:
    """One reference value the agent has never seen.

    The tagged arms are the same three `MetricValue` carries. `+inf` is a *defined*
    claim — the event provably never occurs — and it is a different claim from "the
    oracle could not compute this". Collapsing them is how a degenerate case becomes a
    passing test.
    """

    measure_id: str
    input_hash: str
    value_version: int
    value_kind: Literal["defined", "infinite", "undefined"]
    tolerance: float
    quantum: float
    provenance_tier: str
    value: float | None = None
    infinite_sign: int | None = None
    reason_name: str | None = None


@dataclass(frozen=True)
class CriterionSpec:
    """What to build, what to run, and what the held-out half must produce."""

    criterion_ref: str
    criterion_version: int
    materialization: MaterializationSpec
    visible_command: tuple[str, ...]
    harvest_command: tuple[str, ...]
    timeout_s: float


@dataclass(frozen=True)
class PointResult:
    measure_id: str
    matched: bool
    detail: str


@dataclass(frozen=True)
class Evaluation:
    """The verdict and everything it was composed from."""

    verdict: VerdictValue
    score: float | None
    held_out_result: VerdictValue | None
    held_out_provenance_tier: str | None
    indeterminate_reason: str | None
    visible: Execution
    harvest: Execution | None
    point_results: tuple[PointResult, ...]
    manifest: dict[str, str]


# ------------------------------------------------------------------------- grading


def grade_point(point: HeldOutPoint, observed: object) -> PointResult:
    """Compare one harvested output against one reference value, outside the subprocess.

    The observed value carries its own arm, so an implementation returning `0.0` where the
    reference is `Undefined` is a mismatch rather than a near miss. That is the E1/E7
    collapse, and a comparison that coerced both to floats would score it as a small error.
    """
    if not isinstance(observed, dict) or "kind" not in observed:
        return PointResult(point.measure_id, False, "harvest emitted no tagged value")

    kind = observed.get("kind")
    if kind != point.value_kind:
        return PointResult(
            point.measure_id, False, f"expected kind {point.value_kind!r}, observed {kind!r}"
        )

    if point.value_kind == "infinite":
        sign = observed.get("sign")
        matched = sign in (-1, 1, "-", "+") and _sign_of(sign) == point.infinite_sign
        return PointResult(point.measure_id, matched, f"infinite sign {sign!r}")

    if point.value_kind == "undefined":
        reason = observed.get("reason")
        return PointResult(
            point.measure_id, reason == point.reason_name, f"reason {reason!r}"
        )

    raw = observed.get("value")
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        return PointResult(point.measure_id, False, f"value is not a number: {raw!r}")
    value = float(raw)
    if math.isnan(value):
        # A NaN compares false against every bound including itself, so an
        # `abs(...) <= tolerance` test reports a clean miss and says nothing about why.
        return PointResult(point.measure_id, False, "value is NaN")
    if not math.isfinite(value):
        return PointResult(point.measure_id, False, "non-finite value under the defined arm")

    if point.value is None:
        # Unreachable while the table's arm-payload check constraint holds. Raised rather
        # than asserted so that a reference row written around the constraint fails loudly
        # instead of grading against `None`.
        raise CriterionError(f"{point.measure_id}: defined arm carries no value")
    delta = abs(value - point.value)
    return PointResult(
        point.measure_id,
        delta <= point.tolerance,
        f"|Δ| = {delta:.6g} against tolerance {point.tolerance:.6g} (quantum {point.quantum:.6g})",
    )


def _sign_of(sign: object) -> int | None:
    if sign in (1, "+"):
        return 1
    if sign in (-1, "-"):
        return -1
    return None


# ---------------------------------------------------------------------- evaluation


def evaluate(
    *,
    spec: CriterionSpec,
    candidate_root: Path,
    trusted_root: Path,
    workspace: Path,
    held_out_points: tuple[HeldOutPoint, ...],
    held_out_available: bool = True,
) -> Evaluation:
    """Materialize, run both halves, and compose one three-valued verdict.

    `held_out_available=False` is F4 — the schema could not be reached. It is passed in
    rather than inferred from an empty point list, because "no points were configured"
    and "the points could not be read" are different facts and only one of them is a
    harness fault.
    """
    if not held_out_points and held_out_available:
        # D49: every schedulable task carries at least one held-out grading point. A task
        # without one is inadmissible, and admitting it here would let the visible half
        # decide acceptance — which is the calibration failure D33 exists to prevent.
        raise CriterionError(
            f"{spec.criterion_ref} declares no held-out grading point; the task is not schedulable"
        )

    built: Materialization = materialize(
        candidate_root=candidate_root,
        trusted_root=trusted_root,
        spec=spec.materialization,
        destination=workspace,
    )

    visible = execute(root=built.root, command=spec.visible_command, timeout_s=spec.timeout_s)

    if visible.outcome is ExecutionOutcome.DID_NOT_RUN:
        return _indeterminate(built, visible, None, f"visible criterion: {visible.reason}")

    score = visible.report.score if visible.report else None

    if visible.outcome is ExecutionOutcome.FAILED:
        # The held-out half is not run. Not an optimization: a failing candidate has
        # nothing to grade, and running it would put held-out points into the retry loop
        # by way of timing and log volume.
        return Evaluation(
            verdict="fail",
            score=score,
            held_out_result=None,
            held_out_provenance_tier=None,
            indeterminate_reason=None,
            visible=visible,
            harvest=None,
            point_results=(),
            manifest=built.manifest,
        )

    if not held_out_available:
        return _indeterminate(
            built, visible, None, "held-out schema unreachable at verdict time (F4)"
        )

    harvest = execute(root=built.root, command=spec.harvest_command, timeout_s=spec.timeout_s)
    if harvest.outcome is ExecutionOutcome.DID_NOT_RUN:
        return _indeterminate(built, visible, harvest, f"held-out harvest: {harvest.reason}")

    harvested = _read_harvest(built.root)
    if harvested is None:
        return _indeterminate(built, visible, harvest, "held-out harvest produced no readable output")

    results = tuple(
        grade_point(point, harvested.get(point.measure_id)) for point in held_out_points
    )
    held_out_pass = all(result.matched for result in results)

    # The weakest tier present, not the strongest. A task graded by one P1 point and one
    # P4 point is reported at P4: an invariance point fixes a result's shape and never its
    # level, so quoting the stronger tier would overstate what the verdict rests on.
    tier = max((point.provenance_tier for point in held_out_points), default=None)

    return Evaluation(
        verdict="pass" if held_out_pass else "fail",
        score=score,
        held_out_result="pass" if held_out_pass else "fail",
        held_out_provenance_tier=tier,
        indeterminate_reason=None,
        visible=visible,
        harvest=harvest,
        point_results=results,
        manifest=built.manifest,
    )


def _indeterminate(
    built: Materialization, visible: Execution, harvest: Execution | None, reason: str
) -> Evaluation:
    return Evaluation(
        verdict="indeterminate",
        score=None,
        held_out_result=None,
        held_out_provenance_tier=None,
        indeterminate_reason=reason,
        visible=visible,
        harvest=harvest,
        point_results=(),
        manifest=built.manifest,
    )


def _read_harvest(root: Path) -> dict[str, object] | None:
    path = root / HARVEST_FILENAME
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return raw if isinstance(raw, dict) else None


# -------------------------------------------------------------------- the runner


class CriterionRunner:
    """Sole author of verdicts (D5, D39).

    Holds `alfred_criterion` — the only role with any privilege on `heldout`, and it
    holds `SELECT` there and nothing else, so it cannot write the answers it reads. The
    separation from the agent is physical: this module has no import path from anything
    under `src/`, it runs in its own process, and its credential never enters the
    environment the candidate executes in.
    """

    def __init__(self, conn: psycopg.Connection[Any]) -> None:
        self._conn = conn
        self._store = EvidenceStore(conn)

    def fetch_held_out(
        self,
        *,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        measure_ids: tuple[str, ...],
        input_hash: str,
    ) -> tuple[HeldOutPoint, ...]:
        """Read the reference values at their highest version.

        Highest version rather than a fixed one: held-out values are additive at the row
        level, so a corrected value is a new row under a new version and never an
        `UPDATE`. Reading the maximum is what makes the correction take effect without
        making last week's verdict unreproducible — the old row is still there.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT ON (measure_id) measure_id, input_hash, value_version, "
                "       value_kind, value, infinite_sign, reason_name, tolerance, quantum, "
                "       provenance_tier "
                "FROM heldout.reference_value "
                "WHERE org_id = %s AND project_id = %s AND input_hash = %s "
                "  AND measure_id = ANY(%s) "
                "ORDER BY measure_id, value_version DESC",
                (org_id, project_id, input_hash, list(measure_ids)),
            )
            rows = cur.fetchall()

        return tuple(
            HeldOutPoint(
                measure_id=str(row[0]),
                input_hash=str(row[1]),
                value_version=int(row[2]),
                value_kind=str(row[3]),  # pyright: ignore[reportArgumentType]
                value=None if row[4] is None else float(row[4]),
                infinite_sign=None if row[5] is None else int(row[5]),
                reason_name=None if row[6] is None else str(row[6]),
                tolerance=float(row[7]),
                quantum=float(row[8]),
                provenance_tier=str(row[9]),
            )
            for row in rows
        )

    def record(
        self,
        *,
        evaluation: Evaluation,
        chain_id: str,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        attempt_id: uuid.UUID,
        spec: CriterionSpec,
        caused_by: uuid.UUID | None = None,
    ) -> Appended:
        """Append the verdict row. The caller commits; the commit is the commit point.

        The body carries the materialization manifest and the per-point results, because
        a verdict whose inputs cannot be enumerated afterwards is a verdict nobody can
        re-derive — and re-derivability is the product.
        """
        body = {
            "criterion_ref": spec.criterion_ref,
            "criterion_version": spec.criterion_version,
            "manifest": dict(sorted(evaluation.manifest.items())),
            "visible": {
                "outcome": evaluation.visible.outcome.value,
                "exit_code": evaluation.visible.exit_code,
                "duration_ms": evaluation.visible.duration_ms,
            },
            "harvest": None
            if evaluation.harvest is None
            else {
                "outcome": evaluation.harvest.outcome.value,
                "exit_code": evaluation.harvest.exit_code,
                "duration_ms": evaluation.harvest.duration_ms,
            },
            # Class labels and a comparison detail, never the reference value itself. A
            # held-out diagnostic detailed enough to be useful is detailed enough to be
            # optimized against, and this row is readable by roles the agent's context
            # is assembled from.
            "points": [
                {"measure_id": r.measure_id, "matched": r.matched, "detail": r.detail}
                for r in evaluation.point_results
            ],
        }
        return self._store.append_verdict(
            chain_id=chain_id,
            org_id=org_id,
            project_id=project_id,
            task_id=task_id,
            attempt_id=attempt_id,
            criterion_ref=spec.criterion_ref,
            criterion_version=spec.criterion_version,
            verdict=evaluation.verdict,
            score=evaluation.score,
            held_out_result=evaluation.held_out_result,
            held_out_provenance_tier=evaluation.held_out_provenance_tier,
            indeterminate_reason=evaluation.indeterminate_reason,
            body=body,  # pyright: ignore[reportArgumentType]
            schema_version=1,
            caused_by=caused_by,
        )
