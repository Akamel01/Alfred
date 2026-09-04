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

A fourth finding, over a different property of the same log: **WAIVER**. Four
records state in prose which D28 waiver they are, and that ordinal is derivable
— it is the count of prior `**D28 waiver:** yes` headers. Two records both
claimed to be the third (#55), and the error ran in the under-reporting
direction, which is the direction that makes the waiver count look healthier
than it is. The check derives the position and compares; a body is never
rewritten to fix one, so an appended blockquote correction is read as the
record's effective claim. Fails.

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

from _lintkit import ADR_HEADING as _HEADING
from _lintkit import self_test_exit

LOG = Path("docs/tier1/adr-log.md")

# The heading grammar is `_lintkit.ADR_HEADING`, the same shape `gen_reading_map.py`
# reads and the one the vault's `adrs` extractor already used, so a heading this lint
# cannot parse is a record the register does not own either.
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


def _parse(
    text: str, *, strip: bool = True
) -> tuple[dict[str, str], dict[str, list[int]]]:
    """Every ADR heading as `number -> record text`, plus `number -> heading lines`.

    A record runs from its heading to the next `##` line. The heading's title is
    part of the record: two records under one number that differ only in title are
    still two records. Line endings are folded before parsing, so a checkout under
    a different `core.autocrlf` compares identically.

    `strip` controls whether trailing separators and blockquote notes are removed.
    The claim check needs them gone — a renumbering note must not make two copies of
    one record compare unequal. The waiver-ordinal check needs them kept, because an
    appended correction note is exactly where the corrected ordinal lives. One parse
    with a switch, rather than two parsers that will drift apart on the heading
    grammar they share.
    """
    keep = (lambda span: "\n".join(span).rstrip()) if not strip else _record
    records: dict[str, str] = {}
    lines: dict[str, list[int]] = {}
    current: str | None = None
    span: list[str] = []
    for index, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        heading = _HEADING.match(line)
        if heading:
            if current is not None:
                records[current] = keep(span)
            current = heading.group(1)
            span = [line]
            lines.setdefault(current, []).append(index)
        elif _H2.match(line):
            if current is not None:
                records[current] = keep(span)
                current = None
        elif current is not None:
            span.append(line)
    if current is not None:
        records[current] = keep(span)
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


# ------------------------------------------------------------------- waiver ordinals

#: The ordinal words a waiver paragraph may claim. Bounded on purpose: the operating
#: principles' own falsification clause fires at three waivers against one principle, so a
#: log that reaches a twentieth has already falsified something, and a check that silently
#: keeps counting past the point where the register stopped meaning anything is a check
#: that stopped meaning anything too.
ORDINALS: tuple[str, ...] = (
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
    "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth",
    "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth",
)

#: The header field. The colon is required, and that is what separates the header
#: declaration from the body's prose `**D28 waiver**`, which carries no colon.
_WAIVER_HEADER = re.compile(r"\*\*D28 waiver:\*\*\s*(yes|no)\b", re.IGNORECASE)

#: The body claim. The captured word is checked against `ORDINALS` rather than accepted as
#: any word, so "It is the thing that was measured" — which appears twice in the log — is
#: not read as an ordinal claim.
_ORDINAL_CLAIM = re.compile(r"It is the \*{0,2}([A-Za-z]+)\*{0,2}\.")

#: The prose marker every waiver paragraph carries, colon-less and so distinct from the
#: `**D28 waiver:**` header field. It scopes where an ordinal counts as a *claim*: without
#: it, an ADR that quotes another record's sentence in order to discuss it is read as making
#: that record's claim. ADR-0052 is the instance — it quotes ADR-0040's line while explaining
#: why the line is not being rewritten, and the check fired on the quotation.
_WAIVER_PROSE = "**D28 waiver**"


def _claim_sites(record: str) -> list[str]:
    """The paragraphs of a record in which an ordinal counts as a claim.

    Two shapes, and nothing else. A paragraph carrying the colon-less prose marker
    `**D28 waiver**` is the waiver paragraph itself. A paragraph that is wholly a blockquote
    is a correction note — the only repair shape an append-only log has.

    Everything else is excluded, and the exclusion is not defensive tidying: an ADR that
    quotes another record's ordinal sentence in order to explain it would otherwise be read
    as making that record's claim.
    """
    sites: list[str] = []
    for paragraph in record.split("\n\n"):
        lines = [line for line in paragraph.split("\n") if line.strip()]
        if not lines:
            continue
        quoted = all(line.lstrip().startswith(">") for line in lines)
        if quoted or _WAIVER_PROSE in paragraph:
            sites.append(paragraph)
    return sites


def _claimed_ordinal(record: str) -> str | None:
    """The record's effective ordinal claim: the **last** one across its claim sites.

    Last, not first, because the log is append-only in spirit — a record's body is not
    rewritten to fix a number, a correction note is appended in the blockquote form the
    renumbering notes already use, and the latest statement in a record is the one the
    record is making. ADR-0040 is the instance: its body claims *third* and its appended
    note corrects that to *fourth*.
    """
    ordinals: list[str] = []
    for site in _claim_sites(record):
        for match in _ORDINAL_CLAIM.finditer(site):
            word = match.group(1).lower()
            if word in ORDINALS:
                ordinals.append(word)
    return ordinals[-1] if ordinals else None


def _waiver_numbers(text: str) -> list[str]:
    """The ADR numbers declaring `D28 waiver: yes`, in numeric order.

    This list *is* the count the operating principles read as a health metric, which is
    why it is computed rather than written down anywhere: a total kept in prose is a total
    that can be wrong in the flattering direction, and it already was.
    """
    records, _ = _parse(text, strip=False)
    return [
        number
        for number in sorted(records)
        if (found := _WAIVER_HEADER.search(records[number]))
        and found.group(1).lower() == "yes"
    ]


def audit_waivers(branch_text: str) -> tuple[list[str], list[str]]:
    """The D28 waiver ordinal as a derived value rather than an asserted one.

    Four sites in the log each say the waiver "counts toward the waiver total the operating
    principles use **as a health metric**", and each states its own position in that total in
    prose. A health metric that cannot count itself is not one: two records both claimed to
    be the third, and the error ran in the under-reporting direction — the direction that
    makes the count look healthier than it is.

    The position is derivable — it is the number of prior `**D28 waiver:** yes` headers — so
    this check derives it and compares. Three findings, all failures:

      WAV-CLAIM   — the ordinal claimed is not the position the record holds.
      WAV-MISSING — the header declares a waiver and the body states no ordinal, so the
                    record joins the count without saying where.
      WAV-ORPHAN  — the body states an ordinal and the header does not declare a waiver.
                    The prose would enter a count the header says the record is not in.

    Pure over the log text, like `audit`, so the negative controls need no repository.
    """
    failures: list[str] = []
    warnings: list[str] = []

    records, lines = _parse(branch_text, strip=False)
    if not records:
        failures.append(
            f"{LOG}: the working-tree log parses no ADR heading — a waiver ordinal check "
            "that reads nothing cannot clear anything"
        )
        return failures, warnings

    declared: list[tuple[str, str]] = []  # (number, header value)
    for number in sorted(records):
        header = _WAIVER_HEADER.search(records[number])
        if header:
            declared.append((number, header.group(1).lower()))

    waivers = _waiver_numbers(branch_text)

    for number, value in declared:
        record = records[number]
        claimed = _claimed_ordinal(record)
        at = lines[number][0]
        if value == "yes":
            if claimed is None:
                failures.append(
                    f"{LOG}:{at}: {number} declares `D28 waiver: yes` and its body states no "
                    "ordinal — a record that joins the waiver count without saying where it "
                    "sits leaves the total uncountable"
                )
                continue
            index = waivers.index(number)
            position = ORDINALS[index] if index < len(ORDINALS) else None
            if position is None:
                failures.append(
                    f"{LOG}:{at}: {number} is waiver number {index + 1}, past the "
                    f"{len(ORDINALS)} this check names — the register has outrun its "
                    "own health metric"
                )
            elif claimed != position:
                failures.append(
                    f"{LOG}:{at}: {number} claims to be the {claimed} D28 waiver and is the "
                    f"{position} — the ordinal is derivable from the {len(waivers)} `D28 waiver: "
                    "yes` headers in numeric order, so a prose claim that disagrees with the "
                    "position is the count disagreeing with itself"
                )
        elif claimed is not None:
            failures.append(
                f"{LOG}:{at}: {number} declares `D28 waiver: no` and its body claims to be the "
                f"{claimed} — the prose enters a count the header says this record is not in"
            )

    if not waivers:
        failures.append(
            f"{LOG}: no record declares `D28 waiver: yes` — the ordinal check scanned "
            f"{len(records)} records and had nothing to count, which is the vacuity class "
            "this repository has paid for before"
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


def _planted_waiver_log(records: list[tuple[str, str | None, str | None]]) -> str:
    """A planted log whose records carry a `D28 waiver` header and, optionally, an ordinal
    claim and an appended correction note.

    Each entry is `(number, header, claim)` where `header` is `"yes"`, `"no"` or `None` for
    a record predating the field, and `claim` is the ordinal word the body states or `None`
    for a body that states none. A `claim` prefixed with `note:` is appended as a trailing
    blockquote instead of stated in the body, which is the append-only correction shape the
    log actually uses.
    """
    blocks = []
    for number, header, claim in records:
        head = f"## {number} — Planted record {number}\n\n"
        if header is not None:
            head += f"**Date:** 2026-01-01 · **Status:** Accepted · **D28 waiver:** {header}\n\n"
        body = f"Body of {number}.\n"
        note = ""
        if claim is not None and claim.startswith("note:"):
            note = f"\n> Correction. It is the {claim[5:]}.\n"
        elif claim is not None:
            body = (
                "This is a **D28 waiver** and counts toward the waiver total the operating "
                f"principles use as a health metric. It is the {claim}.\n"
            )
        blocks.append(head + body + note + "\n---\n")
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

    # ---------------------------------------------------------- waiver ordinals
    # Every finding gets a planted violation and the ordinal check gets a paired
    # positive, because a check that only ever fires is a check nobody can trust to
    # stay quiet.

    # 6. Correct ordinals pass. Two waivers with a non-waiver between them: the
    #    position is the position among `yes` headers, not among records.
    correct = audit_waivers(_planted_waiver_log([
        (_num(1), "yes", "first"),
        (_num(2), "no", None),
        (_num(3), "yes", "second"),
    ]))
    expect(not correct[0], f"correct waiver ordinals failed: {correct[0]}")

    # 7. A wrong ordinal fails. This is #55's shape: the second waiver claiming to be
    #    the first, under-reporting the total.
    wrong = audit_waivers(_planted_waiver_log([
        (_num(1), "yes", "first"),
        (_num(2), "yes", "first"),
    ]))
    expect(any("claims to be the first" in f and _num(2) in f for f in wrong[0]),
           f"a wrong waiver ordinal did not fail: {wrong[0]}")

    # 8. An appended correction note overrides the body, and the corrected record
    #    passes. The log is append-only in spirit, so this is the only repair shape
    #    available and the check must accept it.
    corrected = audit_waivers(_planted_waiver_log([
        (_num(1), "yes", "first"),
        (_num(2), "yes", "note:second"),
    ]))
    expect(not corrected[0], f"an appended ordinal correction was not honoured: {corrected[0]}")

    # 9. A waiver whose body states no ordinal fails: it joins the count without
    #    saying where it sits.
    silent = audit_waivers(_planted_waiver_log([(_num(1), "yes", None)]))
    expect(any("states no ordinal" in f for f in silent[0]),
           f"a waiver with no ordinal claim did not fail: {silent[0]}")

    # 10. An ordinal claimed by a record whose header says `no` fails: the prose
    #     enters a count the header excludes it from.
    orphan = audit_waivers(_planted_waiver_log([
        (_num(1), "yes", "first"),
        (_num(2), "no", "second"),
    ]))
    expect(any("is not in" in f for f in orphan[0]),
           f"an orphan ordinal claim did not fail: {orphan[0]}")

    # 11. A record that *quotes* an ordinal sentence outside a waiver paragraph and
    #     outside a blockquote is not making that claim. ADR-0052 is the live instance,
    #     and it fired this check on itself before the claim sites were scoped.
    quoted = _planted_waiver_log([(_num(1), "yes", "first"), (_num(2), "no", None)])
    quoted = quoted.replace(
        f"Body of {_num(2)}.",
        f'{_num(2)} discusses another record, which reads "It is the second." verbatim.',
    )
    discussion = audit_waivers(quoted)
    expect(not discussion[0],
           f"a quoted ordinal was read as a claim: {discussion[0]}")

    # 12. A log with records but no waiver at all fails rather than reporting clean:
    #     the vacuity class, aimed at the ordinal check itself.
    no_waiver = audit_waivers(_planted_waiver_log([(_num(1), "no", None)]))
    expect(any("nothing to count" in f for f in no_waiver[0]),
           f"a log with no waiver reported clean: {no_waiver[0]}")

    return self_test_exit(
        failures,
        "OK self-test — a new number passes, a re-claim fails, a deliberate skip prints "
        "without failing, an in-branch duplicate fails, a heading-less log fails "
        "rather than passing, correct waiver ordinals pass, a wrong one fails, an "
        "appended correction is honoured, a silent waiver fails, an orphan claim fails, a "
        "quoted ordinal is not read as a claim, and a log with no waiver fails rather "
        "than reporting clean\n",
        failures_stream=sys.stderr,
        prefix="FAIL self-test:",
        tally=True,
    )

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
    waiver_failures, waiver_warnings = audit_waivers(branch_text)
    failures += waiver_failures
    warnings += waiver_warnings
    branch_count = len(_parse(branch_text)[0])
    waiver_count = len(_waiver_numbers(branch_text))
    for warning in warnings:
        print(warning)
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        print(f"\n{len(failures)} ADR number finding(s) against {base_ref}", file=sys.stderr)
        return 1
    print(
        f"OK ADR numbers — {branch_count} records in the branch log, no number the base "
        f"has issued is re-claimed ({base_ref}); {waiver_count} D28 waiver(s), each "
        "claiming the ordinal its position derives"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
