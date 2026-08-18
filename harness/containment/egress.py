"""C6 — the egress canary, and the control that stops it being vacuous.

**A7 turns decision 12 from a policy into a machine-checkable criterion.** The run refuses
to start unless a known non-allowlisted connection *fails*. The reason is a measured base
rate rather than a hypothetical: Anthropic's own evaluation harness recorded that "a
misconfiguration left the machines that Claude accessed as part of the evaluation with
live internet access." That is what "we configured deny-by-default" is worth unverified.

**Enforcement is outside; verification is inside.** `nftables` default-drop sits in the
host network namespace, because environment-variable proxy configuration is advisory and
bypassable — a policy asserted by reading configuration asserts nothing. The canary needs
no privilege at all: it only has to try, and fail.

**The control is what makes the canary mean something.** A probe that reports "the target
was unreachable" reports the same thing when egress is blocked and when its own socket
layer is broken — a missing library, a chroot with no `/etc`, a `socket` call that raises
before it reaches the network. So the canary first connects to a loopback listener it
starts itself and requires that to *succeed*. If the control fails, the result is
`not_executed`, never `passed`.

**What the canary cannot establish, stated so a green report is not over-quoted.** It
proves the named targets are unreachable. It does **not** prove a policy is the reason: a
container with no network interface at all passes identically. Distinguishing the two
needs a reachable allowlisted host, and the Phase 1 allowlist is empty by design — so this
assertion is evidence of containment and not evidence that the allowlist mechanism works.
When the allowlist gains its first entry, that entry becomes the second control and this
paragraph should shrink.

CamoLeak (CVSS 9.6) exfiltrated through an *allowlisted* host, so the allowlist itself is
checked against a forbidden-pattern set: no package registry may appear in it. The runtime
image is pulled outside the sandbox network namespace precisely so no registry needs to be
reachable from inside, and one line here would undo that without touching another control.
"""

from __future__ import annotations

import json
import socket
import threading
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from harness.containment.assertions import Assertion, AssertionOutcome

CANARY_ASSERTION_ID: Final = "C6"
ALLOWLIST_ASSERTION_ID: Final = "C6.allowlist"
DEFAULT_PATH: Final = Path(__file__).resolve().parents[2] / "policy" / "network-allowlist.json"

DEFAULT_TIMEOUT_S: Final = 3.0
CONTROL_TIMEOUT_S: Final = 2.0


class NetworkPolicyError(RuntimeError):
    """The policy could not be loaded. Fail closed (F14): nothing dispatches."""


@dataclass(frozen=True)
class CanaryTarget:
    host: str
    port: int
    kind: str
    reason: str


@dataclass(frozen=True)
class NetworkPolicy:
    version: int
    allowlist: tuple[str, ...]
    canary_targets: tuple[CanaryTarget, ...]
    forbidden_allowlist_patterns: tuple[str, ...]


def load(path: Path = DEFAULT_PATH) -> NetworkPolicy:
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise NetworkPolicyError(f"cannot read {path}: {exc}") from exc
    except ValueError as exc:
        raise NetworkPolicyError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise NetworkPolicyError(f"{path} is not an object")

    try:
        version = int(raw["version"])
        targets = tuple(
            CanaryTarget(
                host=str(t["host"]), port=int(t["port"]), kind=str(t["kind"]), reason=str(t["reason"])
            )
            for t in raw["canary_targets"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise NetworkPolicyError(f"{path} is malformed: {exc}") from exc

    if not targets:
        # A canary with no target passes unconditionally, which is the exact shape of a
        # control that has stopped working while still reporting green.
        raise NetworkPolicyError(f"{path} declares no canary target")
    if not any(t.kind == "ip_literal" for t in targets):
        # Without one, every failure could be a resolver failure, and a container with an
        # empty resolv.conf and every port open would read identically to a firewalled one.
        raise NetworkPolicyError(f"{path} declares no ip_literal target; DNS is not egress")

    return NetworkPolicy(
        version=version,
        allowlist=tuple(str(h) for h in raw.get("allowlist", [])),
        canary_targets=targets,
        forbidden_allowlist_patterns=tuple(str(p) for p in raw.get("forbidden_allowlist_patterns", [])),
    )


def _connect(host: str, port: int, timeout_s: float) -> str | None:
    """None if the connection succeeded; a reason string if it did not."""
    try:
        with closing(socket.create_connection((host, port), timeout=timeout_s)):
            return None
    except OSError as exc:
        return f"{type(exc).__name__}: {exc}"


def _loopback_control(timeout_s: float) -> str | None:
    """Prove the probe can open a socket at all. None on success, a reason on failure."""
    try:
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
    except OSError as exc:
        return f"could not bind a loopback listener: {exc}"

    with closing(listener):
        accepted: list[socket.socket] = []
        thread = threading.Thread(target=lambda: accepted.append(listener.accept()[0]), daemon=True)
        thread.start()
        failure = _connect("127.0.0.1", listener.getsockname()[1], timeout_s)
        thread.join(timeout=timeout_s)
        for sock in accepted:
            sock.close()
    return None if failure is None else f"loopback connect failed: {failure}"


def canary(
    *, policy: NetworkPolicy, timeout_s: float = DEFAULT_TIMEOUT_S, run_control: bool = True
) -> Assertion:
    """Require every canary target to be unreachable, with the control run first.

    `run_control=False` exists only for the suite that has to demonstrate what happens
    when the control fails. It is never used in a real boot: without the control, an
    unreachable target and a broken probe are the same observation.
    """
    if run_control:
        control_failure = _loopback_control(CONTROL_TIMEOUT_S)
        if control_failure is not None:
            return Assertion(
                CANARY_ASSERTION_ID,
                AssertionOutcome.NOT_EXECUTED,
                f"canary control failed, so an unreachable target proves nothing: {control_failure}",
            )

    reached: list[str] = []
    for target in policy.canary_targets:
        failure = _connect(target.host, target.port, timeout_s)
        if failure is None:
            reached.append(f"{target.host}:{target.port} ({target.kind}) is REACHABLE")

    if reached:
        return Assertion(CANARY_ASSERTION_ID, AssertionOutcome.FAILED, "; ".join(reached))

    kinds = sorted({t.kind for t in policy.canary_targets})
    return Assertion(
        CANARY_ASSERTION_ID,
        AssertionOutcome.PASSED,
        f"policy v{policy.version}: {len(policy.canary_targets)} target(s) unreachable "
        f"across {', '.join(kinds)}; loopback control connected",
    )


def check_allowlist(policy: NetworkPolicy) -> Assertion:
    """No package registry in the allowlist (C6), matched by substring.

    Substring rather than equality: `files.pythonhosted.org` and a mirror spelled
    `mirror.internal/pypi.org` are the same reachability, and an equality check on
    hostnames is defeated by any prefix anyone finds convenient.
    """
    hits = [
        f"{host} matches forbidden pattern {pattern}"
        for host in policy.allowlist
        for pattern in policy.forbidden_allowlist_patterns
        if pattern in host
    ]
    if hits:
        return Assertion(ALLOWLIST_ASSERTION_ID, AssertionOutcome.FAILED, "; ".join(hits))
    return Assertion(
        ALLOWLIST_ASSERTION_ID,
        AssertionOutcome.PASSED,
        f"{len(policy.allowlist)} allowlisted host(s), none matching "
        f"{len(policy.forbidden_allowlist_patterns)} forbidden pattern(s)",
    )
