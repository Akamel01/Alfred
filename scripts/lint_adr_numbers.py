#!/usr/bin/env python3
"""ADR number claim lint: a branch may not claim a number the base has issued.

The ADR log is append-only in one file, and its preamble states the discipline:
numbering is sequential and never reused. Nothing has ever enforced the *claim*
half of it. The collision is discovered at merge, when two branches land the same
number, and it is paid for by hand — a renumbering note, corrected in-repo
references, and a vault rename, per the `fa62b4b` precedent. That cost was paid
twice in one week when the four ADR branches landed: the protected-set record
renumbered 0029 to 0031 and the agentdb record 0031 to 0032, each by hand, each
with the commit messages still naming the drafted number.

The lint compares the log as the branch has it against the log the base ref has,
on the *records*, not the number sets: branch and base share their history, so a
number present in both is the normal case. Three findings:

  CLAIM — the base has issued a number and this branch carries a *different*
          record under it. The branch drafted against an older tip, the base has
          since issued the number for someone else, and the merge would land two
          ADRs under one number. The comparison is over the heading and the
          decision text; a trailing renumbering note (the blockquote that travels
          with a record) is excluded, because the merge that renumbers a record is
          the same merge that rewrites the note. Fails.
  DUP   — the same number twice in the branch log. An append-only log with a
          repeated number is a number nobody owns. Fails.
  GAP   — a missing number in the branch log. Prints, never fails. A record may
          deliberately take a number it expects to lose at merge (the agentdb
          record took 0031 knowing 0029 was contested), and a deliberate
          reservation reads exactly like a gap. The vault surfaces gaps as a
          declared anomaly, which is the committed home for that fact; a gate
          that reds on a deliberate skip is a gate the branch works around.

Base resolution, first resolvable wins: `origin/$GITHUB_BASE_REF` in CI, else
`origin/main`, else `main`, else `HEAD`. `HEAD` is the branch's own tip and finds
nothing new, which is the correct answer for a tree with no forked base. A base
that resolves to nothing is a failure, not a skip: a claim check with nothing to
check against is the vacuity class this repository has paid for before.

Exit 0 clean, 1 on a finding or an unreadable log.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

LOG = Path("docs/tier1/adr-log.md")

#: The grammar the log declares. The em dash is the same grammar
#: `gen_reading_map.py` and the vault's `adrs` extractor already read, so a
#: heading this lint cannot parse is a record the register does not own either.
_HEADING = re.compile(r"^## (ADR-\d{4}) — ")
_H2 = re.compile(r"^## ")

BASE_CANDIDATES = ("origin/main", "main", "HEAD")


def _record(span: list[str]) -> str:
    """A record with trailing separators and renumbering notes stripped.

    Two records that differ only in trailing `---` lines or `>` blockquote lines
    are the same record. The separator case: the same record is the last record of
    the base file (no trailing `---`) and a middle record of the branch the moment
    the branch appends anything. The blockquote case: a renumbering note travels
    with the record it reconciles, and the merge that renumbers a record is the
    same merge that rewrites the note, so a note cannot take part in the
    comparison either. What compares is the heading and the decision text.
    """
    lines = span[:]
    while lines:
        stripped = lines[-1].strip()
        if stripped in ("", "---") or stripped.startswith(">"):
            lines.pop()
            continue
        break
    return "\n".join(lines).rstrip()


def _parse(text: str) -> tuple[dict[str, str], dict[str, list[int]]]:
    """Every ADR heading as `number -> record text`, plus `number -> heading lines`.

    A record runs from its heading to the next `##` line. The heading's title is
    part of the record: two records under one number that differ only in title are
    still two records. Line endings are folded before parsing, so a checkout under
    a different `core.autocrlf` compares identically.
    """
    records: dict[str, str] = {}
    lines: dict[str, list[int]] = {}
    current: str | None = None
    span: list[str] = []
    for index, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        heading = _HEADING.match(line)
        if heading:
            if current is not None:
                records[current] = _record(span)
            current = heading.group(1)
            span = [line]
            lines.setdefault(current, []).append(index)
        elif _H2.match(line):
            if current is not None:
                records[current] = _record(span)
                current = None
        elif current is not None:
            span.append(line)
    if current is not None:
        records[current] = _record(span)
    return records, lines


def audit(base_text: str, branch_text: str) -> tuple[list[str], list[str]]:
    """The claim check as a pure function of two log texts, returning
    `(failures, warnings)`.

    Pure on purpose: the self-test plants logs rather than git repositories, so
    the negative control runs anywhere a Python interpreter does. A check whose
    negative control needs a repository is a check that runs only where a
    repository happens to be.
    """
    failures: list[str] = []
    warnings: list[str] = []

    base_records, _ = _parse(base_text)
    branch_records, branch_lines = _parse(branch_text)

    if not branch_records:
        failures.append(
            f"{LOG}: the working-tree log parses no ADR heading — a claim lint that reads "
            "nothing cannot clear anything"
        )
        return failures, warnings

    for number in sorted(branch_records):
        at = branch_lines[number]
        if len(at) > 1:
            failures.append(
                f"{LOG}:{at[0]}, {at[-1]}: {number} is declared {len(at)} times — an "
                "append-only log with a repeated number is a number nobody owns"
            )

    for number in sorted(branch_records):
        base_record = base_records.get(number)
        if base_record is not None and base_record != branch_records[number]:
            failures.append(
                f"{LOG}: {number} is issued by the base and this branch carries a different "
                "record under it — the merge would land two ADRs under one number; renumber "
                "at merge per the fa62b4b precedent"
            )

    numbers = {int(n[4:]) for n in branch_records}
    gaps = [n for n in range(1, max(numbers) + 1) if n not in numbers]
    if gaps:
        warnings.append(
            "NOTE gaps in the branch log: "
            + ", ".join(f"ADR-{n:04d}" for n in gaps)
            + " — a deliberate skip prints, never fails; the vault's adr-numbering-gap "
            "anomaly is its committed home"
        )
    return failures, warnings


def _resolve_base() -> tuple[str, str] | None:
    """The base log from the first resolvable ref: `origin/$GITHUB_BASE_REF` in CI,
    else `origin/main`, else `main`, else `HEAD`. The order is load-bearing: a PR
    is checked against the branch it will merge into, a local branch against its
    home, and a tree with no forked base against itself."""
    candidates = list(BASE_CANDIDATES)
    if base_ref := os.environ.get("GITHUB_BASE_REF"):
        candidates.insert(0, f"origin/{base_ref}")
    for ref in candidates:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{LOG.as_posix()}"],
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout, ref
    return None


def _planted_log(records: list[tuple[str, str]]) -> str:
    """A planted log: one heading and one body line per record, in the order given."""
    blocks = []
    for number, title in records:
        blocks.append(f"## {number} — {title}\n\nBody of {number}.\n\n---\n")
    return "".join(blocks)


def self_test() -> int:
    """Plant each collision shape, require the check to fire, require the control to
    stay quiet. The audit is pure over two log texts, so the fixtures need no git
    repository and no tempdir at all."""
    failures: list[str] = []

    def expect(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    def _num(n: int) -> str:
        # Built, never written as a literal: the vault's references extractor reads
        # this file, and a fixture token it resolves would mint an edge from a test.
        return f"ADR-{n:04d}"

    base = _planted_log([(f"ADR-{n:04d}", f"Base record {n}") for n in (1, 2, 3)])
    fresh_base = _planted_log([(f"ADR-{n:04d}", f"Base record {n}") for n in (1, 2)])
    shared = _planted_log([(_num(1), "Base record 1"), (_num(2), "Base record 2")])

    # 1. A fresh number passes: the base ends at 0002, the branch takes 0003, and
    #    nothing else moved. Both the failure list and the warning list stay empty.
    new_number = audit(fresh_base, shared + _planted_log([(_num(3), "A new record")]))
    expect(not new_number[0], f"a new number failed: {new_number[0]}")
    expect(not new_number[1], f"a new number printed a gap warning it did not earn: {new_number[1]}")

    # 2. A re-claim fails: the base has issued 0003 and the branch drafted a rival
    #    record under the same number.
    reclaim = audit(base, shared + _planted_log([(_num(3), "A rival record")]))
    expect(any(_num(3) in f for f in reclaim[0]),
           f"a re-claimed number did not fail: {reclaim[0]}")

    # 3. A deliberate skip passes with a printed warning, never a failure: a record
    #    that takes a number it expects to lose at merge must not read red.
    skip = audit(base, shared + _planted_log([(_num(5), "A record that skips 4")]))
    expect(not skip[0], f"a deliberate skip failed: {skip[0]}")
    expect(any(_num(4) in w for w in skip[1]), "a deliberate skip printed no gap warning")

    # 4. An in-branch duplicate fails: the same number twice is a number nobody owns.
    duplicate = audit(fresh_base, shared + _planted_log([(_num(3), "First"), (_num(3), "Second")]))
    expect(any(_num(3) in f for f in duplicate[0]),
           f"an in-branch duplicate did not fail: {duplicate[0]}")

    # 5. A log with no headings fails rather than passing: the vacuity class.
    vacuous = audit(base, "")
    expect(vacuous[0], "a heading-less log passed — the vacuity guard is not wired")

    for message in failures:
        print(f"FAIL self-test: {message}", file=sys.stderr)
    if failures:
        print(f"\n{len(failures)} self-test failure(s)", file=sys.stderr)
        return 1
    print(
        "OK self-test — a new number passes, a re-claim fails, a deliberate skip prints "
        "without failing, an in-branch duplicate fails, and a heading-less log fails "
        "rather than passing"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ADR number claim lint over the ADR log.")
    parser.add_argument("--self-test", action="store_true",
                        help="plant violations and verify each check fires")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if not LOG.is_file():
        print(f"error: {LOG} does not exist", file=sys.stderr)
        return 1

    branch_text = LOG.read_text(encoding="utf-8")
    base = _resolve_base()
    if base is None:
        tried = f"origin/$GITHUB_BASE_REF, {', '.join(BASE_CANDIDATES)}"
        print(
            f"FAIL no base ref is resolvable (tried {tried}) — a claim lint with nothing "
            "to compare against cannot report clean",
            file=sys.stderr,
        )
        return 1
    base_text, base_ref = base

    failures, warnings = audit(base_text, branch_text)
    branch_count = len(_parse(branch_text)[0])
    for warning in warnings:
        print(warning)
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        print(f"\n{len(failures)} ADR number finding(s) against {base_ref}", file=sys.stderr)
        return 1
    print(
        f"OK ADR numbers — {branch_count} records in the branch log, no number the base "
        f"has issued is re-claimed ({base_ref})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
