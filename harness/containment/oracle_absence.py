"""C7 — the oracle is absent, asserted rather than assumed.

If `commonroad_crime` is importable where agent-authored code runs, a wrapper delegating
to it passes the published constants, every P3 resampled perturbation and every P4/P5
invariance and degeneracy property — with a clean transcript and no dishonesty anywhere in
the loop. Merge rate then measures delegation. **This runs in the agent container and in
the criterion environment**, because agent-authored code executes in both, and asserting
absence only in the first leaves the delegation path open at the moment the verdict is
computed.

**`find_spec`, never `import`.** Importing a module to learn whether it is importable
executes its module-level code inside the sandbox, which is the one thing the probe exists
to prevent happening. Only top-level names are probed, and that is load-bearing:
`find_spec("a.b")` imports `a` to find `b`, while `find_spec("a")` imports nothing.

**Every failure path is fail-closed, the probe erroring included** (F15). An enumeration
that raised, an interpreter that could not be run, output that would not parse — all
`not_executed`, which `require_all_passed` treats exactly as failed. Finding **zero
interpreters** is also `not_executed`: a probe with nothing to probe reports the same
thing as a probe that found nothing wrong, and this project has paid for that confusion
more than once.

**What this cannot close, named so no merge rate is read as stronger than it is** (D50 as
amended). Reconstruction from model weights — if the oracle's source or published values
sit in the lane's training data, the agent reproduces them without importing anything. A
renamed, reformatted vendored copy — these checks are name- and hash-based, never
semantic. Non-Python paths — a shared object through `ctypes`, a subprocess binary, a data
file of constants. And a compromised base image, which the Threat Model puts out of scope.
The probe closes acquisition, declaration, presence and naming. It does not close meaning.

**Every return records its observations**, including the fail-closed ones. C7 is in
`REASSERTED`, and `reassert.compare` diffs observed values across boot and end of run — so
what this probe records decides what a re-assertion can see. Three of the values are the
whole reason:

- `denylist_version` and `denylist_sha256`. **Two passes under two different denylists are
  not a re-assertion.** A policy edited mid-run — the oracle's name removed from it — leaves
  both ends green and the container unchanged, and nothing else here would notice.
- `interpreters`. A Python that appeared during the run is an import path boot never probed.
  The end-of-run probe finds it, probes it, and passes; only the set itself shows the change.
- `import_paths`. The same argument one level down: `sys.path` grown by a `.pth`, an
  environment variable, or a `site` directory that did not exist at boot.

Findings are recorded as **counts**, not listings — `detail` carries the names, and a
listing of every hit would drift on ordering alone. The values above are recorded in full,
because for them the set *is* the finding.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from functools import partial
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from harness.containment.assertions import Assertion, AssertionOutcome
from harness.containment.denylist import Classification, Denylist, _normalize

ASSERTION_ID: Final = "C7"

ARCHIVE_SUFFIXES: Final = (".whl", ".tar.gz", ".tgz", ".zip")
IMPORT_HOOK_NAMES: Final = frozenset({"sitecustomize.py", "usercustomize.py"})

# Runs inside each discovered interpreter. Prints one JSON object and imports nothing it
# is asked about: `find_spec` on a top-level name resolves without executing the module.
_PROBE_SOURCE: Final = r"""
import json, sys
out = {"executable": sys.executable, "path": [p for p in sys.path if p], "found": [], "dists": [], "error": None}
try:
    import importlib.util
    for name in json.loads(sys.argv[1]):
        try:
            if importlib.util.find_spec(name) is not None:
                out["found"].append(name)
        except (ImportError, ValueError):
            # A denied module whose spec lookup raises is absent, not present. Recorded
            # as absent deliberately: the failure that matters is a spec that resolves.
            pass
    import importlib.metadata
    out["dists"] = sorted({d.metadata["Name"] for d in importlib.metadata.distributions()
                           if d.metadata and d.metadata["Name"]})
except Exception as exc:
    out["error"] = f"{type(exc).__name__}: {exc}"
