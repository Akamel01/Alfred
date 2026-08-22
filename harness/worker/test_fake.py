"""Rehearsals of the `Worker` seam against the in-memory adaptor — interface only.

Every test here drives `InMemoryWorker` the way the control plane would drive a real
adaptor: through the five port methods, plus the recorded-call log, which is the one
interior the brief admits. Nothing reaches into attributes beyond that log, because a
rehearsal that inspects a fake's internals proves nothing about an adaptor whose
internals differ (`docs/tier1/worker-port-contract.md` § *Replaceability*: replacement
is only true if replacement is *checkable*).

The downstream decisions asserted throughout are the contract's own mapping table,
quoted as data below. No `CriterionRunner` exists yet to receive them; encoding the
table here means the first adaptor inherits a suite that already knows what each of its
returns must do to the merge rate, the retry decision, and the verdict vocabulary.
"""

from __future__ import annotations

import uuid
from typing import Final

import pytest
from harness.fingerprint.record import RunFingerprint
from harness.worker.fake import InMemoryWorker, RecordedCall, ScriptExhausted
from harness.worker.port import (
    AssertionOutcome,
    AssertionReport,
    AssertionResult,
    AttemptId,
    Budget,
    ClaimIncomplete,
    ContainmentFailure,
    MountMode,
    MountSpec,
    RunId,
    SandboxHandle,
    TaskId,
    Timeouts,
    Usage,
    Worker,
    WorkerClaim,
    WorkerError,
    WorkerFault,
    WorkerOutcome,
    WorkerSpec,
    claim_closure_size,
    verdict_vocabulary_violations,
)
from typing_extensions import get_protocol_members, is_protocol

REQUIRED: Final = frozenset({"C1", "C7"})

#: `docs/tier1/worker-port-contract.md` § *Faults, and how `indeterminate` is decided* —
#: the mapping column, verbatim. What each claim arm does downstream.
DOWNSTREAM_VERDICT: Final[dict[WorkerOutcome, str]] = {
    WorkerOutcome.AGENT_STOPPED: "decided downstream by CriterionRunner",
    WorkerOutcome.BUDGET_EXHAUSTED: "escalation with the attempt bundle",
    WorkerOutcome.POLICY_VIOLATION: "terminate",
    WorkerOutcome.ABORTED: "indeterminate",
}

#: The retry column of the same table. `POLICY_VIOLATION` is the only **never**.
RETRY_DECISION: Final[dict[WorkerOutcome, str]] = {
    WorkerOutcome.AGENT_STOPPED: "within the retry budget, visible criteria only",
    WorkerOutcome.BUDGET_EXHAUSTED: "no",
    WorkerOutcome.POLICY_VIOLATION: "never",
    WorkerOutcome.ABORTED: "operator decision",
}

#: The exception rows of the same table that permit a bounded requeue. A killed executor
#: requeues; a policy violation does not, ever.
REQUEUEABLE: Final = (WorkerFault, ClaimIncomplete)


# ------------------------------------------------------------------------- rig helpers


def _result(
    assertion_id: str, outcome: AssertionOutcome, *, premise_verified: bool = True
) -> AssertionResult:
    return AssertionResult(
        assertion_id=assertion_id,
        outcome=outcome,
        executed_inside_container=True,
        observed={},
        premise_verified=premise_verified,
    )


def _handle(run_id: RunId, *results: AssertionResult) -> SandboxHandle:
    return SandboxHandle(
        run_id=run_id,
        image_digest="sha256:" + "0" * 64,
        boot_report=AssertionReport(at="boot", results=results),
        mounts=(MountSpec("/host", "/repo", MountMode.READ_ONLY, "repo checkout"),),
    )


def _passing_handle(run_id: RunId) -> SandboxHandle:
    return _handle(
        run_id,
        _result("C1", AssertionOutcome.PASSED),
        _result("C7", AssertionOutcome.PASSED),
    )


def _fingerprint() -> RunFingerprint:
    return RunFingerprint(
        capability_id="collision-risk-quantification",
        model_version="test-model",
        prompt_version="p1",
        tool_version="t1",
        context_strategy_version="cs1",
        quant_artifact_sha256="a" * 64,
        inference_runtime_version="rt1",
        server_version="srv1",
        orchestrator_sha="o" * 64,
        harness_identity="harness-test",
        lockfile_sha256="l" * 64,
        criterion_set_version=1,
        model_id="model-under-test",
        quantization="q4",
        loaded_context_length=28000,
        parallel_slots=1,
        executor_name="in-memory-scripted",
        executor_commit_sha="e" * 64,
        adaptor_version="0",
        runtime_image_digest="sha256:" + "0" * 64,
        oracle_denylist_version="denylist-test",
        tool_description_sha256=("td" * 32,),
        seed_layer_order_sha256="s" * 64,
    )


