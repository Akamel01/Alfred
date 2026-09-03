#!/usr/bin/env python3
"""How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything else in this repository is verified *by*: the criterion
runner, the containment assertions, the stamp verifier, the egress canary, the seeded-defect
suite. On `main` @ `fa62b4b` it is the one tree nothing verifies. `[tool.ruff].include` and
`[tool.pyright].include` name `src` and `tests`; neither reaches it.

Measured 2026-08-19, and reproducible from this file's own output:

    uv run ruff check harness     -> warning: No Python files found ... ; exit 0
    uv run pyright harness        -> 311 errors

The first line is the hazard this lint exists for. **A `ruff` include that matches nothing
reports success in exactly the same way a clean tree does** -- the ADR-0007 vacuity class,
here found in the tooling rather than in an assertion. A planted
`def broken(x: int) -> str: return x` in `harness/acs/acs1.py` passes both product gates; the
same line in `src/domain/ids.py` turns both red. The gates are live. `harness/` is scoped out.

Two checks, and one of them carries a recorded hole rather than pretending not to.

  C -- COVERAGE. Of the `.py` files on disk under `harness/`, how many does `ruff` collect
      under the committed configuration? The count is printed on every run and asserted
      against `COVERAGE_FLOOR` below. **The floor is 0 today.** That is not a passing grade,
      it is a recorded measurement, in the shape `lint_ci_coverage.py` already uses for the
      twenty-four `not-yet-injected` failure rows: a lint that cannot be landed green
      enforces nothing, so the hole is counted and printed rather than hidden, and what the
      check forbids is *drift* -- coverage going down, or the disk scan going quiet.

      Raising the floor is the OBSERVER-1 deliverable (see ADR-0029). When the include is
      widened, this constant is the one-line diff that makes the widening irreversible.

  D -- DETECTION. That a collected harness file with a violation in it comes back red, and
      that the *planted* violation is the one reported -- not merely a non-zero exit. Run
      under `--self-test`, against a scratch copy. The original tree is never mutated.

**Vacuity guard (D57).** Zero `.py` files found on disk under `harness/` is a failure, not a
pass: it is what this lint looks like the day someone moves the tree. `ruff` reporting more
collected files than exist on disk is also a failure -- it means the two sides are counting
different things and the comparison has stopped meaning anything.

**F25.** Every mode exits 0 or 1. `not_executed` is not a state this script can produce: if
`ruff` cannot be invoked, that is a failure and it is reported as one.

**What would show this lint vacuous.** The floor sitting at 0 forever while the prose above
implies coverage -- visible, because the count is in the output of every CI run. Or the
detection check planting into a directory `ruff` never reaches, so it reports red for a
reason unrelated to the plant: guarded by asserting the reported rule code *and* path.

Inspector machinery under D20: agents may not edit this file without an authorizing ADR.
This file is authorized by ADR-0029 and is an O9 review item.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from _lintkit import REPO_ROOT, self_test_exit, vacuity_guard

HARNESS: Final = REPO_ROOT / "harness"

# The number of `.py` files under `harness/` that `ruff` collects under the committed
# `[tool.ruff].include`. 0 on `main` @ `fa62b4b`, against 74 files on disk. Held at 0 by
# ADR-0029 pending OBSERVER-1: closing the gap needs 120 hand edits, 55 suppressions and 17
# judgement calls, 45 of them in M2's `harness/containment/`, 8 in M3's `harness/selftest/`
 # and 2 in `harness/patch/`, which no module may touch. See _archive/CLASSIFICATION-M1.md.
# This number may go up. It may not go down.
COVERAGE_FLOOR: Final = 0

# Planted into the scratch copy for check D. `F401` is chosen because it is unambiguous,
# fixable, and in the committed `select` list, so a plant that fails to fire cannot be
# explained away as a rule that is switched off.
_PROBE_CLEAN: Final = '"""A collected file with nothing wrong with it."""\n'
_PROBE_PLANTED: Final = '"""A collected file with one planted violation."""\n\nimport os\n'
_PROBE_RULE: Final = "F401"


def _ruff() -> Path:
    """The project's own `ruff`, or a failure. Never a skip -- F25."""
    candidate = REPO_ROOT / ".venv" / "bin" / "ruff"
    if candidate.is_file():
        return candidate
    found = shutil.which("ruff")
    if found is None:
        sys.stdout.write(
            "FAIL ruff is not installed: expected .venv/bin/ruff or `ruff` on PATH. "
            "A gate that cannot run its tool has not passed; run `uv sync --frozen "
            "--all-extras --dev`.\n"
        )
        raise SystemExit(1)
    return Path(found)


@dataclass(frozen=True)
class Coverage:
    on_disk: int
    collected: int
    violations: list[str]


