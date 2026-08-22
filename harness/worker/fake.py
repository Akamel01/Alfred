"""The in-memory `Worker`: a scripted stand-in that rehearses the seam's semantics.

This adaptor dispatches nothing real and runs no executor. It exists so the rules that
govern the `Worker` port — the claim arms, the fault split, the structural refusals, the
lifecycle — can be rehearsed through the interface before a real adaptor lands, using the
port's own guards rather than a mock of them. Execution-order doctrine forbids
orchestration before per-task merge rate clears K3's Wilson lower bound
(`docs/tier2/execution-order.md` § *What must not be built yet*); this module is the tool
that lets the seam be exercised without building any of it. It is rehearsal tooling, and
nothing here may grow into a driver: the moment something dispatches this worker in
production, the doctrine line has been crossed.

Three properties, each inherited rather than reimplemented:

1. **The real guards run.** `dispatch` calls `check_handle` (`harness/worker/port.py`)
   with this worker's required-assertion set, at the default `Admissibility.MEASUREMENT`
   — the strict end, per that function's own docstring on why the permissive case is the
   one somebody has to ask for. An empty required set therefore refuses here exactly as
   it refuses anywhere else, and the refusal text is the port's, not a copy.
2. **Deaths surface as deaths.** The script vocabulary is the port's: the four claim
   arms, or the three exception classes `dispatch` may raise
   (`docs/tier1/worker-port-contract.md` § *The port*: "Raises `ContainmentFailure`,
   `WorkerFault` or `ClaimIncomplete`"). `WorkerOutcome` deliberately has no member for a
   dead executor, so a kill can enter the script only as `WorkerFault` or
   `ClaimIncomplete` — the constructor refuses everything else, including a pre-built
   `WorkerClaim`, which is the shape a dressed-up death would have to arrive in.
3. **Claims are fabricated faithful, not supplied.** The caller scripts an arm; the
   worker builds the whole `WorkerClaim`. A scripted claim object would let a rehearsal
   author attach whatever evidence the story needed; a fabricated one reports what this
   worker actually did — nothing. The tree is unchanged, so `patch is None` (the contract
   defines an unchanged tree as a real result, not an error), event counts agree with
   zero condensation and zero approval events, and `observed_fingerprint` is the declared
   record verbatim — then compared back through `RunFingerprint.compare` so any drift
   between what was dispatched and what the claim reports fails as `ClaimIncomplete`,
   which is the obligation the contract puts on every adaptor.

Lifecycle follows the port's stated semantics. `abort` is idempotent (I5) and produces
its `ABORTED` claim only when the trajectory had demonstrably started — meaning a
previous `dispatch` for that run *returned*. A `WorkerFault` does not count: its own
definition is that the attempt could not be shown to have run, and an unprovable start
cannot ground an `ABORTED` claim. A `ContainmentFailure` counts double against it: the
contract table's row is "run does not start", so there is nothing to abort. `teardown`
is idempotent and destroys the run for dispatch purposes; a `dispatch` against a torn-
down run raises `WorkerFault` — the execution plane that attempt needed no longer
exists. A handle whose `run_id` does not match the spec's is refused as a
`ContainmentFailure`: the handle carries the proof, and proof addressed to another run
proves nothing about this one.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from harness.worker.port import (
    ArtifactRef,
    ClaimIncomplete,
    ContainmentFailure,
    EventStreamRef,
    RunId,
    SandboxHandle,
    Sha256,
    Usage,
    WorkerClaim,
    WorkerError,
    WorkerFault,
    WorkerOutcome,
    WorkerSpec,
    check_handle,
)

__all__ = [
    "InMemoryWorker",
    "RecordedCall",
    "ScriptEntry",
    "ScriptExhausted",
]


#: What a script may contain. Exactly the port's return vocabulary (four arms) plus its
#: raise vocabulary (three classes) — anything richer would reopen the door the claim/
#: fault split closed.
ScriptEntry = WorkerOutcome | ContainmentFailure | WorkerFault | ClaimIncomplete

#: The three exception classes `Worker.dispatch` is specified to raise. Subclasses and
#: the `WorkerError` base are refused: the taxonomy is closed, and a fourth kind of
#: death is either one of these or a bug in the thing being rehearsed.
_RAISE_CLASSES: Final = (ContainmentFailure, WorkerFault, ClaimIncomplete)


class ScriptExhausted(RuntimeError):
    """The script ran dry on a dispatch.

    Rig misuse, not a worker outcome — a spent script means the rehearsal asked for more
    attempts than it scripted, and answering that with a claim or a fault would invent
    behaviour nobody wrote down.
    """


@dataclass(frozen=True)
class RecordedCall:
    """One call on the worker, as the call log exposes it.

    This log is the only interior a rehearsal may inspect; everything else goes through
    the port like it would with a real adaptor.
    """

    method: str
    run_id: str | None
    detail: str


def _digest(label: str) -> Sha256:
    """A deterministic content address for a fabricated artifact.

    Real-looking rather than constant, so two runs' fabricated artifacts cannot collide
    on their address and a rehearsal that asserts content-addressing behaves is not
    fooled by a placeholder shared across claims.
    """
    return Sha256(hashlib.sha256(label.encode()).hexdigest())


class InMemoryWorker:
    """The `Worker` protocol, satisfied structurally and scripted behaviourally.

    Stateless between attempts in the port's sense: nothing survives a claim except
    what the claim references by content hash. The call log survives, deliberately —
    it is the observation channel the rehearsal suite reads, and it is not part of
    what crosses the port.
    """

    def __init__(
        self,
        *,
        required_assertions: frozenset[str],
        script: Sequence[ScriptEntry] = (),
    ) -> None:
        self._required: Final[frozenset[str]] = frozenset(required_assertions)
        self._script: tuple[WorkerOutcome | WorkerError, ...] = tuple(
            _normalize(entry) for entry in script
        )
        self._cursor = 0
        self._calls: list[RecordedCall] = []
        self._claims: list[WorkerClaim] = []
        # Runs whose last dispatch returned — the only runs where "the trajectory had
        # started" is demonstrable, which is the condition the abort clause states.
        self._started: dict[RunId, tuple[SandboxHandle, WorkerSpec]] = {}
        self._aborted: set[RunId] = set()
        self._torn_down: set[RunId] = set()

    # ------------------------------------------------------------- observation

    @property
    def calls(self) -> tuple[RecordedCall, ...]:
        """Every call made on this worker, in order."""
        return tuple(self._calls)

    @property
    def claims(self) -> tuple[WorkerClaim, ...]:
        """Every claim that crossed the port, dispatch-returned and abort-emitted alike."""
        return tuple(self._claims)

    # ------------------------------------------------------------------ the port

    def identity(self) -> Mapping[str, str]:
        """Adaptor identity, honestly labelled as the fake it is.

        Shaped like the worker fields of `RunFingerprint` so a rehearsal can exercise
        whatever reads identity; every value says in-memory rather than impersonating an
        executor. `asserts` is the id set this worker is able to "make" — the required
        set it will demand at dispatch.
        """
        self._record("identity", None, "")
        return {
            "executor_name": "in-memory-scripted",
            "executor_commit_sha": "none-this-worker-runs-no-executor",
            "adaptor_version": "0-rehearsal-only",
            "runtime_image_digest": "none-this-worker-provisions-nothing",
            "asserts": ",".join(sorted(self._required)),
        }

    def required_assertions(self) -> frozenset[str]:
        self._record("required_assertions", None, "")
        return frozenset(self._required)

    def dispatch(self, handle: SandboxHandle, spec: WorkerSpec) -> WorkerClaim:
        """Run one scripted attempt.

        Order is load-bearing: the real guards run first and the script is consulted
        only after they pass. A rehearsal that passes therefore cannot have been passed
        by a lenient script papering over a refusal the port would have raised — and a
        scripted benign arm behind a failing handle still refuses.
        """
        self._record("dispatch", str(spec.run_id), f"cursor={self._cursor}")

        if spec.run_id in self._torn_down:
            raise WorkerFault(
                f"run {spec.run_id} was torn down; the container this dispatch needs "
                "no longer exists"
            )
        if handle.run_id != spec.run_id:
            raise ContainmentFailure(
                f"the handle proves run {handle.run_id}, the spec dispatches run "
                f"{spec.run_id}; the proof travels with the handle and this is not "
                "its run"
            )

        # Default admissibility: MEASUREMENT — the strict end, on purpose. See the
        # `check_handle` docstring for why the permissive case must be asked for.
        check_handle(handle, frozenset(self._required))

        if self._cursor >= len(self._script):
            raise ScriptExhausted(
                f"script exhausted at dispatch #{self._cursor + 1}; a rig that answers "
                "an unscripted attempt would be inventing behaviour"
            )
        entry = self._script[self._cursor]
        self._cursor += 1

        if isinstance(entry, WorkerError):
            raise entry

        claim = self._fabricate(handle, spec, entry)
        self._claims.append(claim)
        self._started[spec.run_id] = (handle, spec)
        return claim

    def abort(self, run_id: RunId, *, timeout_s: float) -> None:  # noqa: ARG002
        """Stop the run. Idempotent (I5); emits at most one `ABORTED` claim.

        The contract: "Returns a claim through `dispatch` with `outcome = ABORTED` if
        the trajectory had started." Here "had started" means a dispatch for this run
        *returned* — a fault leaves the start unproven and grounds no claim, and a
        contained-out or torn-down run never started at all. Repeated calls change
        nothing after the first, which is what idempotent means rather than what it
        resembles.

        `timeout_s` is declared and unused: the contract requires every port method to
        declare its timeout, and this worker waits for nothing that could time out.
        """
        self._record("abort", str(run_id), "")
        if run_id in self._aborted or run_id in self._torn_down:
            return
        started = self._started.get(run_id)
        if started is None:
            return
        self._aborted.add(run_id)
        handle, spec = started
        self._claims.append(self._fabricate(handle, spec, WorkerOutcome.ABORTED))

    def teardown(self, run_id: RunId, *, timeout_s: float) -> None:  # noqa: ARG002
        """Destroy the run's container. Idempotent.

        The contract: "Destroy the container. Idempotent. Failure to tear down is an
        infrastructure fault and is never silent." Nothing here can fail to tear down —
        which is stated plainly rather than left implied, because a fake whose teardown
        could not fail proves nothing about callers that handle failure; the real
        adaptor owes that path and this one does not rehearse it.

        `timeout_s`: see `abort`.
        """
        self._record("teardown", str(run_id), "")
        self._torn_down.add(run_id)

    # ---------------------------------------------------------------- internals

    def _record(self, method: str, run_id: str | None, detail: str) -> None:
        self._calls.append(RecordedCall(method=method, run_id=run_id, detail=detail))

    def _fabricate(
        self, handle: SandboxHandle, spec: WorkerSpec, arm: WorkerOutcome
    ) -> WorkerClaim:
        """Build the claim the arm deserves, from what this worker actually did.

        Which is nothing: no reads, zero usage, an unchanged tree (`patch is None`, and
        equal tree hashes), an event stream whose persisted count equals the observed
        count at zero — completeness holds trivially, and the condensation and approval
        counters sit at their mandated zeros. `containment` carries the boot report the
        handle presented and nothing else: no end-of-run report is fabricated, because
        none was executed and a rehearsal tool that mints assertion reports is
        manufacturing the very evidence it exists to test.
        """
        claim = WorkerClaim(
            run_id=spec.run_id,
            outcome=arm,
            patch=None,
            tree_sha256_initial=_digest(f"{spec.run_id}:tree"),
            tree_sha256_final=_digest(f"{spec.run_id}:tree"),
            events=EventStreamRef(
                artifact=ArtifactRef(
                    sha256=_digest(f"{spec.run_id}:events"),
                    size_bytes=0,
                    media_type="application/json",
                ),
                observed_event_count=0,
                persisted_event_count=0,
                condensation_event_count=0,
                approval_event_count=0,
            ),
            reads=(),
            usage=Usage(
                turns=0,
                tool_calls=0,
                mutating_tool_calls=0,
                prompt_tokens=0,
                completion_tokens=0,
                cached_prefix_tokens=0,
                agent_ms=0,
                harness_ms=0,
                wallclock_ms=0,
            ),
            observed_fingerprint=spec.fingerprint.as_mapping(),
            containment=(handle.boot_report,),
            schema_version=spec.schema_version,
        )
        # The contract puts comparison on every dispatch: observed against declared,
        # through `RunFingerprint.compare`, raising `ClaimIncomplete` on any difference.
        # The fake reports the declared mapping verbatim, so this passes by construction
        # — and if fabrication ever drifts from the spec it fails here instead of
        # handing the rehearsal a claim that lies about its own configuration.
        diffs = spec.fingerprint.compare(claim.observed_fingerprint)
        if diffs:
            raise ClaimIncomplete(
                "fabricated claim drifted from the dispatched fingerprint: "
                + "; ".join(str(d) for d in diffs)
            )
        return claim


def _normalize(entry: object) -> WorkerOutcome | WorkerError:
    """Validate one script entry against the port's vocabulary, eagerly.

    Construction is where a mistyped script dies — before any dispatch, so a rehearsal
    cannot discover mid-run that its author expressed a death as something that returns.
    Classes are accepted for brevity and instantiated here; instances pass through.
    Everything else is refused, and the refusal names the trap: there is no fifth way
    to say "the executor died".
    """
    if isinstance(entry, WorkerOutcome):
        return entry
    if isinstance(entry, type) and entry in _RAISE_CLASSES:
        return entry(f"scripted {entry.__name__}")
    if type(entry) in _RAISE_CLASSES:
        return entry  # type(entry) is exactly one of the three: no subclass drift
    raise ValueError(
        f"not a scriptable outcome: {entry!r}. The script speaks the port's vocabulary "
        "only — a WorkerOutcome arm, or one of ContainmentFailure/WorkerFault/"
        "ClaimIncomplete. WorkerOutcome deliberately has no member for a dead executor, "
        "so infrastructure trouble can be scripted only as WorkerFault or "
        "ClaimIncomplete and can never cross as a claim."
    )
