"""Containment assertions, each paired with the control that stops it reading green.

**How this suite would be shown vacuous** (D57). Every "must fail" test would pass against
a probe that failed unconditionally, and every "must pass" test against one that passed
unconditionally — so the file is written in pairs and neither half may be deleted without
the other going obviously wrong.

Three tests carry the weight:

- `test_canary_fails_when_the_target_is_reachable` uses a loopback listener the test owns,
  so it does not depend on the network state of the machine running it. Without it, the
  canary suite would pass on an unplugged laptop and prove nothing.
- `test_canary_is_not_executed_when_its_control_fails` is the reason the control exists: an
  unreachable target and a broken socket layer are the same observation, and only one of
  them is containment.
- `test_zero_interpreters_is_not_a_pass` is F15. A probe with nothing to probe reports the
  same thing as a probe that found nothing wrong.

**What none of this establishes.** The canary proves a target is unreachable, never that a
policy is the reason — a container with no network interface passes identically. And the
oracle probe is name- and hash-based, so a renamed, reformatted vendored copy passes it.
Both limits are in the modules' own docstrings and neither is closed here.
"""

from __future__ import annotations

import json
import socket
import sys
from contextlib import closing
from pathlib import Path

import pytest

from harness.containment.assertions import (
    Assertion,
    AssertionOutcome,
    AssertionReport,
    ContainmentFailure,
)
from harness.containment.denylist import Classification, DenylistError
from harness.containment.denylist import load as load_denylist
from harness.containment.egress import (
    CanaryTarget,
    NetworkPolicy,
    NetworkPolicyError,
    canary,
    check_allowlist,
)
from harness.containment.egress import load as load_network
from harness.containment.oracle_absence import (
    check_closure,
    discover_interpreters,
    probe,
)

# ------------------------------------------------------------------ the vocabulary


def _assertion(outcome: AssertionOutcome) -> Assertion:
    return Assertion("C1", outcome, "detail")


def test_not_executed_is_treated_as_failed() -> None:
    """F25, stated as the only line in this file that must never be relaxed."""
    report = AssertionReport((_assertion(AssertionOutcome.NOT_EXECUTED),))
    with pytest.raises(ContainmentFailure, match="not_executed"):
        report.require_all_passed(required=("C1",))


def test_an_absent_assertion_is_a_failure() -> None:
    """An assertion nobody ran and one nobody wrote are indistinguishable from here."""
    with pytest.raises(ContainmentFailure, match="absent"):
        AssertionReport(()).require_all_passed(required=("C1",))


def test_a_passing_assertion_is_accepted() -> None:
    AssertionReport((_assertion(AssertionOutcome.PASSED),)).require_all_passed(required=("C1",))


def test_unverified_premises_are_reported() -> None:
    """ADR-0007: an assertion may be executed, passed, and vacuous.

    Not representable in the three-valued outcome, so it travels as a flag and a reader
    consults it before quoting a green report as evidence.
    """
    report = AssertionReport(
        (
            Assertion("C2", AssertionOutcome.PASSED, "ok", premise_verified=False),
            Assertion("C6", AssertionOutcome.PASSED, "ok"),
        )
    )
    assert report.unverified_premises == ("C2",)


# --------------------------------------------------------------------- the denylist


def _denylist_file(tmp_path: Path, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "version": 7,
        "denied": [
            {"distribution": "fake-oracle", "modules": ["fakeoracle"], "reason": "the oracle"}
        ],
        "permitted_substrate": [
            {"distribution": "numpy", "modules": ["numpy"], "reason": "substrate"}
        ],
    }
    payload.update(overrides)
    path = tmp_path / "denylist.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_the_committed_denylist_loads() -> None:
    """The control for every refusal below: the real policy must be well-formed."""
    loaded = load_denylist()
    assert loaded.version >= 1
    assert "commonroad_crime" in loaded.denied_modules
    assert len(loaded.sha256) == 64


def test_the_digest_covers_the_recorded_reasons(tmp_path: Path) -> None:
    """A silent reclassification changes the fingerprint.

    The reasons are the recorded human judgement D54 asks for. If they were outside the
    digest, the reason for a denial could be rewritten without invalidating a single
    autonomy grant measured under it.
    """
    first = load_denylist(_denylist_file(tmp_path))
    second = load_denylist(
        _denylist_file(
            tmp_path,
            denied=[
                {"distribution": "fake-oracle", "modules": ["fakeoracle"], "reason": "different"}
            ],
        )
    )
    assert first.sha256 != second.sha256


