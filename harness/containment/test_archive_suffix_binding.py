"""Two ARCHIVE_SUFFIXES tuples, frozen verbatim, because their split is real and unexplained.

`harness/containment/inside.py` (C13's whole-mount walk) carries seven suffixes;
`harness/containment/oracle_absence.py` (C7's import-path scan) carries four. The frozen
spec does not explain the split — `docs/tier4/sandbox-specification.md § Executor
containment` row C13 enumerates only `.whl`, `.tar.gz`, `.zip`, and the spec's own
path-scan layer ("The probe", layer 3) says C7 scans "the archives and caches C13 covers",
which reads as one shared set. No ADR, commit message or comment records a reason for
either superset. This test therefore freezes both tuples exactly as implemented, per the
facts-first rule: current behaviour declared as contract, not rationalized.

**Flagged for the sandbox-spec owner**, who owes one of two outcomes: an authority that
states the intended split (and this docstring rewritten to cite it), or one tuple imported
from the other so the two probes cannot disagree quietly.

If you touch either tuple: both sides of this file change with it, and the spec row and
layer-3 paragraph are updated in the same commit.
"""

from __future__ import annotations

from harness.containment.inside import ARCHIVE_SUFFIXES as INSIDE_ARCHIVE_SUFFIXES
from harness.containment.oracle_absence import ARCHIVE_SUFFIXES as ORACLE_ARCHIVE_SUFFIXES


def test_c13_walk_freezes_its_seven_suffixes() -> None:
    assert INSIDE_ARCHIVE_SUFFIXES == (
        ".whl",
        ".tar.gz",
        ".tgz",
        ".zip",
        ".tar.bz2",
        ".tar.xz",
        ".egg",
    )


def test_c7_path_scan_freezes_its_four_suffixes() -> None:
    assert ORACLE_ARCHIVE_SUFFIXES == (".whl", ".tar.gz", ".tgz", ".zip")


def test_the_relationship_between_them_is_exactly_what_is_implemented() -> None:
    """C7's set is a strict subset of C13's — today. Freeze the shape, not just the members.

    A member added to one side without the other is precisely the drift nobody has an
    authority for; this makes it loud at commit time instead of at audit time.
    """
    assert set(ORACLE_ARCHIVE_SUFFIXES) < set(INSIDE_ARCHIVE_SUFFIXES)
    assert set(INSIDE_ARCHIVE_SUFFIXES) - set(ORACLE_ARCHIVE_SUFFIXES) == {
        ".tar.bz2",
        ".tar.xz",
        ".egg",
    }


def test_neither_set_is_empty() -> None:
    """Vacuity guard (D57): two empty frozensets agree perfectly and check nothing."""
    assert INSIDE_ARCHIVE_SUFFIXES
    assert ORACLE_ARCHIVE_SUFFIXES
