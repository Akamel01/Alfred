"""Every chained table is drill-covered.

The store chains exactly `CHAINED_TABLES`; the restore drill dumps, restores and compares
exactly `EVIDENCE_TABLES`. Nothing else keeps those two lists honest against each other,
and the failure when they drift is not an error anywhere: a chained table absent from the
drill's list is never dumped, never restored, never counted — comparisons one and two
pass over it vacuously while comparison four re-walks some other chain. The drill reports
green on a table whose restore was never rehearsed, which is the silent-skip shape D57
exists for. This module imports both constants so the lists can only drift together with
a red test.
"""

from __future__ import annotations

from harness.evidence.restore_drill import EVIDENCE_TABLES
from harness.evidence.store import CHAINED_TABLES


def test_every_chained_table_is_drill_covered() -> None:
    # Vacuity guards first (D57): two empty collections are subsets of each other and
    # would satisfy the subset claim for free.
    assert CHAINED_TABLES, "no chained tables: the chain claims nothing"
    assert EVIDENCE_TABLES, "no evidence tables: the drill would compare nothing"
    uncovered = CHAINED_TABLES - set(EVIDENCE_TABLES)
    assert not uncovered, f"chained but never drill-covered: {sorted(uncovered)}"
