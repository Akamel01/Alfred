"""The `Worker` port. A claim crosses it, or an exception does — never a verdict.

Specified in `docs/tier1/worker-port-contract.md`; this is that contract as executable
types. Three rules generate everything else:

1. **The worker returns a claim, never a verdict.** No type reachable from `WorkerClaim`
   declares a field the harness reads as an outcome, and `verdict_vocabulary_violations`
   checks that mechanically rather than trusting review.
2. **A fault and a failure are different returns.** An agent that failed produces a claim;
   an executor that could not be shown to have run raises. The most likely defect in any
   adaptor is reporting a killed executor as an agent failure, which moves harness
   flakiness into the numerator of the only number the autonomy gates read — so origin is
   part of the return type rather than something inferred from an exception later.
3. **The port names no executor concept.** OpenHands appears in the adaptor and nowhere
   else. A term from a specific executor in a signature here means the contract is wrong.

Nothing in this module knows what an executor is, and that is what makes the swap the
`Worker` interface exists for actually cheap rather than merely intended.
"""

from __future__ import annotations

import dataclasses
import typing
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Final, NewType, Protocol
from uuid import UUID

from harness.fingerprint.record import RunFingerprint

RunId = NewType("RunId", UUID)
TaskId = NewType("TaskId", UUID)
AttemptId = NewType("AttemptId", UUID)
Sha256 = NewType("Sha256", str)


# ---------------------------------------------------------------------- value types


@dataclass(frozen=True)
class ArtifactRef:
    """Content address, never a path (I3)."""

    sha256: Sha256
    size_bytes: int
    media_type: str


class MountMode(Enum):
    READ_ONLY = "ro"
    READ_WRITE = "rw"


@dataclass(frozen=True)
class MountSpec:
    """Fixed by the harness at dispatch and enforced by the mount (A9).

    The worker may not add, widen or re-target a mount. A mount present in the container
    and absent from this set is a containment failure, not a convenience — the asserted
    mount set is what bounds the bytes that could have been read, and it is a stronger
    forensic object than the read log in the direction an incident actually asks about.
    """

    host_source: str
    container_path: str
    mode: MountMode
    purpose: str


@dataclass(frozen=True)
class SeedLayer:
    """One layer of the context seed, ordered most-stable-first (D45).

    Prefix order is architecture rather than tuning: a KV prefix cache is hash-chained
    from token zero, so one changed token invalidates every layer after it. Retrieved and
    per-task-variable content is always last. On this lane the difference is measured at
    two orders of magnitude — 22.7 s cold against 0.178 s warm on an identical prefix.
    """

    name: str
    stability_rank: int
    content_sha256: Sha256


@dataclass(frozen=True)
class ToolSpec:
    """`description_sha256` is a fingerprint field: a description alone changes behaviour
    with no name and no signature changing, which is the tool-poisoning shape (T5)."""

    name: str
    schema_sha256: Sha256
    description_sha256: Sha256
    mutating: bool
    idempotent: bool


@dataclass(frozen=True)
class Budget:
    turn_cap: int
    token_cap: int
    wallclock_cap_ms: int
    iteration_cap: int


@dataclass(frozen=True)
class Timeouts:
    """Set from measured distributions, never from a library default.

    Prefill alone costs ~45 s at 28k and ~76 s at 64k on this lane, so any default in the
    30-60 s range aborts healthy work before it has generated a token.
    """

    model_request_s: float
    turn_s: float
    dispatch_s: float
    teardown_s: float
    consecutive_model_timeouts_before_abort: int


