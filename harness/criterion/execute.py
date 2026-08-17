"""Run a criterion hermetically and classify what happened three ways.

**A check that failed and a check that did not run are different outcomes**, and almost
every test runner and CI system collapses them into one exit code. That collapse is what
makes `indeterminate` necessary: harness flakiness folded into either side of the merge
rate corrupts the only number the autonomy gates read.

**The exit code is corroboration, never the verdict.** An exit code cannot distinguish
"every check passed" from "no check ran" — the second is the shape a vacuous criterion
takes, and it is indistinguishable from success to anything reading `returncode == 0`.
So the command must write a result report, the report is mandatory, and a run that
reports zero checks is `did_not_run` rather than a pass.

**The instrument disagreeing with itself is also `did_not_run`.** Exit zero with failures
in the report, or a nonzero exit with everything reported passing, means the two readings
of the same run contradict each other. Neither reading is then a fact, and picking the
convenient one is how a harness reports on its own health.

**No credential reaches this subprocess.** Agent-authored code executes here, and a
credential for the held-out schema inside the environment that runs the code under test
would let the code under test select its own answers. The environment is built from
nothing rather than filtered from the parent's, because a filter needs a complete list of
what to remove and construction needs a complete list of what to keep — and only the
second list is short enough to be correct.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final

REPORT_FILENAME: Final = "criterion_report.json"

# Kept, not filtered. Everything absent from this list is absent from the environment.
INHERITED_VARS: Final = ("PATH", "LANG", "LC_ALL", "TZ", "HOME", "TMPDIR")

# Pinned rather than inherited. `PYTHONSAFEPATH` keeps the script directory and the
# working directory off `sys.path`, which is the import-side half of the materialization
# allowlist: without it a file the declaration admitted for reading becomes importable by
# a name the criterion never wrote.
PINNED_VARS: Final = {
    "PYTHONSAFEPATH": "1",
    "PYTHONNOUSERSITE": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONUNBUFFERED": "1",
}

# Refused in `extra_env`. Not a boundary — the boundary is that the environment is built
# from `INHERITED_VARS` and nothing else — but a caller passing a credential through the
# one door that stays open should be told, not accommodated.
CREDENTIAL_MARKERS: Final = ("PASSWORD", "SECRET", "TOKEN", "CREDENTIAL", "PG", "ALFRED_DB_URL")

MAX_CAPTURED_CHARS: Final = 64_000


class ExecutionOutcome(Enum):
    """Three values, and the third is the one that must not be folded into the others."""

    PASSED = "passed"
    FAILED = "failed"
    DID_NOT_RUN = "did_not_run"


class ExecutionError(RuntimeError):
    """The run could not be launched as specified."""


@dataclass(frozen=True)
class CriterionReport:
    """What the command said about itself."""

    checks_run: int
    checks_passed: int
    score: float | None


@dataclass(frozen=True)
class Execution:
    """One criterion run. `reason` is non-null exactly when the outcome is DID_NOT_RUN."""

    outcome: ExecutionOutcome
    exit_code: int | None
    reason: str | None
    report: CriterionReport | None
    duration_ms: int
    stdout: str
    stderr: str


def _build_env(extra_env: dict[str, str] | None) -> dict[str, str]:
    env = {name: os.environ[name] for name in INHERITED_VARS if name in os.environ}
    env.update(PINNED_VARS)
    for name, value in (extra_env or {}).items():
        upper = name.upper()
        if any(marker in upper for marker in CREDENTIAL_MARKERS):
            raise ExecutionError(
                f"refusing to pass {name!r} into the criterion environment: agent-authored "
                f"code executes there, and a credential in it lets the code under test "
                f"select its own answers"
            )
        env[name] = value
    return env


def _read_report(root: Path) -> CriterionReport | None:
    path = root / REPORT_FILENAME
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    try:
        checks_run = int(raw["checks_run"])
        checks_passed = int(raw["checks_passed"])
    except (KeyError, TypeError, ValueError):
        return None
    score = raw.get("score")
    if score is not None:
        try:
            score = float(score)
        except (TypeError, ValueError):
            return None
        if math.isnan(score):
            # A score no comparison orders is not a score.
            return None
    if checks_run < 0 or checks_passed < 0 or checks_passed > checks_run:
        return None
    return CriterionReport(checks_run=checks_run, checks_passed=checks_passed, score=score)


def _classify(exit_code: int, report: CriterionReport | None) -> tuple[ExecutionOutcome, str | None]:
    if report is None:
        # Includes the case where the command never started writing it. A missing report
        # after a zero exit is the most dangerous single reading in this module: it is
        # what a criterion that collected nothing looks like.
        return ExecutionOutcome.DID_NOT_RUN, f"no readable {REPORT_FILENAME} (exit {exit_code})"
    if report.checks_run == 0:
        return ExecutionOutcome.DID_NOT_RUN, "criterion reported zero checks run"

    all_passed = report.checks_passed == report.checks_run
    if all_passed and exit_code == 0:
        return ExecutionOutcome.PASSED, None
    if not all_passed and exit_code != 0:
        return ExecutionOutcome.FAILED, None
    disagreement = (
        f"instrument disagrees with itself: exit {exit_code} with "
        f"{report.checks_passed}/{report.checks_run} passing"
    )
    return ExecutionOutcome.DID_NOT_RUN, disagreement


def execute(
    *,
    root: Path,
    command: tuple[str, ...],
    timeout_s: float,
    extra_env: dict[str, str] | None = None,
) -> Execution:
    """Run `command` inside `root` and say which of three things happened.

    Never raises on a failing criterion — a failing criterion is a result. It raises only
    when the run could not be launched as specified, which is a different thing and
    belongs to the caller's fail-closed table rather than to the verdict.
    """
    if not command:
        raise ExecutionError("no command given")
    if not root.is_dir():
        raise ExecutionError(f"{root} is not a materialized environment")

    env = _build_env(extra_env)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as expired:
        return Execution(
            outcome=ExecutionOutcome.DID_NOT_RUN,
            exit_code=None,
            # A timeout is not a failing check. Recording it as one moves a harness
            # property — a timeout set from the wrong distribution — into the agent's
            # measured competence.
            reason=f"timed out after {timeout_s:g}s",
            report=None,
            duration_ms=int((time.monotonic() - started) * 1000),
            stdout=_truncate(expired.stdout),
            stderr=_truncate(expired.stderr),
        )
    except OSError as exc:
        raise ExecutionError(f"could not launch {command[0]!r}: {exc}") from exc

    duration_ms = int((time.monotonic() - started) * 1000)
    report = _read_report(root)
    outcome, reason = _classify(completed.returncode, report)
    return Execution(
        outcome=outcome,
        exit_code=completed.returncode,
        reason=reason,
        report=report,
        duration_ms=duration_ms,
        stdout=_truncate(completed.stdout),
        stderr=_truncate(completed.stderr),
    )


def _truncate(text: str | bytes | None) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    if len(text) <= MAX_CAPTURED_CHARS:
        return text
    return text[:MAX_CAPTURED_CHARS] + f"\n[truncated at {MAX_CAPTURED_CHARS} characters]"
