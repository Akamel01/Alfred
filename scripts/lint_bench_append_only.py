#!/usr/bin/env python3
"""`bench/results/` and `bench/fingerprints/` are append-only. This is what says so.

ADR-0038 decided *harden* and named `scripts/lint_protected_paths.py` as the enforcement.
That file has never existed. What ran instead was an inline step in
`.github/workflows/gates.yml`:

    modified=$(git diff --name-only HEAD~1 -- bench/results/ bench/fingerprints/ 2>/dev/null || true)
    if [ -n "$modified" ]; then ... exit 1; fi

which was wrong in four ways, each of which this module fixes and names:

1. **It was inverted.** `--name-only` does not filter by status, so an *added* file printed
   exactly like a modified one and the step exited 1 — while its own echo promised "Only new
   files (status 'A') are allowed". The next legitimate bench result committed would have
   failed CI. Here the filter is explicit: `--diff-filter=MDR`.
2. **`HEAD~1` saw one commit.** A modification in any non-tip commit of a multi-commit push
   was never diffed. Here the range is the merge base with the branch being merged into.
3. **`2>/dev/null || true` failed open.** A `git` error produced an empty result and reported
   success. Here a git failure raises.
4. **It had no vacuity guard.** `git log --oneline -- bench/results/` returns one commit ever
   and `bench/fingerprints/` does not exist in the tree, so the step had never once seen a
   real diff — green meant "never ran". See `_corpus` for what replaces that.

**The vacuity question here is not the obvious one.** A commit that changes nothing under
these prefixes is the common case and is not vacuous — reporting "0 changed paths" is a true
answer to a real question. What *is* vacuous is guarding an empty corpus: if nothing is
tracked under any protected prefix, this check cannot fail and protects nothing. So D57 is
applied to the corpus, not to the diff, and the per-prefix counts are printed on every run so
that an absent prefix is visible rather than silent.

Exit 0 clean, 1 on a finding, an unresolvable base, an empty corpus, or a git failure.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lintkit import REPO_ROOT, self_test_exit, vacuity_guard  # noqa: E402

#: The append-only prefixes. `policy/protected-paths.json` names both; this list is stated
#: here rather than read from it because that file is the *write*-protection set and answers
#: a different question — a prefix can leave this list while staying protected, and the two
#: drifting apart silently is worse than one honest duplication with a comment saying so.
APPEND_ONLY: Final[tuple[str, ...]] = ("bench/results/", "bench/fingerprints/")

#: Modified, Deleted, Renamed. Additions are the whole point of append-only and must pass.
#: `C` (copied) is deliberately absent: a copy adds a path without altering its source.
DIFF_FILTER: Final = "MDR"

BASE_CANDIDATES: Final[tuple[str, ...]] = ("origin/main", "main", "HEAD")


@dataclass
class Findings:
    """What the check compared and what it found.

    `scanned` is the number of changed paths examined under the append-only prefixes;
    `tracked` is the size of the corpus being protected. Both are printed because they
    answer different questions, and the second is the one that was never asked before.
    """

    scanned: int = 0
    tracked: int = 0
    base: str = "unresolved"
    violations: list[str] = field(default_factory=list)


def _git(args: list[str], *, cwd: Path) -> str:
    """A git invocation whose failure is a failure.

    The predecessor's `2>/dev/null || true` is the specific thing this refuses: a check
    that cannot run must not report the same thing as a check that ran and found nothing.
    """
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _resolve_base(cwd: Path) -> str | None:
    """First resolvable of `origin/$GITHUB_BASE_REF`, `origin/main`, `main`, `HEAD`.

    The order matches `lint_adr_numbers.py`: a PR is checked against what it merges into,
    a local branch against its home, and a tree with no forked base against itself. A base
    that resolves to nothing is a failure rather than a skip.
    """
    candidates = list(BASE_CANDIDATES)
    if base_ref := os.environ.get("GITHUB_BASE_REF"):
        candidates.insert(0, f"origin/{base_ref}")
    for ref in candidates:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            return ref
    return None


def _corpus(cwd: Path) -> tuple[int, list[str]]:
    """Tracked file count under the append-only prefixes, and the per-prefix report.

    The count is what D57 is applied to. An empty corpus means the guarantee is protecting
    nothing, which is exactly the state the predecessor sat in unnoticed.
    """
    total = 0
    report: list[str] = []
    for prefix in APPEND_ONLY:
        out = _git(["ls-files", "--", prefix], cwd=cwd)
        n = len([line for line in out.splitlines() if line.strip()])
        total += n
        report.append(f"{prefix}{n}" if n else f"{prefix}absent")
    return total, report


def check(cwd: Path = REPO_ROOT) -> Findings:
    """Every non-addition to an append-only prefix, against the merge base."""
    findings = Findings()
    findings.tracked, _ = _corpus(cwd)

    base = _resolve_base(cwd)
    if base is None:
        findings.violations.append(
            "no base ref resolved — a check with nothing to compare against cannot pass"
        )
        return findings
    findings.base = base

    # `HEAD` is the last candidate and means no forked base was found. Comparing a tree
    # against itself finds nothing and reports success, which is indistinguishable from a
    # clean diff. Locally that is the honest answer for an unforked tree; in CI it means
    # the checkout was shallow and the guarantee silently evaporated, so it fails there.
    if base == "HEAD" and os.environ.get("GITHUB_ACTIONS") == "true":
        findings.violations.append(
            "base resolved to HEAD in CI — a self-comparison cannot detect a modification; "
            "the checkout needs fetch-depth: 0 so origin/main resolves"
        )
        return findings

    out = _git(
        [
            "diff",
            "--name-status",
            f"--diff-filter={DIFF_FILTER}",
            f"{base}...HEAD",
            "--",
            *APPEND_ONLY,
        ],
        cwd=cwd,
    )
    for line in out.splitlines():
        if not line.strip():
            continue
        findings.scanned += 1
        status, _, path = line.partition("\t")
        findings.violations.append(
            f"{path.strip()} has status {status.strip()} against {base} — "
            f"{APPEND_ONLY[0]} and {APPEND_ONLY[1]} are append-only (ADR-0038)"
        )
    return findings


def _run(cwd: Path = REPO_ROOT) -> int:
    try:
        findings = check(cwd)
    except RuntimeError as exc:
        sys.stdout.write(f"FAIL bench append-only — {exc}\n")
        return 1

    _, report = _corpus(cwd)
    corpus = ", ".join(report)

    if vacuity_guard(
        findings.tracked,
        "FAIL VACUOUS bench append-only: no file is tracked under "
        f"{' or '.join(APPEND_ONLY)}, so this check protects nothing ({corpus})\n",
    ):
        return 1

    if findings.violations:
        sys.stdout.write("FAIL bench append-only — records are immutable once written:\n")
        for line in findings.violations:
            sys.stdout.write(f"  {line}\n")
        sys.stdout.write(
            f"\nOnly additions are permitted. {findings.tracked} tracked ({corpus}).\n"
        )
        return 1

    sys.stdout.write(
        f"OK bench append-only — {findings.tracked} tracked record(s) ({corpus}); "
        f"0 modifications, deletions or renames against {findings.base}\n"
    )
    return 0


# ----------------------------------------------------------------------------- self-test


def _scratch(tmp: Path) -> Path:
    """A repository with one committed record, standing in for `bench/results/`."""
    repo = tmp / "repo"
    (repo / "bench" / "results").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "--initial-branch=main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "bench" / "results" / "seed1.json").write_text('{"seed": 1}\n')
    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-qm", "base"], cwd=repo)
    # Work happens on a branch, as it does in the real repository. Without this the base
    # resolves to `main`, `main...HEAD` is empty, and every arm passes for the wrong
    # reason — which the self-test caught on its first run.
    _git(["checkout", "-q", "-b", "work"], cwd=repo)
    return repo


def _self_test() -> int:
    """Two-sided, plus the vacuity arm.

    A one-sided self-test is how the predecessor stayed broken: nothing ever asserted that
    an *addition* passes, so the inversion survived every run it was in.
    """
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)

        # A: an addition must stay quiet — the arm the predecessor got backwards.
        repo = _scratch(tmp / "add")
        (repo / "bench" / "results" / "seed2.json").write_text('{"seed": 2}\n')
        _git(["add", "-A"], cwd=repo)
        _git(["commit", "-qm", "add a new seed"], cwd=repo)
        if check(repo).violations:
            failures.append("a pure addition was reported as a violation")

        # B: a modification must fire.
        repo = _scratch(tmp / "mod")
        (repo / "bench" / "results" / "seed1.json").write_text('{"seed": 999}\n')
        _git(["add", "-A"], cwd=repo)
        _git(["commit", "-qm", "rewrite a landed seed"], cwd=repo)
        if not check(repo).violations:
            failures.append("a modification of a landed record went unreported")

        # C: a deletion must fire.
        repo = _scratch(tmp / "del")
        _git(["rm", "-q", "bench/results/seed1.json"], cwd=repo)
        _git(["commit", "-qm", "delete a landed seed"], cwd=repo)
        if not check(repo).violations:
            failures.append("a deletion of a landed record went unreported")

        # D: a modification behind a later commit must fire — the `HEAD~1` blind spot.
        repo = _scratch(tmp / "deep")
        (repo / "bench" / "results" / "seed1.json").write_text('{"seed": 42}\n')
        _git(["add", "-A"], cwd=repo)
        _git(["commit", "-qm", "rewrite a landed seed"], cwd=repo)
        (repo / "unrelated.txt").write_text("later\n")
        _git(["add", "-A"], cwd=repo)
        _git(["commit", "-qm", "an unrelated later commit"], cwd=repo)
        if not check(repo).violations:
            failures.append("a modification behind a later commit went unreported")

        # E: an empty corpus must trip the vacuity guard rather than pass.
        empty = tmp / "empty" / "repo"
        empty.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "--initial-branch=main"], cwd=empty, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=empty, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=empty, check=True)
        (empty / "readme.md").write_text("no bench records here\n")
        _git(["add", "-A"], cwd=empty)
        _git(["commit", "-qm", "base"], cwd=empty)
        if check(empty).tracked != 0:
            failures.append("the empty-corpus arm did not produce an empty corpus")
        # `_run` writes the VACUOUS line by design; captured so a passing self-test does
        # not print a line that reads as its own failure.
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            empty_code = _run(empty)
        if empty_code == 0:
            failures.append("an empty corpus passed instead of tripping the vacuity guard")
        if "VACUOUS" not in sink.getvalue():
            failures.append("the empty corpus failed without naming the vacuity guard")

        # F: a base that falls through to HEAD must fail in CI rather than self-compare.
        # No `main` branch exists here, so origin/main and main both miss and the chain
        # lands on HEAD — the shallow-checkout shape.
        lone = tmp / "lone" / "repo"
        (lone / "bench" / "results").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "--initial-branch=work"], cwd=lone, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=lone, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=lone, check=True)
        (lone / "bench" / "results" / "seed1.json").write_text('{"seed": 1}\n')
        _git(["add", "-A"], cwd=lone)
        _git(["commit", "-qm", "base"], cwd=lone)
        if _resolve_base(lone) != "HEAD":
            failures.append("the fallthrough arm did not land on HEAD")
        # Both states are set explicitly. Reading the ambient value and restoring it is
        # what broke this arm on its first CI run: in CI `GITHUB_ACTIONS` is genuinely
        # "true", so the "outside CI" half was asserting against a CI environment.
        prior = os.environ.get("GITHUB_ACTIONS")
        try:
            os.environ["GITHUB_ACTIONS"] = "true"
            if not check(lone).violations:
                failures.append("a HEAD self-comparison passed in CI instead of failing")
            os.environ.pop("GITHUB_ACTIONS", None)
            if check(lone).violations:
                failures.append("a HEAD self-comparison failed outside CI, where it is honest")
        finally:
            if prior is None:
                os.environ.pop("GITHUB_ACTIONS", None)
            else:
                os.environ["GITHUB_ACTIONS"] = prior

    return self_test_exit(
        failures,
        "OK self-test — an addition stays quiet; a modification, a deletion and a "
        "modification behind a later commit each fire; an empty corpus trips D57; a "
        "HEAD self-comparison fails in CI and passes locally\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run the planted controls")
    args = parser.parse_args()
    return _self_test() if args.self_test else _run()


if __name__ == "__main__":
    raise SystemExit(main())
