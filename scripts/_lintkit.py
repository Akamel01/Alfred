"""Shared machinery for the lints in `scripts/`, moved out of their siblings.

Each piece here ran verbatim, or near enough to smell the same, in two or more lints:
the Findings record, the vacuity guard (D57), the fail-closed register load, the ADR
heading grammar, the self-test tail, and the repo-root constant. The extraction is a
move, not a redesign — every caller's output bytes are unchanged, and each lint's
`--self-test` proves it against its pre-refactor run.

Deliberately not imported by `tools/`: the vault keeps its own copies of frontmatter
parsing (`tools/vaultgraph/textio.py`) and tier names
(`tools/vaultgraph/extract/documents.py`) because `scripts/` sits inside the protected
set (policy/protected-paths.json, D20 / ADR-0031) and an import from it would put a
factory module in the inspector's import closure. The dependency direction here is one
way: the lints import this module; nothing imports the lints.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, TextIO

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: The grammar every reader of the ADR log inside `scripts/` shares. It is
#: byte-for-byte the vault extractor's (`tools/vaultgraph/extract/adrs.py`, which keeps
#: its own copy for the D20 reason above), so a heading one reader cannot parse is a
#: record none of them own. Four digits, always: `\d+` admitted `ADR-7`, and a log that
#: issues zero-padded numbers has no seven.
ADR_HEADING: Final = re.compile(r"^## (ADR-\d{4}) — (.+)$", re.MULTILINE)


@dataclass
class Findings:
    """What a check scanned and what it found.

    `scanned` exists so a check can be asked what it looked at: a check with nothing
    to check reports exactly what a passing check reports, and only the count tells
    them apart. Checks with a second number to carry subclass this and add it.
    """

    scanned: int = 0
    violations: list[str] = field(default_factory=list)


def vacuity_guard(scanned: int, line: str) -> bool:
    """D57. A scan that saw nothing writes its VACUOUS line and fails; returns True then.

    A guard that could pass for free is the failure this project paid for twice over:
    ruff's include matching no files reports success identically to a clean tree
    (ADR-0007's class, found in the tooling), and an empty test-directory scan reads
    as coverage. Callers pass the exact line they would have written by hand.
    """
    if scanned != 0:
        return False
    sys.stdout.write(line)
    return True


def load_register(path: Path, *, display: Path | None = None) -> tuple[dict[str, Any], str | None]:
    """A JSON register, fail-closed: `(register, None)`, or `({}, reason)`.

    An unreadable register is not an empty one, and a missing one is not a zero-row
    one: both return a reason the caller reports as a violation, never a silent empty
    mapping that a drift check would read as "nothing to compare". `display` is the
    path spelled into that reason when the checked path is rooted somewhere else —
    the self-tests plant registers under temporary directories and must not print
    absolute paths into a committed expectation.
    """
    shown = display if display is not None else path
    if not path.is_file():
        return {}, f"missing register: {shown}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return {}, f"register does not parse: {exc}"


def self_test_exit(
    failures: list[str],
    ok: str,
    *,
    failures_stream: TextIO = sys.stdout,
    ok_stream: TextIO = sys.stdout,
    prefix: str = "SELF-TEST FAILED",
    tally: bool = False,
) -> int:
    """The tail every `--self-test` mode ends with.

    Each planted violation the checks missed is reported, any miss exits 1, and the
    OK line prints only when every control stayed quiet — a self-test that says OK
    while a plant went unreported is the exact green-on-broken shape its lint exists
    to catch. Two shapes the siblings actually grew: most write findings and OK line
    to stdout under `SELF-TEST FAILED`; `lint_adr_numbers.py` audits pure functions,
    reports its findings to stderr under `FAIL self-test:` with a count line, and its
    OK line to stdout like every sibling's.
    """
    if failures:
        for line in failures:
            failures_stream.write(f"{prefix} {line}\n")
        if tally:
            failures_stream.write(f"\n{len(failures)} self-test failure(s)\n")
        return 1
    ok_stream.write(ok)
    return 0