@dataclass(frozen=True)
class WorkerSpec:
    """Everything the attempt is given.

    There is no `credentials` field, no `network` field and no `env` field, and their
    absence is the contract: a worker that needs a credential cannot be handed one
    through this port, and network posture is the sandbox's property, asserted before a
    handle exists.
    """

    run_id: RunId
    task_id: TaskId
    attempt_id: AttemptId
    attempt_index: int
    # One typed record, and the digest is a property of it rather than a field beside it.
    # A supplied `fingerprint_sha256` is a claim about the fields; a computed one is a
    # function of them, and two fields that can disagree eventually will.
    fingerprint: RunFingerprint
    seed: int
    seed_layers: tuple[SeedLayer, ...]
    read_mounts: tuple[MountSpec, ...]
    write_mount: MountSpec
    tools: tuple[ToolSpec, ...]
    budget: Budget
    timeouts: Timeouts
    schema_version: int


# ------------------------------------------------------------- what the sandbox proves


class AssertionOutcome(Enum):
    PASSED = "passed"
    FAILED = "failed"
    # Never collapsed into either neighbour. An unproven control is a failed control.
    NOT_EXECUTED = "not_executed"


@dataclass(frozen=True)
class AssertionResult:
    assertion_id: str
    outcome: AssertionOutcome
    executed_inside_container: bool
    observed: Mapping[str, str]
    detail_ref: ArtifactRef | None = None
    # ADR-0007's third outcome, carried across the boundary rather than left on the probe.
    # An assertion whose subject was never inspected first-hand can be `passed` and vacuous:
    # a config key read from a research note rather than from source passes harmlessly if the
    # feature is *absent* and passes deceptively if it is merely *misnamed*. Without this
    # field the state exists on the probe report and is invisible to `check_handle`, which is
    # the only thing that gates dispatch — so it could be recorded and never acted on.
    #
    # Defaults True because the overwhelming majority of assertions rest on facts observed
    # inside the container. An adaptor that means "unverified" has to say so.
    premise_verified: bool = True


@dataclass(frozen=True)
class AssertionReport:
    at: str
    results: tuple[AssertionResult, ...]

    def by_id(self) -> Mapping[str, AssertionResult]:
        return {r.assertion_id: r for r in self.results}

    @property
    def unverified_premises(self) -> tuple[str, ...]:
        """Which assertions rest on a premise nobody has checked first-hand.

        What a reader consults before quoting a green report as evidence, and what
        `check_handle` refuses on when the run is a measurement.
        """
        return tuple(r.assertion_id for r in self.results if not r.premise_verified)


class Admissibility(Enum):
    """What the run is for, which decides how an unverified premise is treated.

    ADR-0007: a run whose containment rests on unread executor vocabulary is admissible for
    **build** work and not admissible as a **measurement** under I16 or T10. The distinction
    is real — refusing build work would stop the executor being integrated at all, and
    admitting a measurement would put a number into the merge rate that rests on a name
    nobody checked.

    There is deliberately no third member and no default of convenience.
    """

    BUILD = "build"
    MEASUREMENT = "measurement"


@dataclass(frozen=True)
class SandboxHandle:
    """The proof travels with the handle, so `dispatch` can refuse structurally.

    `mounts` is what was enumerated *inside* the container, not what was requested. The
    difference is the only thing that distinguishes a mount set from a mount intention.
    """

    run_id: RunId
    image_digest: str
    boot_report: AssertionReport
    mounts: tuple[MountSpec, ...]


# ------------------------------------------------------------------ what comes back


class WorkerOutcome(Enum):
    """Agent-attributed terminations only.

    Every harness- or executor-attributed termination is an exception, not a member here.
    There is deliberately no member for "the executor died": adding one would let an
    adaptor report infrastructure trouble as an agent result, which is the defect this
    split exists to make unrepresentable.
    """

    AGENT_STOPPED = "agent_stopped"
    BUDGET_EXHAUSTED = "budget_exhausted"
    POLICY_VIOLATION = "policy_violation"
    ABORTED = "aborted"


class ReadKind(Enum):
    FILE_READ = "file_read"
    SEARCH = "search"
    LIST = "list"
    RETRIEVAL = "retrieval"


