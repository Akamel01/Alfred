"""C11 — the serving lane is the lane the run was dispatched against.

Runs **outside**, against the serving layer. The control already exists:
`harness/lane/lane_fingerprint.py` reads the live lane and raises on drift, on an
unreadable fingerprint and on an expectation too thin to discriminate, and it was written
against an observed defect — a model loaded at 262,144 found serving at 28,672 after an
idle gap, turning 10/10 tool calling into 0/10 with nothing erroring anywhere.

**So this module does not reimplement it.** It does two things the lane module cannot:
derives the expectation from the run fingerprint rather than from a hand-written mapping,
and translates the lane module's exception vocabulary into the three-valued `Assertion`
vocabulary the handle carries. `FingerprintUnavailable` becomes `NOT_EXECUTED`, which F25
already makes a failure — an unread fingerprint is never a pass.

**`parallel_slots` is the honest gap.** The spec row names four fields and the serving
API publishes three of them; the slot count is a launch-time property of the server and is
not in `/api/v0/models`. Guessing a key name would produce a green assertion for a field
nobody read — the misnamed-key vacuity ADR-0007 names and ADR-0017 withdrew the "harmless
pass" argument over. So the count arrives as an explicit argument, and its absence is
`NOT_EXECUTED` rather than a silent three-conjunct pass. The distinction matters: prefix
reuse is 140x at one slot and 1.0x above it, so a lane at four slots is a different lane
wearing the same model id.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Final

from harness.containment.assertions import Assertion, AssertionOutcome
from harness.fingerprint.record import RunFingerprint
from harness.lane.lane_fingerprint import (
    FingerprintDrift,
    FingerprintIncomplete,
    FingerprintUnavailable,
    assert_fingerprint,
)

__all__ = ["ASSERTION_C11", "assert_lane_fingerprint", "expectation_from"]

ASSERTION_C11: Final = "C11"


def expectation_from(fingerprint: RunFingerprint) -> dict[str, Any]:
    """The lane-module expectation the record implies.

    Only the fields the serving layer reports. `parallel_slots` is deliberately absent —
    see the module docstring; the lane module would raise `FingerprintIncomplete` on a
    declared field the observation cannot carry, and that would report an unreadable field
    as a contract violation rather than as the unread conjunct it is.
    """
    return {
        "model_id": fingerprint.model_id,
        "quantization": fingerprint.quantization,
        "loaded_context_length": fingerprint.loaded_context_length,
    }


def assert_lane_fingerprint(
    fingerprint: RunFingerprint,
    *,
    fetch: Callable[[str], Mapping[str, Any]] | None = None,
    observed_parallel_slots: int | None = None,
    base_url: str | None = None,
) -> Assertion:
    """C11. Returns an `Assertion`; the lane module's raises are translated, never swallowed.

    `fetch` is passed straight through, so a caller that already read the lane this run
    compares the read it took rather than taking a second one — two reads of a lane that
    reconfigures itself between them is the defect wearing a check's clothes.
    """
    expected = expectation_from(fingerprint)
    kwargs: dict[str, Any] = {"fetch": fetch}
    if base_url is not None:
        kwargs["base_url"] = base_url

    try:
        observed = assert_fingerprint(fingerprint.model_id, expected, **kwargs)
    except FingerprintDrift as drift:
        return Assertion(
            assertion_id=ASSERTION_C11,
            outcome=AssertionOutcome.FAILED,
            detail=f"{drift}. Run does not start.",
            observed={
                "lane_drift": "; ".join(str(d) for d in drift.differences),
                "model_id": fingerprint.model_id,
            },
        )
    except (FingerprintUnavailable, FingerprintIncomplete) as unread:
        # Both are "nothing was compared". Unavailable is infrastructure and incomplete is
        # a contract violation, and the retry classes differ — but neither is a pass, and
        # the outcome vocabulary here has one member for "did not run".
        return Assertion(
            assertion_id=ASSERTION_C11,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=f"{unread}",
            observed={"model_id": fingerprint.model_id},
        )

    values = {
        "model_id": str(observed.get("model_id")),
        "quantization": str(observed.get("quantization")),
        "loaded_context_length": str(observed.get("loaded_context_length")),
        "parallel_slots": (
            "unread" if observed_parallel_slots is None else str(observed_parallel_slots)
        ),
    }

    if observed_parallel_slots is None:
        return Assertion(
            assertion_id=ASSERTION_C11,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                "three of the four fields matched, and the parallel slot count was not "
                "supplied; the serving API does not publish it and a run measured at an "
                "unknown slot count is not measured on this fingerprint"
            ),
            observed=values,
        )
    if observed_parallel_slots != fingerprint.parallel_slots:
        return Assertion(
            assertion_id=ASSERTION_C11,
            outcome=AssertionOutcome.FAILED,
            detail=(
                f"parallel slot count is {observed_parallel_slots}, fingerprint declares "
                f"{fingerprint.parallel_slots}; slots above 1 disable cross-request prefix "
                f"reuse entirely. Run does not start."
            ),
            observed=values,
        )
    return Assertion(
        assertion_id=ASSERTION_C11,
        outcome=AssertionOutcome.PASSED,
        detail=(
            f"lane {fingerprint.model_id} matches the fingerprint on model id, "
            f"quantization, loaded context length and parallel slot count"
        ),
        observed=values,
    )