def test_an_empty_denylist_is_refused(tmp_path: Path) -> None:
    with pytest.raises(DenylistError, match="denies nothing"):
        load_denylist(_denylist_file(tmp_path, denied=[]))


def test_an_entry_without_a_reason_is_refused(tmp_path: Path) -> None:
    with pytest.raises(DenylistError, match="records no reason"):
        load_denylist(
            _denylist_file(
                tmp_path, denied=[{"distribution": "x", "modules": ["x"], "reason": "  "}]
            )
        )


def test_a_both_listed_distribution_is_refused(tmp_path: Path) -> None:
    """A policy that says two things is decided by whichever code reads it first."""
    with pytest.raises(DenylistError, match="both denied and permitted"):
        load_denylist(
            _denylist_file(
                tmp_path,
                permitted_substrate=[
                    {"distribution": "fake_oracle", "modules": ["fakeoracle"], "reason": "no"}
                ],
            )
        )


def test_distribution_names_normalize(tmp_path: Path) -> None:
    """`commonroad_crime` and `commonroad-crime` are one distribution to a resolver."""
    loaded = load_denylist(_denylist_file(tmp_path))
    assert loaded.classify(distribution="Fake_Oracle") is Classification.DENIED


def test_unclassified_is_neither(tmp_path: Path) -> None:
    loaded = load_denylist(_denylist_file(tmp_path))
    assert loaded.classify(distribution="pytest") is Classification.UNCLASSIFIED


# ---------------------------------------------------------------- the oracle probe


def test_a_denied_module_on_the_import_path_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Layer 2: `find_spec` resolves the denied name, so the run does not start.

    The module is planted with a module-level side effect that would be visible if the
    probe imported it. It must not be — importing a module to learn whether it is
    importable executes its code inside the sandbox, which is the thing being prevented.
    """
    planted = tmp_path / "site"
    (planted / "fakeoracle").mkdir(parents=True)
    (planted / "fakeoracle" / "__init__.py").write_text(
        "raise RuntimeError('module-level code executed: the probe imported instead of "
        "resolving')\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(planted))
    result = probe(
        denylist=load_denylist(_denylist_file(tmp_path)),
        interpreters=(sys.executable,),
        strict_import_hooks=False,
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "fakeoracle is importable" in result.detail


def test_a_denied_module_found_only_by_the_path_scan_fails(tmp_path: Path) -> None:
    """Layer 3, which catches what layer 2 cannot: a mount that is not on `sys.path` yet.

    A directory reachable inside the container but not currently importable becomes
    importable the moment anything appends it, so presence is the finding rather than
    resolvability.
    """
    mount = tmp_path / "mnt"
    (mount / "fakeoracle").mkdir(parents=True)
    result = probe(
        denylist=load_denylist(_denylist_file(tmp_path)),
        interpreters=(sys.executable,),
        extra_paths=(str(mount),),
        strict_import_hooks=False,
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "matches denied module" in result.detail


def test_a_clean_environment_passes(tmp_path: Path) -> None:
    """The control. Without it every test above is satisfied by a probe that always fails."""
    result = probe(
        denylist=load_denylist(_denylist_file(tmp_path)),
        interpreters=(sys.executable,),
        extra_paths=(str(tmp_path),),
        strict_import_hooks=False,
    )
    assert result.outcome is AssertionOutcome.PASSED


def test_zero_interpreters_is_not_a_pass(tmp_path: Path) -> None:
    """F15. A probe with nothing to probe reports what a clean probe reports."""
    result = probe(denylist=load_denylist(_denylist_file(tmp_path)), interpreters=())
    assert result.outcome is AssertionOutcome.NOT_EXECUTED


def test_an_unrunnable_interpreter_is_not_a_pass(tmp_path: Path) -> None:
    """Fail closed on the probe erroring, which is the half most often left as a skip."""
    result = probe(
        denylist=load_denylist(_denylist_file(tmp_path)),
        interpreters=(str(tmp_path / "no-such-python"),),
    )
    assert result.outcome is AssertionOutcome.NOT_EXECUTED


def test_import_hooks_fail_only_under_strictness(tmp_path: Path) -> None:
    """C13 inside the container; noise on a developer virtualenv, which carries `.pth`."""
    mount = tmp_path / "mnt"
    mount.mkdir()
    (mount / "anything.pth").write_text("import os\n", encoding="utf-8")
    denylist = load_denylist(_denylist_file(tmp_path))
    lenient = probe(
        denylist=denylist,
        interpreters=(sys.executable,),
        extra_paths=(str(mount),),
        strict_import_hooks=False,
    )
    strict = probe(
        denylist=denylist,
        interpreters=(sys.executable,),
        extra_paths=(str(mount),),
        strict_import_hooks=True,
    )
    assert lenient.outcome is AssertionOutcome.PASSED
    assert strict.outcome is AssertionOutcome.FAILED


def test_interpreter_discovery_rejects_non_interpreters(tmp_path: Path) -> None:
    """`python*` is not an interpreter glob.

    `python3.14-config` is a shell script that exits 1 on an unrecognised flag. Treating
    it as an interpreter made the probe report `not_executed` for an entire clean machine
    — fail-closed working correctly on a set that should never have contained it.
    """
    fake = tmp_path / "bin"
    fake.mkdir()
    for name in ("python3.13", "python3.13-config", "python-build", "pythonista"):
        target = fake / name
        target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        target.chmod(0o755)
    discovered = {Path(p).name for p in discover_interpreters((str(fake),))}
    assert "python3.13" in discovered
    assert "python3.13-config" not in discovered
    assert "python-build" not in discovered
    assert "pythonista" not in discovered


def test_closure_reports_denied_and_unclassified_separately(tmp_path: Path) -> None:
    """"We have not looked at this one" and "it carries no measure" are different facts."""
    findings = {
        f.distribution: f.classification
        for f in check_closure(
            ("numpy", "fake-oracle", "pytest"), load_denylist(_denylist_file(tmp_path))
        )
    }
    assert findings["fake-oracle"] is Classification.DENIED
    assert findings["pytest"] is Classification.UNCLASSIFIED
    assert "numpy" not in findings


# -------------------------------------------------------------------- the canary


def _policy(*targets: tuple[str, int]) -> NetworkPolicy:
    return NetworkPolicy(
        version=1,
        allowlist=(),
        canary_targets=tuple(
            CanaryTarget(host=h, port=p, kind="ip_literal", reason="test") for h, p in targets
        ),
        forbidden_allowlist_patterns=("pypi.org",),
    )


def _closed_port() -> int:
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_canary_fails_when_the_target_is_reachable() -> None:
    """The load-bearing test, and it owns its own listener.

    Depending on the machine's network state would make this suite pass on an unplugged
    laptop, which is the one condition under which a canary proves nothing.
    """
    with closing(socket.socket()) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        result = canary(policy=_policy(("127.0.0.1", listener.getsockname()[1])), timeout_s=2.0)
    assert result.outcome is AssertionOutcome.FAILED
    assert "REACHABLE" in result.detail


def test_canary_passes_when_the_target_is_unreachable() -> None:
    result = canary(policy=_policy(("127.0.0.1", _closed_port())), timeout_s=2.0)
    assert result.outcome is AssertionOutcome.PASSED


def test_canary_is_not_executed_when_its_control_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unreachable target and a broken socket layer are the same observation."""
    import harness.containment.egress as module

    monkeypatch.setattr(module, "_loopback_control", lambda _timeout: "simulated control failure")
    result = canary(policy=_policy(("127.0.0.1", _closed_port())), timeout_s=2.0)
    assert result.outcome is AssertionOutcome.NOT_EXECUTED
    assert "proves nothing" in result.detail