def _spec(run_id: RunId, *, attempt_index: int = 0) -> WorkerSpec:
    return WorkerSpec(
        run_id=run_id,
        task_id=TaskId(uuid.uuid4()),
        attempt_id=AttemptId(uuid.uuid4()),
        attempt_index=attempt_index,
        fingerprint=_fingerprint(),
        seed=0,
        seed_layers=(),
        read_mounts=(MountSpec("/host", "/repo", MountMode.READ_ONLY, "repo checkout"),),
        write_mount=MountSpec("/host-out", "/out", MountMode.READ_WRITE, "patch output"),
        tools=(),
        budget=Budget(turn_cap=10, token_cap=1000, wallclock_cap_ms=60_000, iteration_cap=10),
        timeouts=Timeouts(
            model_request_s=120.0,
            turn_s=300.0,
            dispatch_s=1800.0,
            teardown_s=30.0,
            consecutive_model_timeouts_before_abort=2,
        ),
        schema_version=1,
    )


def _worker(*script: object, required: frozenset[str] = REQUIRED) -> InMemoryWorker:
    return InMemoryWorker(required_assertions=required, script=list(script))


# ------------------------------------------------------------- structural conformance


def test_the_fake_satisfies_the_worker_protocol_structurally() -> None:
    """Every protocol member exists on the class. The signature check is the point:
    a stand-in that drifts from the port's shape must fail here, before any rehearsal
    trusts it."""
    assert is_protocol(Worker)
    for member in get_protocol_members(Worker):
        assert callable(getattr(InMemoryWorker, member))


# ------------------------------------------------------- every arm crosses as a return


@pytest.mark.parametrize("arm", list(WorkerOutcome))
def test_each_scripted_arm_returns_as_a_claim_with_exactly_that_outcome(
    arm: WorkerOutcome,
) -> None:
    """Rule 1: the worker returns a claim, never a verdict. Every arm — including the
    ones a downstream judge will treat badly — crosses as a returned `WorkerClaim`, and
    nothing the fake fabricates decides the outcome upstream of the judge."""
    worker = _worker(arm)
    run = RunId(uuid.uuid4())

    claim = worker.dispatch(_passing_handle(run), _spec(run))

    assert type(claim) is WorkerClaim
    assert claim.outcome is arm
    assert claim.run_id == run


def test_each_arm_maps_to_the_downstream_decision_the_contract_table_assigns() -> None:
    """The table, checked as data over produced claims: every arm has exactly one row,
    and no arm's row is decided by the worker itself."""
    for arm in WorkerOutcome:
        worker = _worker(arm)
        run = RunId(uuid.uuid4())
        claim = worker.dispatch(_passing_handle(run), _spec(run))
        assert DOWNSTREAM_VERDICT[claim.outcome]
        assert RETRY_DECISION[claim.outcome] in {
            "never",
            "no",
            "operator decision",
            "within the retry budget, visible criteria only",
        }


# --------------------------------------------------------------- the killed-executor trap


def test_a_killed_executor_surfaces_as_a_fault_and_never_as_a_claim() -> None:
    """§ *Replaceability*, property 3: kill the executor mid-trajectory → `WorkerFault`.
    An adaptor that reports a killed executor as an agent failure is 'the single most
    likely defect in any adaptor'. Here the death raises, no claim exists afterwards,
    and the call log shows the dispatch happened — the failure is attributed, not lost."""
    worker = _worker(WorkerFault("executor died mid-trajectory"))
    run = RunId(uuid.uuid4())

    with pytest.raises(WorkerFault):
        worker.dispatch(_passing_handle(run), _spec(run))

    assert worker.claims == ()
    assert [c.method for c in worker.calls] == ["dispatch"]


def test_lost_evidence_surfaces_as_claim_incomplete_and_never_as_a_claim() -> None:
    """§ *Read recording*: persisted below observed is `ClaimIncomplete`, not a smaller
    log. Same assertion shape as the kill: raise, empty claim log."""
    worker = _worker(ClaimIncomplete("persisted event count below observed"))
    run = RunId(uuid.uuid4())

    with pytest.raises(ClaimIncomplete):
        worker.dispatch(_passing_handle(run), _spec(run))

    assert worker.claims == ()


