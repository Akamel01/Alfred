"""C8, C9, C12, C13 — the assertions that need no executor vocabulary.

Four inside-the-container probes that rest on nothing about the selected executor, and so
are written for real rather than as shells: environment variables, the enumerated mount set,
the writable set, and the archives and resolver caches an offline install would need.

**Enumerated, never requested.** Every one of these compares what was found *inside* against
what was *specified*, in that direction. A probe that reported the dispatch spec back would
pass on a container that ignored it entirely — the difference between a mount set and a
mount intention.

**Each carries its own vacuity control, and the shape is the same in all four**: a scan that
examined nothing reports `NOT_EXECUTED`, never `PASSED`. Zero environment variables, zero
mounts, zero interpreters and zero roots are each the observation a broken probe produces,
and each is indistinguishable from a clean one unless the count is checked. That is F15
generalized, and `harness/containment/oracle_absence.py` already pays for it once.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from harness.containment.assertions import Assertion, AssertionOutcome

__all__ = [
    "ARCHIVE_SUFFIXES",
    "CACHE_DIR_NAMES",
    "SECRET_NAME_PATTERNS",
    "SECRET_VALUE_PATTERNS",
    "MountObservation",
    "assert_credentials_absent",
    "assert_mounts_match",
    "assert_no_archives_or_caches",
    "assert_writable_set",
]

# ------------------------------------------------------------------------------ C8

# Name-based first: the overwhelming majority of leaked credentials arrive in a variable
# whose name says so. Written as whole-word-ish fragments rather than exact names because
# the hazard is `GITHUB_TOKEN`, `GH_TOKEN`, `MY_APP_TOKEN` and the next one nobody listed.
SECRET_NAME_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(\A|_)(token|secret|password|passwd|credential|credentials)(_|\Z)",
        r"(\A|_)(api[_-]?key|access[_-]?key|secret[_-]?key|private[_-]?key)(_|\Z)",
        r"(\A|_)(auth|bearer|session[_-]?key|cookie)(_|\Z)",
        r"\A(AWS|GCP|AZURE|GITHUB|GH|GITLAB|NPM|PYPI|DOCKER|HF|OPENAI|ANTHROPIC)_",
        r"(\A|_)(pat|pgpassword|dsn|database_url|connection_string)(_|\Z)",
    )
)

# Value-based second, and it is not redundant. A credential in a variable named `X` is
# exactly the case the name patterns miss, and it is the case an exfiltration path would
# choose if it knew the name list. Shapes only — no attempt to validate a real credential,
# because a probe that phoned anything home to check would be the leak.
SECRET_VALUE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(pattern)
    for pattern in (
        r"\Agh[pousr]_[A-Za-z0-9]{16,}\Z",  # GitHub token families
        r"\Agithub_pat_[A-Za-z0-9_]{20,}\Z",
        r"\AAKIA[0-9A-Z]{16}\Z",  # AWS access key id
        r"\Axox[baprs]-[A-Za-z0-9-]{10,}\Z",  # Slack
        r"\Ask-[A-Za-z0-9_-]{20,}\Z",  # OpenAI-shaped
        r"\A-{5}BEGIN [A-Z ]*PRIVATE KEY-{5}",  # a key pasted whole
        r"\A[a-z]+://[^/\s:@]+:[^/\s:@]+@",  # credentials embedded in a URL
    )
)

ASSERTION_C8: Final = "C8"
ASSERTION_C9: Final = "C9"
ASSERTION_C12: Final = "C12"
ASSERTION_C13: Final = "C13"

# Names that are credential-shaped by pattern and are not credentials. Kept short and
# justified: a growing allowlist here is how the check stops checking.
_NAME_EXEMPT: Final[frozenset[str]] = frozenset(
    {
        # The probe's own switch. Present by construction in the suite that tests the probe.
        "ALFRED_REQUIRE_DB",
    }
)


def assert_credentials_absent(
    environment: Mapping[str, str] | None = None,
    *,
    exempt: Iterable[str] = (),
) -> Assertion:
    """C8 — no credential and no secret-bearing environment variable inside the container.

    The deliverable channel becoming the exfiltration channel is the documented failure: a
    pull request opened at 05:08, a token exfiltrated at 05:16, through the same credential
    the patch flow needed. A2 removes the credential from the container entirely, and this
    asserts the removal rather than trusting it.

    **Findings name the variable and never its value.** A probe that put the secret it found
    into an assertion detail would write it to the evidence chain, which is the one place a
    credential must never be durable.
    """
    env = dict(os.environ) if environment is None else dict(environment)
    exempted = _NAME_EXEMPT | frozenset(exempt)

    # The control. An empty environment is what a probe that failed to read one produces,
    # and it is indistinguishable from a clean container unless the count is checked.
    if not env:
        return Assertion(
            assertion_id=ASSERTION_C8,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail="the environment scan enumerated zero variables; a scan of nothing is not a pass",
        )

    by_name = sorted(
        name
        for name in env
        if name not in exempted and any(p.search(name) for p in SECRET_NAME_PATTERNS)
    )
    by_value = sorted(
        name
        for name in env
        if name not in exempted
        and name not in by_name
        and any(p.search(env[name]) for p in SECRET_VALUE_PATTERNS)
    )

    problems: list[str] = []
    if by_name:
        problems.append(f"secret-bearing names: {by_name}")
    if by_value:
        problems.append(f"credential-shaped values in: {by_value}")
    if problems:
        return Assertion(
            assertion_id=ASSERTION_C8,
            outcome=AssertionOutcome.FAILED,
            detail="; ".join(problems),
        )
    return Assertion(
        assertion_id=ASSERTION_C8,
        outcome=AssertionOutcome.PASSED,
        detail=f"{len(env)} environment variables, none credential-shaped by name or value",
    )


# ------------------------------------------------------------------------------ C9


@dataclass(frozen=True)
class MountObservation:
    """One mount as enumerated **inside** the container.

    `read_only` is the mode as the kernel reports it, not as the spec requested it. The two
    differing is precisely what this assertion exists to find.
    """

    path: str
    read_only: bool


def assert_mounts_match(
    observed: Sequence[MountObservation],
    specified: Sequence[MountObservation],
) -> Assertion:
    """C9 — the mount set inside the container equals the dispatch spec exactly, mode for mode.

    **Set equality in both directions, and the mode is part of the identity.** An extra mount
    is an agent-chosen read path (A9) or an over-broad harness mount; a missing one is a
    dispatch that did not take; a mount present in both at different modes is the quietest of
    the three, because every path check downstream still passes.
    """
    if not specified:
        return Assertion(
            assertion_id=ASSERTION_C9,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail="the dispatch spec declares zero mounts; there is nothing to compare against",
        )
    if not observed:
        return Assertion(
            assertion_id=ASSERTION_C9,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail="the in-container enumeration returned zero mounts; the probe did not run",
        )

    observed_modes = {m.path: m.read_only for m in observed}
    specified_modes = {m.path: m.read_only for m in specified}

    problems: list[str] = []
    extra = sorted(set(observed_modes) - set(specified_modes))
    if extra:
        problems.append(f"mounted but not specified: {extra}")
    missing = sorted(set(specified_modes) - set(observed_modes))
    if missing:
        problems.append(f"specified but not mounted: {missing}")
    mismatched = sorted(
        f"{path}(observed {'ro' if observed_modes[path] else 'rw'}, "
        f"specified {'ro' if specified_modes[path] else 'rw'})"
        for path in set(observed_modes) & set(specified_modes)
        if observed_modes[path] != specified_modes[path]
    )
    if mismatched:
        problems.append(f"mode differs: {mismatched}")

    if problems:
        return Assertion(
            assertion_id=ASSERTION_C9, outcome=AssertionOutcome.FAILED, detail="; ".join(problems)
        )
    return Assertion(
        assertion_id=ASSERTION_C9,
        outcome=AssertionOutcome.PASSED,
        detail=f"{len(observed)} mounts match the dispatch spec, mode for mode",
    )


# ----------------------------------------------------------------------------- C12


def assert_writable_set(
    observed: Sequence[MountObservation],
    *,
    writable_roots: Sequence[str],
    interpreter_paths: Sequence[str],
) -> Assertion:
    """C12 — writable is exactly the repo tree and the patch volume; interpreters read-only.

    Catches a mid-run install into `site-packages`, which would put an oracle inside the
    container after every boot-time probe has passed. C13 covers the archives such an install
    would read from and C14 re-asserts both at the end; this is the write path itself.

    `interpreter_paths` are the paths `oracle_absence.discover_interpreters` finds. Any of
    them **outside** a writable root must be mounted read-only; one inside a writable root is
    a finding in its own right, because an interpreter the agent can rewrite is an import
    hook with extra steps.
    """
    if not observed:
        return Assertion(
            assertion_id=ASSERTION_C12,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail="the in-container enumeration returned zero mounts; the probe did not run",
        )
    if not writable_roots:
        return Assertion(
            assertion_id=ASSERTION_C12,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                "no writable roots were declared; with an empty declaration every writable "
                "mount reads as unexpected and the assertion would fail for the wrong reason"
            ),
        )

    roots = tuple(Path(root) for root in writable_roots)

    def _under_a_root(path: str) -> bool:
        candidate = Path(path)
        return any(candidate == root or root in candidate.parents for root in roots)

    problems: list[str] = []
    unexpected_writable = sorted(
        m.path for m in observed if not m.read_only and not _under_a_root(m.path)
    )
    if unexpected_writable:
        problems.append(f"writable outside the declared roots: {unexpected_writable}")

    if not interpreter_paths:
        problems.append(
            "zero interpreters were enumerated; the read-only half of this assertion "
            "scanned nothing (F15)"
        )
    else:
        modes = {m.path: m.read_only for m in observed}

        def _mode_of(path: str) -> bool | None:
            candidate = Path(path)
            covering = [
                mount
                for mount in modes
                if candidate == Path(mount) or Path(mount) in candidate.parents
            ]
            if not covering:
                return None
            # The longest covering mount wins: a read-only tree with a writable subtree
            # mounted over it is writable at that subtree, and the shorter path would lie.
            return modes[max(covering, key=len)]

        for interpreter in interpreter_paths:
            if _under_a_root(interpreter):
                problems.append(f"interpreter {interpreter} sits inside a writable root")
                continue
            mode = _mode_of(interpreter)
            if mode is None:
                problems.append(f"interpreter {interpreter} is covered by no enumerated mount")
            elif not mode:
                problems.append(f"interpreter {interpreter} is writable")

    if problems:
        return Assertion(
            assertion_id=ASSERTION_C12, outcome=AssertionOutcome.FAILED, detail="; ".join(problems)
        )
    return Assertion(
        assertion_id=ASSERTION_C12,
        outcome=AssertionOutcome.PASSED,
        detail=(
            f"writable set is exactly {sorted(writable_roots)}; "
            f"{len(interpreter_paths)} interpreter path(s) read-only"
        ),
    )


# ----------------------------------------------------------------------------- C13

ARCHIVE_SUFFIXES: Final[tuple[str, ...]] = (
    ".whl",
    ".tar.gz",
    ".tgz",
    ".zip",
    ".tar.bz2",
    ".tar.xz",
    ".egg",
)

CACHE_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        "pip",
        "uv",
        ".uv-cache",
        "wheels",
        "http",
        "http-v2",
        "poetry",
        "pdm",
        "npm",
        ".npm",
        "yarn",
    }
)


def assert_no_archives_or_caches(roots: Sequence[Path]) -> Assertion:
    """C13 — no package archives and no resolver caches under any mount.

    The point is acquisition closure, not tidiness. C6 stops the oracle being fetched
    mid-run; this stops it being installed from something already inside. Together with C12
    they are what let a boot-time absence assertion hold for a whole run instead of only for
    its first instant.

    A cache directory counts on its **name**, not on its contents: an empty `pip` cache
    directory is a resolver that has been configured to have one, and the next thing it does
    is fill it.
    """
    if not roots:
        return Assertion(
            assertion_id=ASSERTION_C13,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail="zero roots were supplied; a walk over nothing is not a clean walk",
        )

    scanned = 0
    archives: list[str] = []
    caches: list[str] = []
    unreadable: list[str] = []

    for root in roots:
        if not root.exists():
            unreadable.append(f"{root} does not exist")
            continue
        try:
            for path in root.rglob("*"):
                scanned += 1
                name = path.name
                if path.is_dir():
                    if name in CACHE_DIR_NAMES or name.endswith((".cache", "-cache")):
                        caches.append(str(path))
                elif any(name.endswith(suffix) for suffix in ARCHIVE_SUFFIXES):
                    archives.append(str(path))
        except OSError as exc:
            # Never swallowed into a pass. A tree that could not be walked is a tree whose
            # contents are unknown, which is the same as an unproven control.
            unreadable.append(f"{root}: {exc}")

    if unreadable:
        return Assertion(
            assertion_id=ASSERTION_C13,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=f"the walk did not complete: {unreadable}",
        )
    if scanned == 0:
        return Assertion(
            assertion_id=ASSERTION_C13,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=f"the walk over {[str(r) for r in roots]} visited zero entries",
        )

    problems: list[str] = []
    if archives:
        problems.append(f"package archives present: {sorted(archives)[:10]}")
    if caches:
        problems.append(f"resolver caches present: {sorted(caches)[:10]}")
    if problems:
        return Assertion(
            assertion_id=ASSERTION_C13, outcome=AssertionOutcome.FAILED, detail="; ".join(problems)
        )
    return Assertion(
        assertion_id=ASSERTION_C13,
        outcome=AssertionOutcome.PASSED,
        detail=f"{scanned} entries under {len(roots)} root(s); no archive, no resolver cache",
    )
