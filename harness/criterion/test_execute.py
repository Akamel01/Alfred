"""Three outcomes, and the ways two of them get silently collapsed into one.

**How this suite would be shown vacuous** (D57). Every classification test below would
pass against a classifier that returned `DID_NOT_RUN` for everything, so the positive
controls are load-bearing: `test_all_checks_passing_is_a_pass` and
`test_a_failing_check_is_a_fail` must hold, or the three-valued vocabulary has collapsed
to one value and every merge rate is zero.

The two tests worth reading first are `test_zero_checks_is_not_a_pass` and
`test_exit_zero_with_failures_is_not_a_pass`. Both are runs a classifier reading only
`returncode == 0` calls a success, and both are what a vacuous criterion actually looks
like from outside.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from harness.criterion.execute import (
    REPORT_FILENAME,
    ExecutionError,
    ExecutionOutcome,
    execute,
)


def _script(root: Path, *, report: object, exit_code: int, sleep_s: float = 0.0) -> tuple[str, ...]:
    """A command that writes a report and exits with a chosen code.

    Written as a generated script rather than as a stub of `subprocess.run`: the module
    under test is almost entirely about what a real process does — its exit code, its
    report file, its timeout — and a mocked process asserts the mock.
    """
    body = [
        "import json, pathlib, sys, time",
        f"time.sleep({sleep_s!r})",
    ]
    if report is not None:
        # The report text is embedded as a literal. An earlier version wrapped it in a
        # second `json.dumps`, which wrote a JSON *string* rather than an object — and
        # every DID_NOT_RUN test still passed, because "unreadable report" and the thing
        # each test meant to check both classify the same way. The positive controls are
        # what caught it, which is the argument for having them.
        body.append(
            f"pathlib.Path({REPORT_FILENAME!r}).write_text({json.dumps(report)!r})"
        )
    body.append(f"sys.exit({exit_code})")
    script = root / "run_criterion.py"
    script.write_text("\n".join(body) + "\n", encoding="utf-8")
    return (sys.executable, "run_criterion.py")


@pytest.fixture
def env_root(tmp_path: Path) -> Path:
    root = tmp_path / "env"
    root.mkdir()
    return root


# ------------------------------------------------------------------ positive controls


def test_all_checks_passing_is_a_pass(env_root: Path) -> None:
    command = _script(env_root, report={"checks_run": 4, "checks_passed": 4}, exit_code=0)
    result = execute(root=env_root, command=command, timeout_s=30)
    assert result.outcome is ExecutionOutcome.PASSED
    assert result.reason is None
    assert result.report is not None
    assert result.report.checks_run == 4


def test_a_failing_check_is_a_fail(env_root: Path) -> None:
    command = _script(env_root, report={"checks_run": 4, "checks_passed": 3}, exit_code=1)
    result = execute(root=env_root, command=command, timeout_s=30)
    assert result.outcome is ExecutionOutcome.FAILED
    assert result.reason is None


def test_score_is_carried_through(env_root: Path) -> None:
    command = _script(
        env_root, report={"checks_run": 2, "checks_passed": 2, "score": 1.0}, exit_code=0
    )
    result = execute(root=env_root, command=command, timeout_s=30)
    assert result.report is not None
    assert result.report.score == 1.0


# ------------------------------------------------------- what a vacuous criterion looks like


def test_zero_checks_is_not_a_pass(env_root: Path) -> None:
    """The single most dangerous reading in the module.

    A criterion that collected nothing exits zero and looks exactly like one where
    everything passed. Anything keying on the exit code alone scores it a pass, and a
    task whose criterion silently stopped collecting would merge forever.
    """
    command = _script(env_root, report={"checks_run": 0, "checks_passed": 0}, exit_code=0)
    result = execute(root=env_root, command=command, timeout_s=30)
    assert result.outcome is ExecutionOutcome.DID_NOT_RUN
    assert result.reason is not None
    assert "zero checks" in result.reason


def test_missing_report_is_not_a_pass(env_root: Path) -> None:
    command = _script(env_root, report=None, exit_code=0)
    result = execute(root=env_root, command=command, timeout_s=30)
    assert result.outcome is ExecutionOutcome.DID_NOT_RUN


def test_unparseable_report_is_not_a_pass(env_root: Path) -> None:
    (env_root / REPORT_FILENAME).write_text("{not json", encoding="utf-8")
    script = env_root / "run_criterion.py"
    script.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    result = execute(root=env_root, command=(sys.executable, "run_criterion.py"), timeout_s=30)
    assert result.outcome is ExecutionOutcome.DID_NOT_RUN


def test_nan_score_is_rejected(env_root: Path) -> None:
    """A score no comparison orders is not a score.

    `float('nan')` compares false against every threshold including itself, so a criterion
    emitting one scores below any bar and above none — which reads as a clean failure.
    """
    (env_root / REPORT_FILENAME).write_text(
        '{"checks_run": 1, "checks_passed": 1, "score": NaN}', encoding="utf-8"
    )
    script = env_root / "run_criterion.py"
    script.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    result = execute(root=env_root, command=(sys.executable, "run_criterion.py"), timeout_s=30)
    assert result.outcome is ExecutionOutcome.DID_NOT_RUN


def test_exit_zero_with_failures_is_not_a_pass(env_root: Path) -> None:
    """Two readings of one run that contradict each other.

    Neither is then a fact, and picking the convenient one is how a harness reports on
    its own health. `did_not_run` is the honest answer.
    """
    command = _script(env_root, report={"checks_run": 3, "checks_passed": 1}, exit_code=0)
    result = execute(root=env_root, command=command, timeout_s=30)
    assert result.outcome is ExecutionOutcome.DID_NOT_RUN
    assert result.reason is not None
    assert "disagrees" in result.reason


def test_nonzero_exit_with_everything_passing_is_not_a_fail(env_root: Path) -> None:
    """The same disagreement in the direction that would flatter the agent's failure rate."""
    command = _script(env_root, report={"checks_run": 3, "checks_passed": 3}, exit_code=1)
    result = execute(root=env_root, command=command, timeout_s=30)
    assert result.outcome is ExecutionOutcome.DID_NOT_RUN