def test_the_script_cannot_dress_a_death_as_an_agent_stopped_claim() -> None:
    """The trap closed at both ends. A pre-built claim — the only way to hand the fake a
    fabricated `AGENT_STOPPED` — is refused at construction, so a death can be expressed
    only as an exception class; and the taxonomy is closed, so no fourth kind of death
    smuggles in under a subclass."""
    source = _worker(WorkerOutcome.AGENT_STOPPED)
    run = RunId(uuid.uuid4())
    dressed = source.dispatch(_passing_handle(run), _spec(run))

    with pytest.raises(ValueError, match="not a scriptable outcome"):
        _worker(dressed)  # a real WorkerClaim object, offered as a script entry

    class OffTaxonomy(WorkerFault):
        """A fourth kind of infrastructure trouble, which the taxonomy refuses."""

    with pytest.raises(ValueError, match="not a scriptable outcome"):
        _worker(OffTaxonomy("novel death"))

    with pytest.raises(ValueError, match="not a scriptable outcome"):
        _worker(WorkerError("base-class instance"))  # type: ignore[arg-type]


# ------------------------------------------------------- POLICY_VIOLATION never retries


def _dispatch_with_bounded_requeue(
    worker: InMemoryWorker, budget: int = 3
) -> tuple[WorkerClaim, int]:
    """A minimal control-plane loop built straight off the contract table: requeue only
    on `WorkerFault`/`ClaimIncomplete` (bounded), treat every returned claim as final."""
    for attempt in range(budget):
        run = RunId(uuid.uuid4())
        try:
            return worker.dispatch(_passing_handle(run), _spec(run)), attempt + 1
        except REQUEUEABLE:
            continue
    raise AssertionError("requeue budget exhausted without a final answer")


def test_policy_violation_terminates_the_loop_on_the_first_attempt() -> None:
    """Table row: `POLICY_VIOLATION` → terminate, retry **never**. One dispatch, one
    returned claim, no second attempt — read off the recorded-call log, not internals."""
    worker = _worker(WorkerOutcome.POLICY_VIOLATION)

    claim, attempts = _dispatch_with_bounded_requeue(worker)

    assert claim.outcome is WorkerOutcome.POLICY_VIOLATION
    assert attempts == 1
    assert len([c for c in worker.calls if c.method == "dispatch"]) == 1


def test_worker_fault_requeues_within_the_bound_and_then_resolves() -> None:
    """The contrast that makes the previous test mean something: the same loop on the
    same worker spends its requeue budget on faults and stops at the first claim."""
    worker = _worker(
        WorkerFault("transient"), WorkerFault("transient"), WorkerOutcome.AGENT_STOPPED
    )

    claim, attempts = _dispatch_with_bounded_requeue(worker)

    assert claim.outcome is WorkerOutcome.AGENT_STOPPED
    assert attempts == 3


# ------------------------------------------------ containment failure = no run at all


def test_containment_failure_starts_nothing_there_is_nothing_to_abort() -> None:
    """Table row: `ContainmentFailure` → run does not start. No claim, and — because
    the abort clause pays out only when the trajectory had started — no `ABORTED`
    claim either when the operator aborts afterwards."""
    worker = _worker(
        ContainmentFailure("environment failed containment"), WorkerOutcome.AGENT_STOPPED
    )
    run = RunId(uuid.uuid4())

    with pytest.raises(ContainmentFailure):
        worker.dispatch(_passing_handle(run), _spec(run))

    worker.abort(run, timeout_s=1.0)

    assert worker.claims == ()


def test_guards_fire_before_the_script_so_a_benign_arm_cannot_mask_a_bad_handle() -> None:
    """Order is load-bearing: refusals are the port's judgement of the environment, and
    a script saying `AGENT_STOPPED` must not override it. After the refusal, the script
    is unconsumed — the next dispatch against a passing handle gets its arm."""
    worker = _worker(WorkerOutcome.AGENT_STOPPED)
    refused_run = RunId(uuid.uuid4())
    bad = _handle(
        refused_run,
        _result("C1", AssertionOutcome.FAILED),
        _result("C7", AssertionOutcome.PASSED),
    )

    with pytest.raises(ContainmentFailure, match="did not pass"):
        worker.dispatch(bad, _spec(refused_run))

    assert worker.claims == ()

    ok_run = RunId(uuid.uuid4())
    claim = worker.dispatch(_passing_handle(ok_run), _spec(ok_run))
    assert claim.outcome is WorkerOutcome.AGENT_STOPPED


