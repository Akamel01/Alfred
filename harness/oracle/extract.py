"""Runs INSIDE the oracle image. Computes what CriMe says, and nothing else.

This is the only Alfred-authored code that ever executes in the same process as the
oracle, and it is built into the image rather than mounted (see the Dockerfile) so that a
run cannot be handed different code. It imports nothing from Alfred: no `src`, no
`harness`, no shared package. Its output is a JSON document on stdout and in /out.

Three things it does that are easy to get wrong and expensive to get wrong quietly:

**NaN is mapped to `undefined`, never to a number.** CriMe returns NaN for at least one
pinned case. Alfred's edge-case specification forbids NaN as an output anywhere, and the
dangerous coercion is the silent one — a NaN written into a Double column compares false
against everything, so a criterion measuring against it can never pass and never says why.

**The quantum is read from the oracle's source, not assumed.** CriMe rounds every measure
through `int_round(x, n)`, whose quantum is 10**-n, and n varies by measure. The heldout
schema enforces `tolerance >= quantum` — a constraint that passes vacuously against a
wrong quantum. Where no rounding call is found the quantum is reported as null and the
loader refuses the point, because a tolerance compared against an unknown quantum is not
a check.

**Every point carries its own agreement with the oracle's pinned literal.** A point whose
computed value disagrees with the literal transcribed beside it is a transcription defect
in the point set — wrong ego id, wrong scenario, wrong argument — and it is reported as
`mismatch`, not silently loaded. See points.py.
"""

from __future__ import annotations

import importlib
import inspect
import json
import math
import os
import re
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from points import MINIMUM_POINTS, PHASE0_SCENARIOS, POINTS, Point, scenarios_covered

SRC = Path("/oracle/src")
OUT = Path(os.environ.get("ORACLE_OUT", "/out"))

# `int_round(value, n)` — n is a count of decimal places, so the quantum is 10**-n. The
# default in CriMe's signature is 1; a bare `int_round(x)` therefore rounds to 0.1.
_INT_ROUND = re.compile(r"int_round\s*\(\s*[^,()]*(?:\([^()]*\))?[^,()]*(?:,\s*(\d+))?\s*\)")


