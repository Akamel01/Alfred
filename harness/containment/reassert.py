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

### `compare` reads values, not just outcomes

An outcome-level comparison cannot see the drift that matters most here. A run that swapped
one container for another of the same kind passes C16 at both ends, and two passes look
identical. So `compare` diffs `Assertion.observed` — the values each check actually read —
and reports six distinct kinds of movement, because they are six different findings:

- `OUTCOME` — what the comparison used to be, and still the loudest.
- `VALUE` — the same key with a different value. The swapped container. A mount that changed
  mode. The writable set that grew.
- `OBSERVATION_LOST` — a key reported at boot and **not** at the end. The quiet one: a
  key-wise diff over shared keys sees nothing, and a check that stopped observing is
  indistinguishable from one that observed no change. It is a finding, not an absence.
- `OBSERVATION_APPEARED` — the mirror. Reported symmetrically rather than by taste: an
  unexplained new observation at the end of a run is not obviously benign, and deciding it
  is would be exactly the judgement this module refuses to make on the reader's behalf.
- `MISSING_AT_END` / `MISSING_AT_BOOT` — the assertion is absent from one report. `reassert`
  already refuses on end-side absence; boot-side absence was caught by nothing at all, and
  an assertion that appears only at the end was never a re-assertion of anything.

### The vacuity control this needs

**A value comparison over assertions that report no values is not a clean comparison**
(D57). `value_blind` names every id that both reports carry and that neither side gave an
observation for: those were compared on their outcome alone, exactly as before, and a caller
reading an empty `compare` result over them is reading less than it looks like.

Every member of the closed set records observations today, so `value_blind` is empty against
the real implementations — which is what makes it a control rather than a note. It fires on
an adaptor that supplies reports without observations, and on a member added later that
forgets to. Both halves are tested: one against the five real checks, one against reports
built with no observations at all.

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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Final

from harness.containment.assertions import Assertion, AssertionOutcome, AssertionReport

__all__ = [
    "ASSERTION_C14",
    "REASSERTED",
    "Drift",
    "DriftKind",
    "compare",
    "drifted_ids",
    "reassert",
    "value_blind",
]

# C7 oracle absence, C9 mounts, C12 writable set, C13 archives and caches, C16 the container
# still being there at all.
REASSERTED: Final[tuple[str, ...]] = ("C7", "C9", "C12", "C13", "C16")

ASSERTION_C14: Final = "C14"


class DriftKind(Enum):
    """The six ways a re-asserted claim can have moved. Never collapsed into each other."""

    OUTCOME = "outcome"
    VALUE = "value"
    OBSERVATION_LOST = "observation_lost"
    OBSERVATION_APPEARED = "observation_appeared"
    MISSING_AT_BOOT = "missing_at_boot"
    MISSING_AT_END = "missing_at_end"


@dataclass(frozen=True)
class Drift:
    """One thing that differs between boot and end of run.

    `key` is the observation name for value-level kinds and `None` for the whole-assertion
    ones. `boot` and `end` are rendered strings so a drift is reportable without the reader
    needing the original types.
    """

    assertion_id: str
    kind: DriftKind
    key: str | None
    boot: str
    end: str

    def __str__(self) -> str:
        where = f"{self.assertion_id}.{self.key}" if self.key else self.assertion_id
        return f"{where} {self.kind.value}: {self.boot!r} -> {self.end!r}"


def _drifts_for(
    assertion_id: str, boot: Assertion | None, end: Assertion | None
) -> list[Drift]:
    if boot is None and end is None:
        return []
    if boot is None:
        return [Drift(assertion_id, DriftKind.MISSING_AT_BOOT, None, "<absent>", "present")]
    if end is None:
        return [Drift(assertion_id, DriftKind.MISSING_AT_END, None, "present", "<absent>")]

    found: list[Drift] = []
    if boot.outcome is not end.outcome:
        found.append(
            Drift(
                assertion_id,
                DriftKind.OUTCOME,
                None,
                boot.outcome.value,
                end.outcome.value,
            )
        )

    boot_observed: Mapping[str, str] = boot.observed
    end_observed: Mapping[str, str] = end.observed
    for key in sorted(set(boot_observed) | set(end_observed)):
        if key not in end_observed:
            found.append(
                Drift(
                    assertion_id,
                    DriftKind.OBSERVATION_LOST,
                    key,
                    boot_observed[key],
                    "<not observed>",
                )
            )
        elif key not in boot_observed:
            found.append(
                Drift(
                    assertion_id,
                    DriftKind.OBSERVATION_APPEARED,
                    key,
                    "<not observed>",
                    end_observed[key],
                )
            )
        elif boot_observed[key] != end_observed[key]:
            found.append(
                Drift(assertion_id, DriftKind.VALUE, key, boot_observed[key], end_observed[key])
            )
    return found


def compare(boot: AssertionReport, end: AssertionReport) -> tuple[Drift, ...]:
    """Everything about the re-asserted set that moved between boot and end of run.

    Reported separately from a plain end-of-run failure because the two say different things.
    An assertion that failed at both ends means the container was never right and the boot
    gate let it through; one that passed at boot and failed at the end means **something
    appeared during the run**, which is the finding C14 exists for. And one that passed at
    both ends over a *different* observed value means the run moved underneath a control that
    never noticed — the case an outcome-level comparison cannot express at all.

    Ordering is deterministic: the closed set's own order, then kind, then key. The set's
    order is used rather than the alphabetical one, so `C9` precedes `C12` — the ids are not
    lexically sortable and sorting them that way would put `C12` first and read as a bug.
    """
    boot_by_id = {a.assertion_id: a for a in boot.assertions}
    end_by_id = {a.assertion_id: a for a in end.assertions}
    found: list[Drift] = []
    for assertion_id in REASSERTED:
        found.extend(
            _drifts_for(assertion_id, boot_by_id.get(assertion_id), end_by_id.get(assertion_id))
        )
    order = {assertion_id: index for index, assertion_id in enumerate(REASSERTED)}
    return tuple(
        sorted(found, key=lambda d: (order[d.assertion_id], d.kind.value, d.key or ""))
    )


def drifted_ids(drifts: Sequence[Drift]) -> tuple[str, ...]:
    """The assertion ids named by a comparison, in the closed set's order, deduplicated."""
    named = {d.assertion_id for d in drifts}
    return tuple(i for i in REASSERTED if i in named)


def value_blind(boot: AssertionReport, end: AssertionReport) -> tuple[str, ...]:
    """Re-asserted ids present in both reports that **neither side gave any observation for**.

    D57, aimed at this comparison specifically. `compare` returning nothing over an assertion
    in this list means only that its outcome held; nothing was compared value-wise, because
    there was nothing to compare. A caller that reads that as "the container did not move"
    is reading a check that did not run.

    Empty against the five real checks, which all record observations. What it catches is an
    adaptor that supplies reports without them, and a member added to `REASSERTED` later that
    forgets to record any.
    """
    boot_by_id = {a.assertion_id: a for a in boot.assertions}
    end_by_id = {a.assertion_id: a for a in end.assertions}
    return tuple(
        assertion_id
        for assertion_id in REASSERTED
        if assertion_id in boot_by_id
        and assertion_id in end_by_id
        and not boot_by_id[assertion_id].observed
        and not end_by_id[assertion_id].observed
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