# ----------------------------------------------------- check_handle refusals, via dispatch


@pytest.mark.parametrize(
    ("required", "results", "fragment"),
    [
        (frozenset(), (_result("C1", AssertionOutcome.PASSED),), "checks nothing"),
        (
            frozenset({"C1", "C7"}),
            (_result("C1", AssertionOutcome.PASSED),),
            "absent",
        ),
        (
            frozenset({"C1"}),
            (_result("C1", AssertionOutcome.NOT_EXECUTED),),
            "not_executed",
        ),
        (
            frozenset({"C1"}),
            (_result("C1", AssertionOutcome.PASSED, premise_verified=False),),
            "unverified premise",
        ),
    ],
)
def test_check_handle_refusals_fire_through_dispatch(
    required: frozenset[str],
    results: tuple[AssertionResult, ...],
    fragment: str,
) -> None:
    """The fake wires the port's own `check_handle`, at the default MEASUREMENT
    strictness — so every refusal text is the port's, including the vacuity refusal on
    an empty required set and ADR-0007's unverified-premise refusal."""
    worker = _worker(required=required)
    run = RunId(uuid.uuid4())
    handle = _handle(run, *results)

    with pytest.raises(ContainmentFailure, match=fragment):
        worker.dispatch(handle, _spec(run))

    assert worker.claims == ()


def test_a_handle_for_another_run_proves_nothing_and_is_refused() -> None:
    """The proof travels with the handle. A boot report addressed to run A says nothing
    about run B, and a claim citing it would carry foreign containment evidence."""
    worker = _worker(WorkerOutcome.AGENT_STOPPED)
    other_run = RunId(uuid.uuid4())
    dispatch_run = RunId(uuid.uuid4())

    with pytest.raises(ContainmentFailure, match="proof"):
        worker.dispatch(_passing_handle(other_run), _spec(dispatch_run))

    assert worker.claims == ()


# --------------------------------------------------- the vocabulary stays clean over fakes


def test_verdict_vocabulary_stays_empty_over_every_fake_produced_claim() -> None:
    """The closure check runs over `WorkerClaim` itself (the port's root), across
    claims produced by every arm plus an abort-emitted one — and the walk is asserted
    non-vacuous, because a walk that reached nothing also reports clean."""
    produced: list[WorkerClaim] = []
    for arm in WorkerOutcome:
        worker = _worker(arm)
        run = RunId(uuid.uuid4())
        produced.append(worker.dispatch(_passing_handle(run), _spec(run)))
    aborted = _worker(WorkerOutcome.AGENT_STOPPED)
    run = RunId(uuid.uuid4())
    aborted.dispatch(_passing_handle(run), _spec(run))
    aborted.abort(run, timeout_s=1.0)
    produced.extend(aborted.claims)

    assert produced
    assert all(type(c) is WorkerClaim for c in produced)
    assert verdict_vocabulary_violations() == []
    assert claim_closure_size() >= 5


# --------------------------------------------------------- what the fabricated claim says


def test_fabricated_claims_report_what_actually_happened_nothing() -> None:
    """No reads, zero usage, unchanged tree (`patch is None` — a real result, not an
    error, per the contract), agreeing event counts at the mandated zeros, and an
    observed fingerprint equal field-for-field to the declared record."""
    worker = _worker(WorkerOutcome.AGENT_STOPPED)
    run = RunId(uuid.uuid4())
    spec = _spec(run)

    claim = worker.dispatch(_passing_handle(run), spec)

    assert claim.patch is None
    assert claim.tree_sha256_initial == claim.tree_sha256_final
    assert claim.reads == ()
    assert claim.usage == Usage(
        turns=0,
        tool_calls=0,
        mutating_tool_calls=0,
        prompt_tokens=0,
        completion_tokens=0,
        cached_prefix_tokens=0,
        agent_ms=0,
        harness_ms=0,
        wallclock_ms=0,
    )
    events = claim.events
    assert events.observed_event_count == events.persisted_event_count == 0
    assert events.condensation_event_count == 0
    assert events.approval_event_count == 0
    assert claim.observed_fingerprint == spec.fingerprint.as_mapping()
    reports = claim.containment
    assert len(reports) == 1 and reports[0].at == "boot"


