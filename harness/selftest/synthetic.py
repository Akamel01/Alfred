"""A criterion with no domain in it, and a defect that can be dialled.

S4 asks whether `CriterionRunner` reds what it should red and greens what it should green.
That is a question about the *runner*, not about any metric — so the criterion it is
measured with is synthetic, and deliberately so. Calibrating the inspector against a real
domain metric would make a factory gate depend on a domain that may be written off, and
would confound the runner's tolerance behaviour with the metric's own correctness.

------------------------------------------------------------------ what it computes

The sum of a list of floats. Chosen because it has a **genuine, measurable noise floor**:
naive left-to-right summation of values spanning many magnitudes loses low-order bits, and
how much it loses depends on the order. Permuting the input therefore produces a real
spread, which is what `noise.py` measures to obtain ε. A criterion whose output is exactly
reproducible would give ε = 0, collapsing the ladder's two middle rungs onto the tolerance
boundary and leaving τ's calibration untested — the very thing the rung exists for.

The reference value is `math.fsum`, which is exact. The candidate uses naive summation, so
even a perfectly honest candidate sits a little away from the reference. That is the point:
the noise floor is a property of the criterion, not a defect in the solution.

------------------------------------------------------------- where the defect goes in

`delta` is added to the candidate's result. Nothing else about the candidate changes, so a
rung differs from its neighbour in exactly one number and any change in verdict is
attributable to it.

------------------------------------------------- the visible half must not do the grading

The visible criterion checks shape — the module imports, the entry point exists, the result
is a finite float — and passes at **every** rung. It has to: `evaluate` short-circuits to
`fail` without running the harvest when the visible half fails, so a visible criterion that
also checked the value would make the ladder measure the visible half and never reach the
held-out comparison the rungs are about. This mirrors A3, where visible criteria test in
isolation and the held-out half is the gate.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Final

MEASURE_ID: Final = "synthetic.sum"

# Values spanning magnitudes, so naive summation genuinely loses bits and the loss depends
# on order. A list of similar-sized values would sum exactly and report no noise floor.
SYNTHETIC_INPUT: Final[tuple[float, ...]] = tuple(
    value
    for index in range(1, 1201)
    for value in (float(index) * 1e8, 1.0 / float(index), -float(index) * 1e8)
)


def reference_value() -> float:
    """Exact. `math.fsum` is correctly rounded, so this is the answer the noise is around."""
    return math.fsum(SYNTHETIC_INPUT)


def naive_sum(values: tuple[float, ...]) -> float:
    total = 0.0
    for v in values:
        total += v
    return total


_SOLUTION = '''"""Candidate solution. Written by the harness, standing in for an agent's patch."""

INPUT = {input_literal!r}
DELTA = {delta!r}


def compute() -> float:
    total = 0.0
    for value in INPUT:
        total += value
    return total + DELTA
'''

_VISIBLE = '''"""Visible criterion: shape only. Passes at every rung, by design."""

import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

checks_run = 0
checks_passed = 0


def check(ok: object) -> None:
    global checks_run, checks_passed
    checks_run += 1
    if ok:
        checks_passed += 1


try:
    import solution

    check(hasattr(solution, "compute"))
    result = solution.compute()
    check(isinstance(result, float))
    check(math.isfinite(result))
except Exception:
    checks_run = max(checks_run, 1)

pathlib.Path(__file__).resolve().parent.joinpath("criterion_report.json").write_text(
    json.dumps(
        {
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "score": (checks_passed / checks_run) if checks_run else None,
        }
    )
)
sys.exit(0 if checks_run and checks_passed == checks_run else 1)
'''

# Computes and reports. It does NOT compare: the reference value never enters this
# environment, because agent-authored code executes here and an expected value sitting
# beside the code under test is D50's delegation failure (ADR-0011).
_HARVEST = '''"""Held-out harvest: compute and emit. No reference value is present here."""

import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import solution

value = solution.compute()
if math.isnan(value):
    tagged = {"kind": "undefined", "reason": "NOT_A_NUMBER"}
elif math.isinf(value):
    tagged = {"kind": "infinite", "sign": 1 if value > 0 else -1}
else:
    tagged = {"kind": "defined", "value": value}

root = pathlib.Path(__file__).resolve().parent
root.joinpath("criterion_harvest.json").write_text(json.dumps({"synthetic.sum": tagged}))
root.joinpath("criterion_report.json").write_text(
    json.dumps({"checks_run": 1, "checks_passed": 1, "score": 1.0})
)
sys.exit(0)
'''


def write_candidate(root: Path, *, delta: float) -> None:
    """The agent's tree. One file, one dialled defect."""
    root.mkdir(parents=True, exist_ok=True)
    root.joinpath("solution.py").write_text(
        _SOLUTION.format(input_literal=SYNTHETIC_INPUT, delta=delta)
    )


def write_null_candidate(root: Path) -> None:
    """A run that took no actions. The tree exists and holds nothing.

    Not an empty `solution.py`: a null agent produced no file at all, and the floor test
    is about what the harness scores when there is nothing to score.
    """
    root.mkdir(parents=True, exist_ok=True)


def write_trusted(root: Path) -> None:
    """The harness's own tree: the criterion, never the candidate's."""
    root.mkdir(parents=True, exist_ok=True)
    root.joinpath("run_visible.py").write_text(_VISIBLE)
    root.joinpath("run_harvest.py").write_text(_HARVEST)