@dataclass(frozen=True)
class ReadRecord:
    """D26, and it is positive evidence only.

    Derived by the adaptor from the executor's action/observation stream, never from
    anything the agent says it read. Content it records did enter context; the absence of
    a read is *not* evidence the read did not happen, because the granularity is the
    action and files opened inside a shell command arrive as one command.
    """

    index: int
    kind: ReadKind
    turn_index: int
    call_index: int | None
    path: str | None
    query: str | None
    result_sha256: Sha256 | None
    result_row_ids: tuple[str, ...]
    bytes_returned: int
    truncated: bool


@dataclass(frozen=True)
class EventStreamRef:
    """Counts, because completeness is demonstrated against the executor's own durable
    count and nothing else can demonstrate it from outside."""

    artifact: ArtifactRef
    observed_event_count: int
    persisted_event_count: int
    # Must be zero. Compaction upstream of a verdict is a lossy summary standing in for
    # the record (I16), and the executor ships one by default.
    condensation_event_count: int
    # Must be zero. An approval inside the executor is a second authorization path the
    # evidence chain never sees, which would make the most privileged actor (T10) the
    # least audited one.
    approval_event_count: int


@dataclass(frozen=True)
class Usage:
    turns: int
    tool_calls: int
    mutating_tool_calls: int
    prompt_tokens: int
    completion_tokens: int
    # Separate from prompt_tokens, always. Folded together, a 140x prefix-cache win and a
    # lane that silently stopped reusing its cache report the same number.
    cached_prefix_tokens: int
    agent_ms: int
    harness_ms: int
    wallclock_ms: int


@dataclass(frozen=True)
class WorkerClaim:
    """What the agent says happened. A claim, never a fact.

    `patch is None` means the tree is unchanged, and that is a real result rather than an
    error: a run that took no actions belongs in the merge-rate denominator at the floor.
    """

    run_id: RunId
    outcome: WorkerOutcome
    patch: ArtifactRef | None
    tree_sha256_initial: Sha256
    tree_sha256_final: Sha256
    events: EventStreamRef
    reads: tuple[ReadRecord, ...]
    usage: Usage
    # Stays a mapping, and deliberately. `RunFingerprint` is what Alfred *declared*; this
    # is what the executor *reported*, and a dataclass cannot represent a field the record
    # never declared — which is precisely the direction `RunFingerprint.compare` checks and
    # the contract raises on. Typing this would delete the check by making its subject
    # unrepresentable. `object` rather than `str` because a context length is an int.
    observed_fingerprint: Mapping[str, object]
    containment: tuple[AssertionReport, ...]
    schema_version: int


# --------------------------------------------------------------------------- faults


class WorkerError(Exception):
    taxonomy_class: str = "unknown"


class ContainmentFailure(WorkerError):
    """A required assertion is absent, failed, or was not executed."""

    taxonomy_class = "contract_violation"


class WorkerFault(WorkerError):
    """The executor could not be shown to have run the attempt it was given."""

    taxonomy_class = "infrastructure"


class ClaimIncomplete(WorkerError):
    """A claim exists but cannot be trusted as a record of the attempt."""

    taxonomy_class = "contract_violation"


# ------------------------------------------------------------------------- the port


class Worker(Protocol):
    """Executes one attempt inside a provisioned sandbox and returns a claim.

    Stateless between attempts. Nothing survives a claim except what the claim references
    by content hash.
    """

    def identity(self) -> Mapping[str, str]:
        """Adaptor identity for the fingerprint. Read before dispatch; recorded."""
        ...

    def required_assertions(self) -> frozenset[str]:
        ...

    def dispatch(self, handle: SandboxHandle, spec: WorkerSpec) -> WorkerClaim:
        """Run one attempt. Raises on containment, fault or incompleteness; returns in
        every other case, including every way the agent can fail."""
        ...

    def abort(self, run_id: RunId, *, timeout_s: float) -> None:
        ...

    def teardown(self, run_id: RunId, *, timeout_s: float) -> None:
        ...