# --------------------------------------------------------------------------- lifecycle


def test_abort_before_any_trajectory_emits_nothing_and_stays_idempotent() -> None:
    worker = _worker()
    run = RunId(uuid.uuid4())

    worker.abort(run, timeout_s=1.0)
    worker.abort(run, timeout_s=1.0)

    assert worker.claims == ()
    assert [c.method for c in worker.calls] == ["abort", "abort"]


def test_abort_after_a_returned_claim_yields_exactly_one_aborted_claim() -> None:
    """I5, idempotent: N aborts, one `ABORTED` claim. The claim arrives through the
    same fabrication path and lands in the same log a dispatch-returned claim uses."""
    worker = _worker(WorkerOutcome.AGENT_STOPPED)
    run = RunId(uuid.uuid4())
    worker.dispatch(_passing_handle(run), _spec(run))

    worker.abort(run, timeout_s=1.0)
    worker.abort(run, timeout_s=1.0)

    assert [c.outcome for c in worker.claims] == [
        WorkerOutcome.AGENT_STOPPED,
        WorkerOutcome.ABORTED,
    ]


def test_abort_after_a_fault_does_not_invent_a_trajectory() -> None:
    """`WorkerFault`: the attempt could not be *shown* to have run. An unprovable start
    cannot ground the ABORTED claim the abort clause promises for started trajectories.
    (Interpretation flagged in the patch fragment: the contract does not spell this row
    out; the fake takes the reading that only a returned claim demonstrates a start.)"""
    worker = _worker(WorkerFault("executor died"))
    run = RunId(uuid.uuid4())

    with pytest.raises(WorkerFault):
        worker.dispatch(_passing_handle(run), _spec(run))
    worker.abort(run, timeout_s=1.0)

    assert worker.claims == ()


def test_teardown_is_idempotent_and_dispatch_after_it_refuses() -> None:
    """Teardown destroys the container; a later dispatch needs an execution plane that
    no longer exists, which is infrastructure fault territory — and the second
    teardown is silently idempotent, as the port specifies."""
    worker = _worker(WorkerOutcome.AGENT_STOPPED)
    run = RunId(uuid.uuid4())

    worker.teardown(run, timeout_s=1.0)
    worker.teardown(run, timeout_s=1.0)
    worker.abort(run, timeout_s=1.0)  # torn down: nothing to abort either

    with pytest.raises(WorkerFault, match="torn down"):
        worker.dispatch(_passing_handle(run), _spec(run))

    assert worker.claims == ()


# ---------------------------------------------------------------------------- recording


def test_every_port_call_is_recorded_in_order() -> None:
    """The recorded-call log is the observation channel rehearsals read; it must see
    identity, requirement enumeration, dispatch, abort and teardown, in call order."""
    worker = _worker(WorkerOutcome.AGENT_STOPPED)
    run = RunId(uuid.uuid4())

    worker.identity()
    worker.required_assertions()
    worker.dispatch(_passing_handle(run), _spec(run))
    worker.abort(run, timeout_s=1.0)
    worker.teardown(run, timeout_s=1.0)

    assert [c.method for c in worker.calls] == [
        "identity",
        "required_assertions",
        "dispatch",
        "abort",
        "teardown",
    ]
    assert all(isinstance(c, RecordedCall) for c in worker.calls)
    assert worker.calls[2].run_id == str(run)


# -------------------------------------------------------------------------- exhaustion


def test_a_spent_script_fails_loudly_instead_of_improvising() -> None:
    """An unscripted attempt gets `ScriptExhausted`, not an invented claim or fault —
    a rig that answers questions nobody scripted is authoring behaviour mid-run."""
    worker = _worker()
    run = RunId(uuid.uuid4())

    with pytest.raises(ScriptExhausted, match="script exhausted"):
        worker.dispatch(_passing_handle(run), _spec(run))


def test_required_assertions_round_trips_through_the_port() -> None:
    """The configured set comes back through the method the contract names, unchanged —
    and the constructor's copy means later mutation of the caller's set cannot widen
    what dispatch demands."""
    caller_held = frozenset({"C1", "C7"})
    worker = InMemoryWorker(required_assertions=caller_held)
    caller_mutated = caller_held | {"C16"}

    assert worker.required_assertions() == REQUIRED == caller_held
    assert worker.required_assertions() != caller_mutated
