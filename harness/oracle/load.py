"""Carries oracle values across the boundary as data, and refuses when they are not clean.

The oracle's code never crosses (D54). What crosses is a JSON document, and this module
treats it as what it is: structured input from another environment, validated before any
of it reaches a table. Nothing here imports CriMe, and nothing here can.

------------------------------------------------------------------ what it refuses, and why

**Any finding, any mismatch, any error — the whole load is refused, not the offending
rows.** Partial loads are the failure mode that matters: a run in which four points
errored and twenty-four loaded looks like a successful load of twenty-four points, and the
four missing ones are invisible at every later stage. The extract is one artifact and it
is accepted or rejected whole.

**A point whose quantum could not be read from the oracle's source.** The schema enforces
`tolerance >= quantum`, and against an unknown quantum that constraint passes while
checking nothing — the vacuity class ADR-0007 names. A tolerance compared to a guess is
not a tolerance.

**A connection holding the reading role.** `alfred_criterion` reads held-out values at
verdict time and has SELECT and no INSERT for a reason: a process that can both read the
answers and write them can make any verdict come true. If this module is ever run on that
connection the grant would refuse it anyway — the assertion is here so the failure names
the boundary instead of surfacing as a permissions error nobody reads.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import psycopg

from harness.acs.acs1 import acs_sha256
from harness.oracle.pins import ORACLE_NAME

# Domain separation, as everywhere else a digest is taken. The input hash answers "what is
# this a value OF", so its preimage is the question and never the answer.
QUESTION_RECORD_TYPE = "alfred.oracle.question.v1"

# The role that owns the heldout schema. `alfred_criterion` is SELECT-only there.
LOADER_ROLE = "alfred_migrator_heldout"

# D49. Every point produced by this stage is a constant pinned by the oracle itself, which
# is tier P1. P2 and P3 are not produced here: P2 needs an equivariance relation the
# oracle pins, and P3 needs the seeded resampler, which does not exist and has never been
# specified. Recorded as a constant so the absence is legible rather than implied.
TIER_PRODUCED = "P1"
TIERS_NOT_PRODUCED = ("P2", "P3", "P4", "P5")


class LoadRefused(RuntimeError):
    """The extract did not qualify. Nothing was written."""


@dataclass(frozen=True)
class LoadReport:
    rows_written: int
    measures: int
    # Measures holding at least two non-degenerate points. D49's admissibility test: a
    # measure with one pinned value has no second point to hold out, so it cannot support
    # the visible/held-out split the autonomy ladder rests on.
    measures_with_two_nondegenerate: tuple[str, ...]
    measures_with_one_nondegenerate: tuple[str, ...]
    degenerate_only: tuple[str, ...]

    @property
    def admissible(self) -> tuple[str, ...]:
        return self.measures_with_two_nondegenerate


def question_hash(record: dict[str, Any]) -> str:
    """Content address of the question, not of the answer.

    A perturbed slice and the slice it came from must be distinguishable without storing
    either, which is what the heldout schema's `input_hash` column is for. Everything that
    changes what is being asked goes in; nothing that is part of the reply does.
    """
    return acs_sha256(
        QUESTION_RECORD_TYPE,
        {
            "args": [int(a) for a in record["args"]],
            "config_overrides": {k: str(v) for k, v in sorted(record["config_overrides"].items())},
            "ego_id": int(record["ego_id"]),
            "kwargs": {k: str(v) for k, v in sorted(record["kwargs"].items())},
            "measure_id": record["measure_id"],
            "mutations": list(record["mutations"]),
            "scenario_ref": record["scenario_ref"],
        },
    )


def _validate(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings = list(report.get("findings", []))
    if findings:
        raise LoadRefused(f"extract carries findings, nothing loaded: {findings}")

    records = list(report.get("records", []))
    if not records:
        raise LoadRefused("extract holds zero records")

    bad = [r["point_id"] for r in records if r.get("status") != "ok"]
    if bad:
        raise LoadRefused(
            f"{len(bad)} of {len(records)} points did not agree with the oracle's own "
            f"pinned literal or errored; the extract is refused whole: {bad[:8]}"
        )

    unknown_quantum = [r["point_id"] for r in records if r.get("quantum") is None]
    if unknown_quantum:
        raise LoadRefused(
            "quantum could not be read from the oracle's source for: "
            f"{unknown_quantum}. tolerance >= quantum would pass without checking anything."
        )

    unresolvable = [
        r["point_id"] for r in records if float(r["tolerance"]) < float(r["quantum"])
    ]
    if unresolvable:
        raise LoadRefused(
            "tolerance is finer than the oracle's own rounding for: "
            f"{unresolvable}. Such a point cannot distinguish a correct answer from the "
            "next representable one."
        )
    return records


def _admissibility(records: list[dict[str, Any]]) -> LoadReport:
    by_measure: dict[str, int] = {}
    seen: dict[str, int] = {}
    for r in records:
        m = r["measure_id"]
        seen[m] = seen.get(m, 0) + 1
        if r["value_kind"] == "defined":
            by_measure[m] = by_measure.get(m, 0) + 1

    two = tuple(sorted(m for m, n in by_measure.items() if n >= 2))
    one = tuple(sorted(m for m, n in by_measure.items() if n == 1))
    none = tuple(sorted(m for m in seen if by_measure.get(m, 0) == 0))
    return LoadReport(
        rows_written=len(records),
        measures=len(seen),
        measures_with_two_nondegenerate=two,
        measures_with_one_nondegenerate=one,
        degenerate_only=none,
    )


def load(
    conn: psycopg.Connection[Any],
    report: dict[str, Any],
    *,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    require_loader_role: bool = True,
) -> LoadReport:
    records = _validate(report)
    oracle_sha = report["environment"]["oracle_commit_sha"]

    with conn.cursor() as cur:
        if require_loader_role:
            cur.execute("SELECT current_user")
            row = cur.fetchone()
            current = row[0] if row else None
            if current != LOADER_ROLE:
                raise LoadRefused(
                    f"connected as {current!r}; held-out values are written only by "
                    f"{LOADER_ROLE!r}. The role that reads the answers must not write them."
                )

        now = datetime.now(UTC)
        for r in records:
            input_hash = question_hash(r)
            cur.execute(
                "SELECT COALESCE(MAX(value_version), 0) FROM heldout.reference_value "
                "WHERE org_id = %s AND project_id = %s AND measure_id = %s "
                "AND input_hash = %s",
                (org_id, project_id, r["measure_id"], input_hash),
            )
            fetched = cur.fetchone()
            next_version = (fetched[0] if fetched else 0) + 1
            cur.execute(
                "INSERT INTO heldout.reference_value ("
                " id, org_id, project_id, schema_version, created_at, measure_id,"
                " scenario_ref, input_hash, value_version, value_kind, value,"
                " infinite_sign, reason_name, tolerance, quantum, provenance_tier,"
                " oracle_name, oracle_commit_sha"
                ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    uuid.uuid4(), org_id, project_id, 1, now, r["measure_id"],
                    r["scenario_ref"], input_hash, next_version, r["value_kind"],
                    r.get("value"), r.get("infinite_sign"), r.get("reason_name"),
                    float(r["tolerance"]), float(r["quantum"]), TIER_PRODUCED,
                    ORACLE_NAME, oracle_sha,
                ),
            )
    return _admissibility(records)