# -------------------------------------------------------- the structural refusals


def check_handle(
    handle: SandboxHandle,
    required: frozenset[str],
    *,
    admissibility: Admissibility = Admissibility.MEASUREMENT,
) -> None:
    """Refuse to dispatch unless every required assertion is present and passed.

    `admissibility` defaults to `MEASUREMENT`, which is the strict end. A default of `BUILD`
    would make every caller that forgot the argument admit a vacuous control into the merge
    rate, and the whole point of the flag is that the permissive case is the one somebody
    has to ask for.

    Lives here rather than in each adaptor: a refusal reimplemented per adaptor is a
    refusal that will eventually be implemented once with a subtle difference, and this
    is the check standing between an unproven container and a measured merge rate.

    An empty `required` set raises. A worker that requires nothing has not been configured
    — it has been configured to check nothing, and the two are indistinguishable from the
    outside, which is the vacuity class ADR-0007 names.
    """
    if not required:
        raise ContainmentFailure(
            "the required-assertion set is empty; a dispatch that checks nothing cannot "
            "be distinguished from one whose checks all passed"
        )

    present = handle.boot_report.by_id()
    missing = sorted(required - present.keys())
    if missing:
        raise ContainmentFailure(f"required assertions absent from the boot report: {missing}")

    not_passed = sorted(
        f"{i}={present[i].outcome.value}"
        for i in required
        if present[i].outcome is not AssertionOutcome.PASSED
    )
    if not_passed:
        raise ContainmentFailure(
            f"required assertions did not pass: {not_passed}. `not_executed` is a failure "
            "here for the same reason it is everywhere else: an unproven control is a "
            "failed control."
        )

    if admissibility is Admissibility.MEASUREMENT:
        unverified = sorted(i for i in required if not present[i].premise_verified)
        if unverified:
            raise ContainmentFailure(
                f"required assertions rest on an unverified premise: {unverified}. Each "
                "passed, and each may have passed vacuously — a control named by a key "
                "nobody read reports the same green whether the feature is absent or "
                "merely misnamed (ADR-0007). Admissible for build work, not as a "
                "measurement under I16 or T10."
            )


VERDICT_VOCABULARY: Final = frozenset(
    {
        "verdict", "pass", "passed", "fail", "failed", "indeterminate",
        "merged", "complete", "completed", "blocked", "approved", "score",
    }
)

CLAIM_CLOSURE_ROOT: Final = "WorkerClaim"


def _reachable_dataclasses(root: type) -> set[type]:
    seen: set[type] = set()
    stack: list[type] = [root]
    while stack:
        current = stack.pop()
        if current in seen or not dataclasses.is_dataclass(current):
            continue
        seen.add(current)
        hints = typing.get_type_hints(current)
        for annotation in hints.values():
            stack.extend(
                arg
                for arg in (annotation, *typing.get_args(annotation))
                if isinstance(arg, type)
            )
    return seen


def verdict_vocabulary_violations(root: type = WorkerClaim) -> Sequence[str]:
    """Every field in the claim's transitive closure whose name is a verdict word.

    Checked mechanically because convention does not hold this. A graph engine raises
    only on *concurrent* unreducered writes, so a sequential write to a verdict field
    raises nothing at all — and a claim carrying a field named `passed` is a worker that
    has been handed the vocabulary of the thing that judges it.

    Returns the empty sequence when the closure is clean. **The caller must also assert
    the closure was non-empty**: a walk that reached no dataclass reports clean.
    """
    violations: list[str] = []
    for cls in _reachable_dataclasses(root):
        for field in dataclasses.fields(cls):
            if field.name.lower() in VERDICT_VOCABULARY:
                violations.append(f"{cls.__name__}.{field.name}")
    return sorted(violations)


def claim_closure_size(root: type = WorkerClaim) -> int:
    """How many dataclasses the vocabulary check actually walked. The vacuity guard."""
    return len(_reachable_dataclasses(root))