print(json.dumps(out))
"""


@dataclass
class ProbeResult:
    """What the probe saw, before it becomes an assertion."""

    interpreters: list[str] = field(default_factory=list)
    denied_findings: list[str] = field(default_factory=list)
    hook_findings: list[str] = field(default_factory=list)
    scanned_paths: int = 0
    error: str | None = None


# `python*` is not an interpreter glob, and discovering that cost a fail-closed probe on
# the first real machine it ran against: it matched `python3.14-config`, a shell script
# that exits 1 on an unrecognised flag, and the probe correctly refused to treat "could
# not run" as "nothing found" — reporting `not_executed` for the whole container because
# of a build-configuration helper. The membership rule is therefore explicit. Deciding
# what is in the interpreter set is a different question from failing closed on a member
# that cannot be probed, and collapsing the two makes the probe unusable.
_INTERPRETER_NAME: Final = re.compile(r"^python(\d+(\.\d+)?t?)?(\.exe)?$")


def discover_interpreters(search: tuple[str, ...] | None = None) -> list[str]:
    """Every Python on PATH, plus the one running this code.

    Enumerated rather than assumed. A container with a system interpreter and a virtualenv
    has two import paths, and a probe checking only the one it happens to run under
    reports on half the container.
    """
    found: dict[str, None] = {os.path.realpath(sys.executable): None}
    directories = search if search is not None else tuple(os.environ.get("PATH", "").split(os.pathsep))
    for directory in directories:
        if not directory:
            continue
        base = Path(directory)
        if not base.is_dir():
            continue
        for entry in sorted(base.glob("python*")):
            if not _INTERPRETER_NAME.match(entry.name):
                continue
            if entry.is_file() and os.access(entry, os.X_OK):
                found.setdefault(os.path.realpath(entry), None)
    return list(found)


def _run_import_probe(interpreter: str, modules: tuple[str, ...], denylist: Denylist) -> tuple[list[str], list[str], str | None]:
    try:
        completed = subprocess.run(
            [interpreter, "-c", _PROBE_SOURCE, json.dumps(list(modules))],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], [], f"{interpreter}: probe could not run: {exc}"

    if completed.returncode != 0:
        return [], [], f"{interpreter}: probe exited {completed.returncode}: {completed.stderr.strip()[:400]}"
    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return [], [], f"{interpreter}: probe produced no parseable output"
    if payload.get("error"):
        return [], [], f"{interpreter}: {payload['error']}"

    findings = [f"{interpreter}: {name} is importable" for name in payload.get("found", [])]
    findings += [
        f"{interpreter}: distribution {name} is installed"
        for name in payload.get("dists", [])
        if _normalize(str(name)) in denylist.denied_distributions
    ]
    return findings, [str(p) for p in payload.get("path", [])], None


def _scan_paths(paths: tuple[str, ...], denylist: Denylist) -> tuple[list[str], list[str], int, str | None]:
    denied_names = denylist.denied_modules
    denied_dists = denylist.denied_distributions
    denied_findings: list[str] = []
    hook_findings: list[str] = []
    scanned = 0

    for raw in paths:
        base = Path(raw)
        if not base.is_dir():
            continue
        scanned += 1
        try:
            entries = sorted(base.iterdir())
        except OSError as exc:
            # Fail closed. An unreadable directory on the import path is a directory the
            # probe cannot speak for, and "could not look" is not "nothing there".
            return [], [], scanned, f"cannot enumerate {base}: {exc}"

        for entry in entries:
            name = entry.name
            stem = name.removesuffix(".py")
            if stem in denied_names or name in denied_names:
                denied_findings.append(f"{entry}: matches denied module {stem}")
            if name.endswith((".dist-info", ".egg-info")):
                distribution = _normalize(name.rsplit("-", 1)[0] if "-" in name else name)
                if distribution in denied_dists:
                    denied_findings.append(f"{entry}: metadata for a denied distribution")
            if name in IMPORT_HOOK_NAMES or name.endswith(".pth"):
                hook_findings.append(f"{entry}: import hook on the effective path")
            if name.endswith(ARCHIVE_SUFFIXES):
                hook_findings.append(f"{entry}: package archive under an import path (C13)")
    return denied_findings, hook_findings, scanned, None


def _observed(
    denylist: Denylist,
    *,
    strict_import_hooks: bool,
    interpreters: Sequence[str] = (),
    import_paths: Sequence[str] = (),
    scanned_paths: int | None = None,
    denied_findings: int | None = None,
    hook_findings: int | None = None,
) -> dict[str, str]:
    """What C7 saw, in the shape `reassert.compare` diffs.

    The denylist identity and the strictness flag are recorded on **every** return, including
    the fail-closed ones, because they are the two ways C7 can be weakened without any
    observable change to the container. Everything else is recorded only once it is known:
    the alternative is a placeholder that reads as an observation, and a key whose value is
    a stand-in for "not reached yet" would diff against a real one as though something moved.
    """
    values = {
        "denylist_version": str(denylist.version),
        "denylist_sha256": denylist.sha256,
        "denied_module_count": str(len(denylist.denied_modules)),
        "denied_distribution_count": str(len(denylist.denied_distributions)),
        "strict_import_hooks": str(strict_import_hooks).lower(),
    }
    if interpreters:
        values["interpreters"] = ",".join(sorted(interpreters))
    if import_paths:
        values["import_paths"] = ",".join(sorted(set(import_paths)))
    if scanned_paths is not None:
        values["scanned_paths"] = str(scanned_paths)
    if denied_findings is not None:
        values["denied_findings"] = str(denied_findings)
    if hook_findings is not None:
        values["hook_findings"] = str(hook_findings)
    return values


def probe(
    *,
    denylist: Denylist,
    interpreters: tuple[str, ...] | None = None,
    extra_paths: tuple[str, ...] = (),
    strict_import_hooks: bool = True,
) -> Assertion:
    """Run layers 2 and 3 and return one assertion.

    `strict_import_hooks` is True inside the container, where any `.pth`, `sitecustomize`
    or package archive on the import path is a finding under C13. It exists as a parameter
    because a developer virtualenv legitimately carries `.pth` files, and a probe that
    cannot be run outside the container is a probe nobody runs until it matters.
    """
    result = ProbeResult()
    result.interpreters = list(interpreters) if interpreters is not None else discover_interpreters()

    seen = partial(_observed, denylist, strict_import_hooks=strict_import_hooks)

    if not result.interpreters:
        return Assertion(
            ASSERTION_ID,
            AssertionOutcome.NOT_EXECUTED,
            "no interpreter could be enumerated; a probe with nothing to probe is not a pass (F15)",
            observed=seen(),
        )

    modules = tuple(sorted(denylist.denied_modules))
    effective_paths: list[str] = list(extra_paths)
    for interpreter in result.interpreters:
        findings, sys_path, error = _run_import_probe(interpreter, modules, denylist)
        if error:
            # The interpreter set is recorded even though the probe failed on one of them:
            # which interpreters were *found* is the fact that says whether the container
            # changed, and it is known here whether or not any of them could be run.
            return Assertion(
                ASSERTION_ID,
                AssertionOutcome.NOT_EXECUTED,
                error,
                observed=seen(interpreters=result.interpreters),
            )
        result.denied_findings.extend(findings)
        effective_paths.extend(sys_path)

    denied, hooks, scanned, scan_error = _scan_paths(tuple(dict.fromkeys(effective_paths)), denylist)
    if scan_error:
        return Assertion(
            ASSERTION_ID,
            AssertionOutcome.NOT_EXECUTED,
            scan_error,
            observed=seen(
                interpreters=result.interpreters,
                import_paths=effective_paths,
                scanned_paths=scanned,
            ),
        )
    result.denied_findings.extend(denied)
    result.hook_findings.extend(hooks)
    result.scanned_paths = scanned

    observed = seen(
        interpreters=result.interpreters,
        import_paths=effective_paths,
        scanned_paths=result.scanned_paths,
        denied_findings=len(result.denied_findings),
        hook_findings=len(result.hook_findings),
    )

    if result.scanned_paths == 0:
        return Assertion(
            ASSERTION_ID,
            AssertionOutcome.NOT_EXECUTED,
            "no import path directory was scanned; the path scan had nothing to look at",
            observed=observed,
        )

    problems = list(result.denied_findings)
    if strict_import_hooks:
        problems += result.hook_findings
    if problems:
        return Assertion(
            ASSERTION_ID, AssertionOutcome.FAILED, "; ".join(problems[:20]), observed=observed
        )

    return Assertion(
        ASSERTION_ID,
        AssertionOutcome.PASSED,
        f"denylist v{denylist.version} ({denylist.sha256[:12]}): "
        f"{len(modules)} module(s) absent from {len(result.interpreters)} interpreter(s), "
        f"{result.scanned_paths} path(s) scanned",
        observed=observed,
    )


# ------------------------------------------------------------------ layer 1, outside


@dataclass(frozen=True)
class ClosureFinding:
    distribution: str
    classification: Classification


def check_closure(distributions: tuple[str, ...], denylist: Denylist) -> tuple[ClosureFinding, ...]:
    """Layer 1: compare a resolved dependency closure against the policy, at image build.

    Returns every entry that is **not** permitted substrate — denied entries and
    unclassified ones both. Unclassified is returned rather than silently allowed because
    "we have not looked at this one" and "we looked and it carries no measure" are
    different facts, and only the second is a decision. The caller decides what an
    unclassified entry costs; what it must not do is confuse the two.
    """
    findings: list[ClosureFinding] = []
    for distribution in sorted(set(distributions)):
        classification = denylist.classify(distribution=distribution)
        if classification is not Classification.PERMITTED_SUBSTRATE:
            findings.append(ClosureFinding(distribution, classification))
    return tuple(findings)
