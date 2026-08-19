"""The Worker port's structural refusals, and the control on the check that enforces them."""

from __future__ import annotations

import keyword
import uuid
from dataclasses import dataclass

import pytest

from harness.worker.port import (
    VERDICT_VOCABULARY,
    AssertionOutcome,
    AssertionReport,
    AssertionResult,
    ClaimIncomplete,
    ContainmentFailure,
    MountMode,
    MountSpec,
    RunId,
    SandboxHandle,
    WorkerFault,
    WorkerOutcome,
    check_handle,
    claim_closure_size,
    verdict_vocabulary_violations,
)


def _handle(*results: AssertionResult) -> SandboxHandle:
    return SandboxHandle(
        run_id=RunId(uuid.uuid4()),
        image_digest="sha256:" + "0" * 64,
        boot_report=AssertionReport(at="boot", results=tuple(results)),
        mounts=(MountSpec("/host", "/repo", MountMode.READ_ONLY, "repo checkout"),),
    )


def _result(assertion_id: str, outcome: AssertionOutcome) -> AssertionResult:
    return AssertionResult(
        assertion_id=assertion_id,
        outcome=outcome,
        executed_inside_container=True,
        observed={},
    )


# ---------------------------------------------------------- the claim carries no verdict


def test_the_claim_closure_declares_no_verdict_field() -> None:
    assert verdict_vocabulary_violations() == []


def test_the_vocabulary_walk_is_not_vacuous() -> None:
    """A walk that reached no dataclass reports clean. The count is the guard."""
    assert claim_closure_size() >= 5


def test_control_a_planted_verdict_field_is_caught() -> None:
    """Without this the check above is indistinguishable from one that scans nothing."""

    @dataclass(frozen=True)
    class Tainted:
        run_id: str
        verdict: str

    assert verdict_vocabulary_violations(Tainted) == ["Tainted.verdict"]


def test_control_every_word_in_the_vocabulary_is_caught() -> None:
    """The vocabulary is data, so a word silently dropped from it would go unnoticed.

    Python keywords are skipped and cannot be otherwise: `pass` is unusable as a field
    name at the language level, so no dataclass can ever declare it. It stays in the
    vocabulary anyway — the check also reads annotations from types this suite does not
    construct, and a word that costs nothing to keep should not be removed on the
    strength of one host language's grammar.
    """
    for word in VERDICT_VOCABULARY:
        if keyword.iskeyword(word):
            continue
        tainted = type(
            "Planted",
            (),
            {"__annotations__": {"run_id": str, word: str}},
        )
        assert verdict_vocabulary_violations(dataclass(frozen=True)(tainted))


# ---------------------------------------------------- the outcome enum's deliberate gap


def test_no_outcome_member_describes_the_executor_dying() -> None:
    """Agent-attributed terminations only.

    A member for infrastructure trouble would let an adaptor report a killed executor as
    an agent result, moving harness flakiness into the numerator of the only number the
    autonomy gates read. It is unrepresentable rather than discouraged.
    """
    assert {o.value for o in WorkerOutcome} == {
        "agent_stopped", "budget_exhausted", "policy_violation", "aborted"
    }


def test_faults_carry_the_taxonomy_class_that_decides_the_retry() -> None:
    assert ContainmentFailure.taxonomy_class == "contract_violation"
    assert WorkerFault.taxonomy_class == "infrastructure"
    assert ClaimIncomplete.taxonomy_class == "contract_violation"


# ------------------------------------------------------------------- check_handle


def test_dispatch_refuses_an_empty_required_set() -> None:
    """A worker that requires nothing has been configured to check nothing, and from
    outside that is indistinguishable from every check passing (ADR-0007)."""
    with pytest.raises(ContainmentFailure, match="checks nothing"):
        check_handle(_handle(_result("C1", AssertionOutcome.PASSED)), frozenset())


def test_a_missing_assertion_refuses_the_dispatch() -> None:
    handle = _handle(_result("C1", AssertionOutcome.PASSED))
    with pytest.raises(ContainmentFailure, match="absent"):
        check_handle(handle, frozenset({"C1", "C7"}))


def test_a_failed_assertion_refuses_the_dispatch() -> None:
    handle = _handle(_result("C1", AssertionOutcome.FAILED))
    with pytest.raises(ContainmentFailure, match="did not pass"):
        check_handle(handle, frozenset({"C1"}))


def test_not_executed_is_a_failure_and_is_not_collapsed_into_passed() -> None:
    """F25. The single most common way a containment control fails is by not running."""
    handle = _handle(_result("C1", AssertionOutcome.NOT_EXECUTED))
    with pytest.raises(ContainmentFailure, match="not_executed"):
        check_handle(handle, frozenset({"C1"}))


def test_all_required_assertions_passed_permits_the_dispatch() -> None:
    """The positive control. Without it every test above is satisfied by a check that
    refuses unconditionally."""
    handle = _handle(
        _result("C1", AssertionOutcome.PASSED),
        _result("C7", AssertionOutcome.PASSED),
        _result("C9", AssertionOutcome.FAILED),  # present, not required — must not block
    )
    check_handle(handle, frozenset({"C1", "C7"}))