def _resolved_environment() -> dict[str, Any]:
    """What this image actually is, read from the image rather than from the pins.

    The pins say what was asked for. This says what arrived. They are compared outside;
    recording only one of them is how a rebuild that resolved differently goes unnoticed.
    """
    head = subprocess.run(
        ["git", "-C", str(SRC), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    resolved = Path("/oracle/resolved.txt")
    return {
        "oracle_commit_sha": head,
        "python_version": sys.version.split()[0],
        "platform": f"{os.uname().sysname}/{os.uname().machine}",
        "resolved_packages": sorted(resolved.read_text().split()) if resolved.exists() else [],
    }


def _measure_class(name: str) -> type:
    module = importlib.import_module("commonroad_crime.measure")
    cls = getattr(module, name, None)
    if cls is None:  # WTTR is not re-exported from the package root.
        for sub in ("time.wttr", "time.ttce"):
            try:
                cls = getattr(importlib.import_module(f"commonroad_crime.measure.{sub}"), name)
                break
            except (ImportError, AttributeError):
                continue
    if cls is None:
        raise LookupError(f"measure class not found: {name}")
    return cls


def _quantum_for(cls: type) -> tuple[float | None, str]:
    """Coarsest rounding the measure's own source applies, as a quantum.

    Coarsest rather than finest: a measure rounding to 0.01 on one branch and 0.1 on
    another can return a value only accurate to 0.1, and a tolerance sized for the finer
    branch would accept a wrong answer on the coarser one. Taking the maximum is the
    conservative direction and the only one that is safe to be wrong in.
    """
    try:
        source = inspect.getsource(inspect.getmodule(cls))  # type: ignore[arg-type]
    except (OSError, TypeError):
        return None, "source_unavailable"
    decimals = [int(m) if m else 1 for m in _INT_ROUND.findall(source)]
    if not decimals:
        return None, "no_rounding_call_found"
    return 10.0 ** -min(decimals), f"int_round decimals={sorted(set(decimals))}"


def _build_config(point: Point) -> Any:
    from commonroad_crime.data_structure.configuration import CriMeConfiguration

    config = CriMeConfiguration()
    # The scenario corpus ships inside the oracle repository, so the path is a property of
    # the image and never of the invocation.
    if hasattr(config.general, "path_scenarios"):
        # Trailing separator is load-bearing: CriMe concatenates rather than joining, so
        # a path without it yields `/oracle/src/scenariosZAM_Urban-3_3_Repair.xml` and a
        # FileNotFoundError naming a file that never existed.
        config.general.path_scenarios = f"{SRC / 'scenarios'}/"
    config.general.set_scenario_name(point.scenario_id)
    config.vehicle.ego_id = point.ego_id
    for dotted, value in point.config_overrides.items():
        target: Any = config
        *parents, leaf = dotted.split(".")
        for part in parents:
            target = getattr(target, part)
        setattr(target, leaf, value)
    config.update()
    for mutation in point.mutations:
        if mutation == "remove_static_obstacles":
            config.scenario.remove_obstacle(config.scenario.static_obstacles)
            config.update(sce=config.scenario)
        else:
            raise ValueError(f"unknown mutation: {mutation}")
    return config


def _as_arm(raw: Any) -> dict[str, Any]:
    """Tagged union, matching heldout.reference_value's three arms exactly."""
    value = float(raw)
    if math.isnan(value):
        # Not a number and not a failure: the oracle computed and the answer is not
        # defined. Recorded as such rather than coerced.
        return {"value_kind": "undefined", "reason_name": "ORACLE_RETURNED_NAN"}
    if math.isinf(value):
        return {"value_kind": "infinite", "infinite_sign": 1 if value > 0 else -1}
    return {"value_kind": "defined", "value": value}


def _agrees(arm: dict[str, Any], expected: Any, tolerance: float) -> bool:
    if arm["value_kind"] != expected.kind:
        return False
    if expected.kind == "defined":
        return math.isclose(arm["value"], expected.value, abs_tol=tolerance)
    if expected.kind == "infinite":
        return arm["infinite_sign"] == expected.infinite_sign
    return arm.get("reason_name") == expected.reason


def _run_point(point: Point) -> dict[str, Any]:
    record: dict[str, Any] = {
        "point_id": point.point_id,
        "measure_id": point.measure,
        "scenario_ref": point.scenario_id,
        "ego_id": point.ego_id,
        "args": list(point.args),
        "kwargs": dict(point.kwargs),
        "config_overrides": dict(point.config_overrides),
        "mutations": list(point.mutations),
        "tolerance": point.tolerance,
        "source_line": point.source_line,
        "expected": {
            "kind": point.expected.kind,
            "value": point.expected.value,
            "infinite_sign": point.expected.infinite_sign,
            "reason": point.expected.reason,
        },
    }
    try:
        cls = _measure_class(point.measure)
        quantum, quantum_source = _quantum_for(cls)
        record["quantum"] = quantum
        record["quantum_source"] = quantum_source
        config = _build_config(point)
        raw = cls(config).compute(*point.args, **point.kwargs)
        arm = _as_arm(raw)
        record.update(arm)
        record["status"] = "ok" if _agrees(arm, point.expected, point.tolerance) else "mismatch"
    except Exception as exc:  # noqa: BLE001 — every failure mode is a finding, not a crash
        record["status"] = "error"
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()[-2000:]
    return record


def main() -> int:
    records = [_run_point(p) for p in POINTS]
    counts = {
        status: sum(1 for r in records if r["status"] == status)
        for status in ("ok", "mismatch", "error")
    }

    findings: list[str] = []
    # Vacuity guard. A point set that shrank to nothing reports every check green.
    if len(records) < MINIMUM_POINTS:
        findings.append(f"point set is {len(records)}, below the floor of {MINIMUM_POINTS}")
    missing = PHASE0_SCENARIOS - scenarios_covered()
    if missing:
        findings.append(f"Phase 0 scenarios not reached: {sorted(missing)}")
    if counts["ok"] == 0:
        findings.append("no point agreed with the oracle's own literal — extraction is vacuous")

    report = {
        "schema_version": 1,
        "environment": _resolved_environment(),
        "counts": counts,
        "findings": findings,
        "records": records,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "oracle_extract.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    json.dump({"counts": counts, "findings": findings}, sys.stdout, indent=2)
    sys.stdout.write("\n")

    # Fail-closed: mismatches and errors are both defects here, and a run that produced
    # neither an agreement nor a written file has not succeeded.
    return 0 if not findings and counts["mismatch"] == 0 and counts["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
