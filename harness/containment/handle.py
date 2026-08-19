"""The one crossing from probe vocabulary to handle vocabulary.

Two `Assertion` types exist and both are right. `harness/containment/assertions.py` is what a
probe produces — an id, an outcome, prose, and whether its premise was checked first-hand.
`harness/worker/port.py`'s `AssertionResult` is what travels on `SandboxHandle` to the gate —
the same plus where it ran and what it observed, because the gate needs to know a claim was
made *inside* the container rather than about it.

Until this module they were unconnected, and the consequence was specific: `premise_verified`
lived on the probe report and `check_handle` could not see it, so ADR-0007's third state was
recorded and unactionable. Every probe result therefore crosses here, once, and the crossing
is **lossless in the direction that matters** — an unverified premise stays unverified.

**The direction is one-way on purpose.** There is no `from_result`. A handle result is what
the adaptor asserted; reconstructing a probe from it would invite a code path where the
inspector's own record is rebuilt out of adaptor-supplied data, which is the shape of every
control that ends up checking a copy of its own input.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from harness.containment.assertions import Assertion, AssertionOutcome
from harness.worker.port import AssertionOutcome as PortOutcome
from harness.worker.port import AssertionReport as PortReport
from harness.worker.port import AssertionResult

__all__ = ["to_report", "to_result"]

# Written out rather than mapped by `.value`. The two enums are equal today, and a mapping
# that relied on that would silently misroute the first time either grew a member — which is
# exactly how `not_executed` would end up collapsed into a neighbour.
_OUTCOMES: Mapping[AssertionOutcome, PortOutcome] = {
    AssertionOutcome.PASSED: PortOutcome.PASSED,
    AssertionOutcome.FAILED: PortOutcome.FAILED,
    AssertionOutcome.NOT_EXECUTED: PortOutcome.NOT_EXECUTED,
}


def to_result(
    assertion: Assertion,
    *,
    executed_inside_container: bool,
    observed: Mapping[str, str] | None = None,
) -> AssertionResult:
    """One probe result, in the shape the handle carries.

    `executed_inside_container` is required and has no default. The specification's table
    assigns each assertion a side — C6 and C7 run inside, C4 and C5 run outside — and a
    default here would let an adaptor omit the one fact that says whether the claim is about
    the container or merely about the dispatch that requested it.

    **`observed` now carries the probe's own values across.** Until the checks recorded them
    this fell back to `{"detail": ...}`, which put prose where the handle's schema promises
    values — so the one structured thing an assertion knows stopped at the boundary and only
    a sentence about it crossed. An explicit `observed` argument still wins, for the adaptor
    that measured something the probe could not.
    """
    outcome = _OUTCOMES.get(assertion.outcome)
    if outcome is None:  # pragma: no cover — unreachable while the two enums agree
        raise ValueError(
            f"{assertion.assertion_id}: no handle outcome for {assertion.outcome!r}; "
            "the two vocabularies have diverged and this mapping must be extended"
        )
    return AssertionResult(
        assertion_id=assertion.assertion_id,
        outcome=outcome,
        executed_inside_container=executed_inside_container,
        observed=dict(observed or assertion.observed or {"detail": assertion.detail}),
        premise_verified=assertion.premise_verified,
    )


def to_report(
    assertions: Sequence[Assertion],
    *,
    at: str,
    inside: frozenset[str],
    observed: Mapping[str, Mapping[str, str]] | None = None,
) -> PortReport:
    """A whole boot or end-of-run report.

    `inside` names the assertion ids that ran inside the container; anything not in it ran
    outside. Passing the set rather than a per-assertion flag keeps the specification's own
    table as the single source of that fact.
    """
    per_assertion = observed or {}
    return PortReport(
        at=at,
        results=tuple(
            to_result(
                assertion,
                executed_inside_container=assertion.assertion_id in inside,
                observed=per_assertion.get(assertion.assertion_id),
            )
            for assertion in assertions
        ),
    )
