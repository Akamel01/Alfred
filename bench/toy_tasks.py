"""Phase -1 toy tasks: is the narrow task class within reach of a local model?

Each task is shaped like the real Phase 1 class (D36): a published formula, a
fixed signature, and a numeric verdict the model does not author.

Three properties are deliberate, because they are the ones Phase 1 depends on:

  * The model sees two worked examples. It is graded on HELD-OUT cases it never
    sees (A3). Visible-only scoring certifies exactly the behaviour that games
    the visible suite.
  * Generated code executes in a container with ``--network none``, never on the
    host (D10/A2). These are toy tasks, but the containment precedent is the
    point; a harness that runs model output on the host teaches the wrong habit.
  * The harness computes the verdict. The model's reply is a claim (D5).

Usage:
    python3 bench/toy_tasks.py --model openai/gpt-oss-120b
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASE_URL = "http://127.0.0.1:1234/v1"
RESULTS_DIR = Path(__file__).parent / "results"
IMAGE = "python:3.12-slim"


@dataclass
class Task:
    name: str
    spec: str
    signature: str
    visible: list[tuple[list[float], float]]
    held_out: list[tuple[list[float], float]] = field(default_factory=list)
    tolerance: float = 1e-2
    # The task label and the function the model must define are not always the
    # same string. Grading on the label silently scores every solution zero.
    fn: str = ""

    def __post_init__(self) -> None:
        if not self.fn:
            self.fn = self.signature.split("def ", 1)[1].split("(", 1)[0].strip()


TASKS: list[Task] = [
    Task(
        name="thw",
        spec=(
            "Time headway (THW) is the time until the ego vehicle reaches the "
            "current position of the lead vehicle, assuming the ego keeps its "
            "present speed. Given the longitudinal gap in metres between the "
            "front of the ego and the rear of the lead vehicle, and the ego's "
            "speed in m/s, return the time headway in seconds. If the ego is "
            "stationary the headway is infinite."
        ),
        signature="def thw(gap_m: float, ego_speed_mps: float) -> float:",
        visible=[([24.0, 10.0], 2.4), ([0.0, 10.0], 0.0)],
        held_out=[
            ([50.0, 20.0], 2.5),
            ([7.5, 3.0], 2.5),
            ([13.0, 0.0], float("inf")),
            ([100.0, 8.0], 12.5),
        ],
    ),
    Task(
        name="ttc_constant_velocity",
        spec=(
            "Time to collision (TTC) for two vehicles on the same lane under "
            "constant velocity. Given the longitudinal gap in metres and the "
            "closing speed in m/s (ego speed minus lead speed), return the time "
            "to collision in seconds. If the closing speed is zero or negative "
            "the vehicles are not approaching and TTC is infinite."
        ),
        signature="def ttc(gap_m: float, closing_speed_mps: float) -> float:",
        visible=[([24.0, 10.0], 2.4), ([10.0, -2.0], float("inf"))],
        held_out=[
            ([25.0, 20.0], 1.25),
            ([0.0, 5.0], 0.0),
            ([12.0, 0.0], float("inf")),
            ([64.0, 8.0], 8.0),
        ],
    ),
    Task(
        name="drac",
        spec=(
            "Deceleration rate to avoid a crash (DRAC) is the constant "
            "deceleration the following vehicle must apply to avoid colliding "
            "with the lead vehicle. For a longitudinal gap in metres and a "
            "closing speed in m/s, DRAC is the closing speed squared divided by "
            "twice the gap, in m/s^2. If the closing speed is zero or negative "
            "DRAC is zero. If the gap is zero and the vehicles are closing, DRAC "
            "is infinite."
        ),
        signature="def drac(gap_m: float, closing_speed_mps: float) -> float:",
        visible=[([25.0, 10.0], 2.0), ([10.0, -3.0], 0.0)],
        held_out=[
            ([20.0, 20.0], 10.0),
            ([50.0, 10.0], 1.0),
            ([8.0, 4.0], 1.0),
            ([0.0, 6.0], float("inf")),
        ],
    ),
    Task(
        name="pet",
        spec=(
            "Post-encroachment time (PET) is the gap between one road user "
            "leaving a conflict area and the next entering it. Given the time in "
            "seconds at which the first user exits the conflict area and the time "
            "at which the second user enters it, return the PET in seconds. If "
            "the second user enters before the first has left, the paths overlap "
            "in time and PET is 0.0."
        ),
        signature="def pet(first_exit_s: float, second_entry_s: float) -> float:",
        visible=[([2.0, 5.2], 3.2), ([4.0, 3.0], 0.0)],
        held_out=[
            ([1.5, 4.7], 3.2),
            ([10.0, 10.0], 0.0),
            ([0.0, 7.25], 7.25),
            ([6.0, 5.0], 0.0),
        ],
    ),
    Task(
        name="msd",
        spec=(
            "Minimum safe distance (MSD) under a constant-deceleration model is "
            "the distance a vehicle travels during the driver's reaction time "
            "plus the distance needed to brake to a full stop. Given speed in "
            "m/s, reaction time in seconds, and deceleration magnitude in m/s^2 "
            "(a positive number), return the minimum safe distance in metres."
        ),
        signature="def msd(speed_mps: float, reaction_s: float, decel_mps2: float) -> float:",
        visible=[([10.0, 1.0, 5.0], 20.0), ([0.0, 1.0, 5.0], 0.0)],
        held_out=[
            ([20.0, 1.0, 5.0], 60.0),
            ([15.0, 0.5, 7.5], 22.5),
            ([30.0, 2.0, 10.0], 105.0),
            ([5.0, 0.0, 2.5], 5.0),
        ],
    ),
]


def _post(payload: dict[str, Any], timeout: float = 900.0) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def build_prompt(task: Task) -> str:
    examples = "\n".join(
        f"    {task.fn}({', '.join(str(a) for a in args)}) == {expected}"
        for args, expected in task.visible
    )
    return (
        f"{task.spec}\n\n"
        f"Implement exactly this function:\n\n    {task.signature}\n\n"
        f"It must satisfy:\n{examples}\n\n"
        "Use `math.inf` for infinite results. Return ONLY the Python code, "
        "including any imports. No explanation, no markdown fences."
    )


def extract_code(reply: str) -> str:
    """Models wrap code in fences despite instructions. Strip rather than fail —
    the task is the metric, not instruction-following."""
    text = reply.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts[1:]:
            body = part.split("\n", 1)
            candidate = body[1] if len(body) > 1 else body[0]
            if "def " in candidate:
                return candidate.rsplit("```", 1)[0].strip()
    return text


RUNNER = '''
import json, math, sys
sys.path.insert(0, "/work")
results = []
try:
    import candidate
except Exception as exc:
    print(json.dumps({"import_error": repr(exc)}))
    raise SystemExit(0)

cases = json.load(open("/work/cases.json"))
fn = getattr(candidate, cases["fn"], None)
if fn is None:
    print(json.dumps({"import_error": "function not defined: " + cases["fn"]}))
    raise SystemExit(0)

for args, expected in cases["cases"]:
    try:
        got = fn(*args)
        ok = (
            (math.isinf(expected) and math.isinf(got) and (got > 0) == (expected > 0))
            or (not math.isinf(expected) and abs(got - expected) <= cases["tol"])
        )
        results.append({"args": args, "expected": expected, "got": got, "pass": bool(ok)})
    except Exception as exc:
        results.append({"args": args, "expected": expected, "error": repr(exc), "pass": False})

print(json.dumps({"results": results}))
'''


def run_in_container(code: str, task: Task, cases: list[Any]) -> dict[str, Any]:
    """Execute model-authored code with no network and a read-only mount."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "candidate.py").write_text(code)
        (work / "runner.py").write_text(RUNNER)
        (work / "cases.json").write_text(
            json.dumps(
                {
                    "fn": task.fn,
                    "tol": task.tolerance,
                    "cases": [[a, e] for a, e in cases],
                }
            )
        )
        try:
            proc = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "--network", "none",
                    "--memory", "512m",
                    "--pids-limit", "64",
                    "-v", f"{work}:/work:ro",
                    IMAGE,
                    "python", "/work/runner.py",
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            return {"error": "container timeout"}

        out = proc.stdout.strip().splitlines()
        if not out:
            return {"error": f"no output; stderr={proc.stderr.strip()[:400]}"}
        try:
            return json.loads(out[-1])
        except json.JSONDecodeError:
            return {"error": f"unparseable: {out[-1][:400]}"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"model": args.model, "tasks": []}

    for task in TASKS:
        print(f"\n=== {task.name}", flush=True)
        started = time.perf_counter()
        try:
            resp = _post(
                {
                    "model": args.model,
                    "messages": [{"role": "user", "content": build_prompt(task)}],
                    "temperature": args.temperature,
                    "max_tokens": 1200,
                }
            )
            reply = resp["choices"][0]["message"]["content"] or ""
        except (urllib.error.URLError, TimeoutError, KeyError) as exc:
            print(f"  generation failed: {exc!r}", flush=True)
            report["tasks"].append({"task": task.name, "error": repr(exc)})
            continue
        gen_s = round(time.perf_counter() - started, 2)

        code = extract_code(reply)
        visible = run_in_container(code, task, task.visible)
        held_out = run_in_container(code, task, task.held_out)

        def score(block: dict[str, Any]) -> str:
            if "results" not in block:
                return f"0/? ({block.get('error') or block.get('import_error')})"
            passed = sum(1 for r in block["results"] if r["pass"])
            return f"{passed}/{len(block['results'])}"

        print(f"  gen {gen_s}s  visible {score(visible)}  held-out {score(held_out)}", flush=True)
        report["tasks"].append(
            {
                "task": task.name,
                "generation_s": gen_s,
                "code": code,
                "visible": visible,
                "held_out": held_out,
            }
        )

    def total(key: str) -> tuple[int, int]:
        passed = attempted = 0
        for entry in report["tasks"]:
            block = entry.get(key) or {}
            for result in block.get("results", []):
                attempted += 1
                passed += bool(result["pass"])
        return passed, attempted

    vp, va = total("visible")
    hp, ha = total("held_out")
    report["summary"] = {
        "visible_passed": vp,
        "visible_total": va,
        "held_out_passed": hp,
        "held_out_total": ha,
    }
    print(f"\nVISIBLE {vp}/{va}   HELD-OUT {hp}/{ha}")

    out = RESULTS_DIR / f"toy_{args.model.replace('/', '_')}.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