def test_impossible_report_is_rejected(env_root: Path) -> None:
    command = _script(env_root, report={"checks_run": 2, "checks_passed": 5}, exit_code=0)
    result = execute(root=env_root, command=command, timeout_s=30)
    assert result.outcome is ExecutionOutcome.DID_NOT_RUN


# ------------------------------------------------------------------------- timeout


def test_timeout_is_not_a_failing_check(env_root: Path) -> None:
    """A timeout is a harness property, not a measurement of the agent.

    Recording it as `failed` moves a badly-set timeout into the agent's measured
    competence, where nothing later can tell it apart from a genuine wrong answer.
    """
    command = _script(env_root, report={"checks_run": 1, "checks_passed": 1}, exit_code=0, sleep_s=5)
    result = execute(root=env_root, command=command, timeout_s=0.5)
    assert result.outcome is ExecutionOutcome.DID_NOT_RUN
    assert result.exit_code is None
    assert result.reason is not None
    assert "timed out" in result.reason


# --------------------------------------------------------------------- environment


def test_parent_environment_does_not_cross(env_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Built from nothing, not filtered from the parent.

    A filter needs a complete list of what to remove; construction needs a complete list
    of what to keep, and only the second is short enough to be correct. The variable here
    is deliberately not credential-shaped — a test using `PGPASSWORD` would pass against
    a denylist.
    """
    monkeypatch.setenv("ALFRED_ARBITRARY_MARKER", "leaked")
    script = env_root / "run_criterion.py"
    script.write_text(
        "import json, os, pathlib, sys\n"
        "leaked = 'ALFRED_ARBITRARY_MARKER' in os.environ\n"
        f"pathlib.Path({REPORT_FILENAME!r}).write_text("
        "json.dumps({'checks_run': 1, 'checks_passed': 0 if leaked else 1}))\n"
        "sys.exit(1 if leaked else 0)\n",
        encoding="utf-8",
    )
    result = execute(root=env_root, command=(sys.executable, "run_criterion.py"), timeout_s=30)
    assert result.outcome is ExecutionOutcome.PASSED


def test_credential_shaped_extra_env_is_refused(env_root: Path) -> None:
    command = _script(env_root, report={"checks_run": 1, "checks_passed": 1}, exit_code=0)
    for name in ("ALFRED_DB_URL_MIGRATOR_HELDOUT", "PGPASSWORD", "API_TOKEN", "app_secret"):
        with pytest.raises(ExecutionError, match="refusing to pass"):
            execute(root=env_root, command=command, timeout_s=30, extra_env={name: "x"})


def test_ordinary_extra_env_crosses(env_root: Path) -> None:
    """The control for the refusal above: the door is open for non-credentials."""
    script = env_root / "run_criterion.py"
    script.write_text(
        "import json, os, pathlib, sys\n"
        "ok = os.environ.get('ALFRED_SCENARIO_ID') == 'ZAM_Urban-3_3_Repair'\n"
        f"pathlib.Path({REPORT_FILENAME!r}).write_text("
        "json.dumps({'checks_run': 1, 'checks_passed': 1 if ok else 0}))\n"
        "sys.exit(0 if ok else 1)\n",
        encoding="utf-8",
    )
    result = execute(
        root=env_root,
        command=(sys.executable, "run_criterion.py"),
        timeout_s=30,
        extra_env={"ALFRED_SCENARIO_ID": "ZAM_Urban-3_3_Repair"},
    )
    assert result.outcome is ExecutionOutcome.PASSED


def test_working_directory_is_not_importable(env_root: Path) -> None:
    """`PYTHONSAFEPATH`, and it is the import-side half of the materialization allowlist.

    Without it a file admitted for *reading* becomes importable under a name the criterion
    never declared — which is how a shadowing module reaches a criterion that only ever
    imports the names it was told to.
    """
    (env_root / "json.py").write_text("raise SystemExit('shadowed')\n", encoding="utf-8")
    script = env_root / "run_criterion.py"
    script.write_text(
        "import json, pathlib, sys\n"
        f"pathlib.Path({REPORT_FILENAME!r}).write_text("
        "json.dumps({'checks_run': 1, 'checks_passed': 1}))\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    result = execute(root=env_root, command=(sys.executable, "run_criterion.py"), timeout_s=30)
    assert result.outcome is ExecutionOutcome.PASSED


def test_empty_command_is_refused(env_root: Path) -> None:
    with pytest.raises(ExecutionError):
        execute(root=env_root, command=(), timeout_s=30)


def test_missing_root_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ExecutionError):
        execute(root=tmp_path / "absent", command=("true",), timeout_s=30)