def check_coverage(*, base: Path | None = None, floor: int = COVERAGE_FLOOR) -> Coverage:
    """C. What `ruff` collects under `harness/`, against what is there."""
    root = base if base is not None else REPO_ROOT
    tree = root / "harness"

    on_disk = sorted(p for p in tree.rglob("*.py") if "__pycache__" not in p.parts) if tree.is_dir() else []

    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell, executable resolved above
        [str(_ruff()), "check", "--show-files", "harness"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        return Coverage(len(on_disk), 0, [f"ruff exited {proc.returncode}: {proc.stderr.strip()[:400]}"])

    collected = [line for line in proc.stdout.splitlines() if line.strip().endswith(".py")]

    violations: list[str] = []
    if len(collected) < floor:
        violations.append(
            f"C coverage regressed: ruff collects {len(collected)} files under harness/, "
            f"below the recorded floor of {floor}. Coverage may go up; it may not go down."
        )
    if len(collected) > len(on_disk):
        violations.append(
            f"C ruff collected {len(collected)} files but only {len(on_disk)} .py files "
            f"exist under harness/. The two sides are counting different things."
        )
    return Coverage(len(on_disk), len(collected), violations)


def check_detection(scratch: Path) -> list[str]:
    """D. A collected harness file with a violation in it comes back red, naming the plant.

    Runs against a copy with an include that reaches it, so it tests the *detector* rather
    than the current include. Both arms are required: the clean arm is the control against a
    check that reports red unconditionally.
    """
    failures: list[str] = []
    ruff = _ruff()

    for arm, body, expect_hit in (("clean", _PROBE_CLEAN, False), ("planted", _PROBE_PLANTED, True)):
        root = scratch / f"detect-{arm}"
        (root / "harness").mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "pyproject.toml", root / "pyproject.toml")
        probe = root / "harness" / "_gate_probe.py"
        probe.write_text(body, encoding="utf-8")

        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [
                str(ruff), "check",
                "--config", 'include=["harness/**/*.py"]',
                "--output-format", "json",
                "harness/_gate_probe.py",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode not in (0, 1):
            failures.append(f"D {arm} arm: ruff exited {proc.returncode}: {proc.stderr.strip()[:300]}")
            continue

        try:
            reported = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            failures.append(f"D {arm} arm: ruff did not return JSON: {proc.stdout[:200]!r}")
            continue

        hits = [
            d for d in reported
            if d.get("code") == _PROBE_RULE and d.get("filename", "").endswith("_gate_probe.py")
        ]
        if expect_hit and not hits:
            failures.append(
                f"D the planted {_PROBE_RULE} in a collected harness file was not reported. "
                f"ruff returned {len(reported)} diagnostics: {[d.get('code') for d in reported]}"
            )
        if not expect_hit and hits:
            failures.append(
                f"D the clean control reported {_PROBE_RULE} with nothing planted -- a gate "
                f"that reports red unconditionally is not a gate."
            )
    return failures


def _fixture(root: Path, *, include_harness: bool, files: int) -> None:
    """A scratch repository with `files` harness modules, included or not."""
    (root / "harness").mkdir(parents=True, exist_ok=True)
    for n in range(files):
        (root / "harness" / f"mod_{n}.py").write_text('"""x."""\n', encoding="utf-8")
    include = '["harness/**/*.py"]' if include_harness else '["src/**/*.py"]'
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "keep.py").write_text('"""x."""\n', encoding="utf-8")
    (root / "pyproject.toml").write_text(
        f'[tool.ruff]\nline-length = 100\ninclude = {include}\n', encoding="utf-8"
    )


def self_test() -> int:
    """Plant, require the check to fire, and require the paired control to stay quiet.

    Committed as a mode rather than a separate test file so it travels with the lint. This
    lint's whole subject is a check that stopped collecting anything without anyone noticing;
    its own control living in another directory is a control someone deletes.
    """
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)

        # C control: an include that reaches the tree, at a floor it clears. Must be silent.
        covered = scratch / "covered"
        _fixture(covered, include_harness=True, files=3)
        result = check_coverage(base=covered, floor=3)
        if result.violations:
            failures.append(f"C control fired on a fully covered tree: {result.violations}")
        if (result.collected, result.on_disk) != (3, 3):
            failures.append(f"C control counted {result.collected}/{result.on_disk}, expected 3/3")

        # C planted: the state of `main` -- files on disk, include pointing elsewhere.
        uncovered = scratch / "uncovered"
        _fixture(uncovered, include_harness=False, files=3)
        result = check_coverage(base=uncovered, floor=3)
        if not result.violations:
            failures.append("C did not fire on a tree ruff collects nothing from at a floor of 3")
        if result.collected != 0:
            failures.append(f"C uncovered tree reported {result.collected} collected, expected 0")

        # C vacuity: an empty tree must not read as covered.
        empty = scratch / "empty"
        _fixture(empty, include_harness=True, files=0)
        if check_coverage(base=empty, floor=0).on_disk != 0:
            failures.append("C empty tree did not report zero .py files on disk")

        failures.extend(check_detection(scratch))

    return self_test_exit(
        failures,
        "OK self-test — C fires on a tree ruff collects nothing from, stays quiet on a "
        "covered one, and reports zero on an empty one; D reports the planted "
        f"{_PROBE_RULE} in a collected harness file and stays quiet without it\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint coverage of harness/, and whether the gate can go red.")
    parser.add_argument("--self-test", action="store_true", help="plant violations and verify each check fires")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    result = check_coverage()

    failed = False
    for violation in result.violations:
        sys.stdout.write(f"{violation}\n")
        failed = True
    if vacuity_guard(
        result.on_disk,
        "VACUOUS C: found 0 .py files under harness/ — the tree moved, or the scan broke\n",
    ):
        failed = True

    if failed:
        return 1
    sys.stdout.write(
        f"OK harness lint coverage — ruff collects {result.collected} of {result.on_disk} "
        f".py files under harness/ (floor {COVERAGE_FLOOR}). "
        f"{result.on_disk - result.collected} files are linted by nothing; ADR-0029, OBSERVER-1.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