def test_a_policy_with_no_target_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "net.json"
    path.write_text(json.dumps({"version": 1, "canary_targets": []}), encoding="utf-8")
    with pytest.raises(NetworkPolicyError, match="no canary target"):
        load_network(path)


def test_a_policy_with_no_ip_literal_is_refused(tmp_path: Path) -> None:
    """DNS is not egress.

    A canary whose every target is a name reports the same green on a firewalled container
    and on one with an empty resolver and every port open.
    """
    path = tmp_path / "net.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "canary_targets": [
                    {"host": "pypi.org", "port": 443, "kind": "dns_name", "reason": "x"}
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(NetworkPolicyError, match="no ip_literal"):
        load_network(path)


def test_the_committed_network_policy_loads() -> None:
    policy = load_network()
    assert any(t.kind == "ip_literal" for t in policy.canary_targets)
    assert any(t.kind == "dns_name" for t in policy.canary_targets)


def test_a_registry_in_the_allowlist_fails() -> None:
    """CamoLeak exfiltrated through an allowlisted host; substring, not equality."""
    policy = NetworkPolicy(
        version=1,
        allowlist=("mirror.internal/pypi.org",),
        canary_targets=(CanaryTarget("1.1.1.1", 443, "ip_literal", "x"),),
        forbidden_allowlist_patterns=("pypi.org",),
    )
    assert check_allowlist(policy).outcome is AssertionOutcome.FAILED


def test_the_committed_allowlist_carries_no_registry() -> None:
    assert check_allowlist(load_network()).outcome is AssertionOutcome.PASSED
