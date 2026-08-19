"""C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.

C7, C9, C12, C13 and C16 are asserted before the agent process starts. Each of them is a
claim about a container that then runs untrusted code for the length of a task. Boot-time
absence plus an argument that nothing could have changed is still an argument: C6 makes
fetching impossible and C12/C13 make installing impossible, and **a control that holds "by
argument" is a control that has not been checked.**

C16 was added to the set for a reason the other four do not have. It is not that the
workspace kind could change mid-run — it cannot. It is that `docker run` carries `--rm`, so
**a container that exits during the run leaves nothing behind**. At the end of the run the
adaptor either still has a container id or it does not, and if it does not, C16 fails, C14
fails, and the verdict is `indeterminate` — which is the correct reading of a run whose
container died under the measurement.

### What re-asserting C16 does not catch

`compare` is outcome-level: it reports an id whose end-of-run *outcome* differs from boot.
A run that swapped one container for another of the same kind passes C16 at both ends with a
**different container id**, and `compare` sees two passes. Closing that needs an identity
comparison, not another member of this set, and it is not written. Stated here rather than
left for a reader to assume, because "C16 is re-asserted" reads stronger than it is.

So the five are re-run after the agent stops and before the claim is accepted. The
disposition differs from boot and the difference is the point: at boot a failure means *the
run does not start*, and here it means *the claim is rejected and the verdict is
`indeterminate`* (F18). Nothing was learned about the agent — the environment moved under
the measurement — so the run belongs on neither side of the merge rate.

**The re-assertion set is closed and stated here.** It is not "whatever assertions happen to
be re-runnable", because that set silently shrinks as assertions gain boot-only dependencies.
A member of `REASSERTED` missing from the end-of-run report is itself a failure, exactly as
an absent required assertion is at dispatch.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from harness.containment.assertions import Assertion, AssertionOutcome, AssertionReport

__all__ = ["ASSERTION_C14", "REASSERTED", "compare", "reassert"]

# C7 oracle absence, C9 mounts, C12 writable set, C13 archives and caches, C16 the container
# still being there at all.
REASSERTED: Final[tuple[str, ...]] = ("C7", "C9", "C12", "C13", "C16")

ASSERTION_C14: Final = "C14"


def compare(boot: AssertionReport, end: AssertionReport) -> tuple[str, ...]:
    """Every re-asserted id whose end-of-run outcome differs from its boot outcome.

    Reported separately from a plain end-of-run failure because the two say different things.
    An assertion that failed at both ends means the container was never right and the boot
    gate let it through; one that passed at boot and failed at the end means **something
    appeared during the run**, which is the finding C14 exists for.
    """
    boot_by_id = {a.assertion_id: a.outcome for a in boot.assertions}
    end_by_id = {a.assertion_id: a.outcome for a in end.assertions}
    return tuple(
        assertion_id
        for assertion_id in REASSERTED
        if assertion_id in boot_by_id
        and assertion_id in end_by_id
        and boot_by_id[assertion_id] is not end_by_id[assertion_id]
    )


def reassert(end_of_run: Sequence[Assertion]) -> Assertion:
    """Fold the end-of-run results into the single C14 assertion the claim gate reads.

    Absence is a failure, never a skip, and it is `NOT_EXECUTED` rather than `FAILED`: an
    assertion nobody re-ran and an assertion that re-ran and found a problem are different
    findings, and only the second says something about the container.
    """
    by_id = {a.assertion_id: a for a in end_of_run}

    absent = sorted(set(REASSERTED) - set(by_id))
    if absent:
        return Assertion(
            assertion_id=ASSERTION_C14,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                f"re-assertion did not run for {absent}; the closed set is {list(REASSERTED)} "
                "and a member missing from the end-of-run report is not a member that passed"
            ),
        )

    not_executed = sorted(
        i for i in REASSERTED if by_id[i].outcome is AssertionOutcome.NOT_EXECUTED
    )
    if not_executed:
        return Assertion(
            assertion_id=ASSERTION_C14,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=f"re-assertion could not be completed for {not_executed} (F25)",
        )

    failed = sorted(f"{i}: {by_id[i].detail}" for i in REASSERTED if not by_id[i].passed)
    if failed:
        return Assertion(
            assertion_id=ASSERTION_C14,
            outcome=AssertionOutcome.FAILED,
            detail=(
                f"the environment changed during the run — {failed}. The claim is rejected "
                "and the verdict is indeterminate (F18): nothing was learned about the agent."
            ),
        )

    unverified = sorted(i for i in REASSERTED if not by_id[i].premise_verified)
    return Assertion(
        assertion_id=ASSERTION_C14,
        outcome=AssertionOutcome.PASSED,
        detail=f"re-asserted {list(REASSERTED)} after the agent stopped",
        # An unverified premise anywhere in the set travels up. A fold that reported a clean
        # premise over a member resting on an unread one would launder the very state
        # ADR-0007 exists to keep visible.
        premise_verified=not unverified,
    )
