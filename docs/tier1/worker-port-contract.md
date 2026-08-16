---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      The record shape, the claim/fault split and the read-recording obligation rest on measured behaviour of the selected lane — the content-channel defect (15–20% of calls), the silent reload to defaultContextLength, and the parallel-slot effect on prefix reuse — and on the Run Instrumentation Specification, which this port must be able to fill. Everything specific to the selected executor (OpenHands) rests on the plan's research notes and is **unverified first-hand**: the executor is not present in this repository and was not fetched. Those obligations are marked in place.
falsifies_if:  A conforming adaptor is written and Phase 1 finds a required instrumentation field that cannot be derived from what this port returns; or a second executor cannot be made to satisfy this contract without changing it; or a claim reaches the harness carrying a field the harness treats as a verdict.
review_after:  Phase 1
---

# Worker Port Contract

`Worker` is the seam between the control plane and the execution plane. Everything on
the far side of it is untrusted, disposable, and replaceable. This document specifies
what crosses it, in both directions, and what must be asserted before anything crosses
at all.

The port is written as typed Python because a signature is a contract and prose is not.
The code here is **specification**: it defines the shape the implementation must have.
It is not the implementation, and it does not live in `src/` or `harness/`.

## The three rules that generate the rest

1. **The worker returns a claim, never a verdict.** The claim type contains no field the
   harness reads as an outcome. This is enforced structurally, not by convention — see
   *Verdict-shaped fields*.
2. **A fault and a failure are different returns.** An agent that failed produces a
   claim. A worker that could not be shown to have run produces an exception. Collapsing
   them puts harness flakiness into merge rate, which is the one number the autonomy
   gates read.
3. **The port names no executor concept.** OpenHands appears in exactly one place in the
   system: the adaptor. If a term from a specific executor appears in a signature below,
   the contract is wrong.

## Identities and value types

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, NewType, Protocol, Sequence
from uuid import UUID

RunId      = NewType("RunId", UUID)   # uuid7, I4
TaskId     = NewType("TaskId", UUID)
AttemptId  = NewType("AttemptId", UUID)
Sha256     = NewType("Sha256", str)   # lowercase hex, 64 chars

@dataclass(frozen=True)
class ArtifactRef:
    """Content address, never a path (I3)."""
    sha256: Sha256
    size_bytes: int
    media_type: str
```

## What goes in

```python
class MountMode(Enum):
    READ_ONLY  = "ro"
    READ_WRITE = "rw"

@dataclass(frozen=True)
class MountSpec:
    """Fixed by the harness at dispatch and enforced by the mount (A9).

    The worker may not add, widen or re-target a mount. `container_path` is what the
    boot assertion enumerates and compares against; a mount present in the container
    and absent here is a containment failure, not a convenience.
    """
    host_source: str
    container_path: str
    mode: MountMode
    purpose: str          # free text, recorded; e.g. "repo checkout", "patch output"

@dataclass(frozen=True)
class SeedLayer:
    """One layer of the deterministic context seed, ordered most-stable-first (D45).

    Prefix order is architecture, not tuning: a KV prefix cache is hash-chained from
    token zero, so one changed token invalidates every layer after it. Retrieved and
    per-task-variable content is always the last layer.
    """
    name: str             # "conventions" | "protected_paths" | "capability" | "task" | "retrieved"
    stability_rank: int   # 0 = most stable. Strictly increasing across the tuple.
    content_sha256: Sha256

@dataclass(frozen=True)
class ToolSpec:
    """Declared per tool. `description_sha256` is a fingerprint field: a description
    alone changes behaviour without any name or signature changing (T5)."""
    name: str
    schema_sha256: Sha256
    description_sha256: Sha256
    mutating: bool        # declared, never inferred — the repetition metric needs it
    idempotent: bool

@dataclass(frozen=True)
class Budget:
    turn_cap: int
    token_cap: int
    wallclock_cap_ms: int
    iteration_cap: int

@dataclass(frozen=True)
class Timeouts:
    """Every external call carries an explicit timeout, set from measured
    distributions. Prefill alone costs ~45 s at 28k and ~76 s at 64k on this lane, so
    any library default in the 30–60 s range aborts healthy work."""
    model_request_s: float
    turn_s: float
    dispatch_s: float
    teardown_s: float
    consecutive_model_timeouts_before_abort: int

@dataclass(frozen=True)
class WorkerSpec:
    run_id: RunId
    task_id: TaskId
    attempt_id: AttemptId
    attempt_index: int
    fingerprint_sha256: Sha256
    fingerprint: Mapping[str, str]   # full D19/D40 field set — see Fingerprint obligations
    seed: int
    seed_layers: tuple[SeedLayer, ...]
    read_mounts: tuple[MountSpec, ...]
    write_mount: MountSpec           # exactly one: the patch output volume
    tools: tuple[ToolSpec, ...]
    budget: Budget
    timeouts: Timeouts
    schema_version: int              # I6
```

There is no `credentials` field, no `network` field and no `env` field. Their absence is
the contract: a worker that needs a credential cannot be given one through this port, and
network posture is the sandbox's property, asserted before the worker is handed a handle.

## What the sandbox hands over

The `Sandbox` port provisions; `Worker` executes inside what it provisioned. The handle
carries the proof, so `dispatch` can refuse structurally rather than trusting a caller to
have run the right checks in the right order.

```python
class AssertionOutcome(Enum):
    PASSED       = "passed"
    FAILED       = "failed"
    NOT_EXECUTED = "not_executed"   # never collapsed into FAILED, never into PASSED

@dataclass(frozen=True)
class AssertionResult:
    assertion_id: str        # "C1".."C15", see Sandbox Specification § Executor containment
    outcome: AssertionOutcome
    executed_inside_container: bool
    observed: Mapping[str, str]
    detail_ref: ArtifactRef | None

@dataclass(frozen=True)
class AssertionReport:
    at: str                  # "boot" | "end_of_run"
    results: tuple[AssertionResult, ...]

@dataclass(frozen=True)
class SandboxHandle:
    run_id: RunId
    image_digest: str
    boot_report: AssertionReport
    mounts: tuple[MountSpec, ...]     # as enumerated inside the container, not as requested
```

```python
def required_assertions(self) -> frozenset[str]: ...
```

`dispatch` raises `ContainmentFailure` when any id in `required_assertions()` is absent
from `boot_report`, or present with an outcome other than `PASSED`. `NOT_EXECUTED` is a
failure here for the same reason it is everywhere else in this system: an unproven
control is a failed control.

## What comes back

```python
class WorkerOutcome(Enum):
    """Agent-attributed terminations only. Every harness- or executor-attributed
    termination is an exception, not a value of this enum."""
    AGENT_STOPPED     = "agent_stopped"      # the agent ended its own trajectory
    BUDGET_EXHAUSTED  = "budget_exhausted"   # a cap in `Budget` was reached
    POLICY_VIOLATION  = "policy_violation"   # protected path, denied egress, denied query
    ABORTED           = "aborted"            # the harness stopped it deliberately

class ReadKind(Enum):
    FILE_READ = "file_read"
    SEARCH    = "search"
    LIST      = "list"
    RETRIEVAL = "retrieval"

@dataclass(frozen=True)
class ReadRecord:
    """D26. Derived by the adaptor from the executor's action/observation stream —
    never from anything the agent says it read."""
    index: int
    kind: ReadKind
    turn_index: int
    call_index: int | None
    path: str | None           # repo-relative; absolute paths are a containment finding
    query: str | None
    result_sha256: Sha256 | None
    result_row_ids: tuple[str, ...]
    bytes_returned: int
    truncated: bool

@dataclass(frozen=True)
class EventStreamRef:
    artifact: ArtifactRef
    observed_event_count: int    # events the adaptor received over the stream
    persisted_event_count: int   # event records found on the mounted volume, counted
                                 # by the harness outside the container
    condensation_event_count: int  # must be 0 (I16)
    approval_event_count: int      # must be 0 — see Sandbox Specification § C3

@dataclass(frozen=True)
class Usage:
    turns: int
    tool_calls: int
    mutating_tool_calls: int
    prompt_tokens: int
    completion_tokens: int
    cached_prefix_tokens: int    # separate from prompt_tokens, always
    agent_ms: int
    harness_ms: int
    wallclock_ms: int

@dataclass(frozen=True)
class WorkerClaim:
    run_id: RunId
    outcome: WorkerOutcome
    patch: ArtifactRef | None    # None when the tree is unchanged — a real result, not an error
    tree_sha256_initial: Sha256
    tree_sha256_final: Sha256
    events: EventStreamRef
    reads: tuple[ReadRecord, ...]
    turns: tuple["TurnRecord", ...]
    tool_calls: tuple["ToolCallRecord", ...]
    usage: Usage
    observed_fingerprint: Mapping[str, str]
    containment: tuple[AssertionReport, ...]   # boot and end-of-run
    schema_version: int
```

`TurnRecord` and `ToolCallRecord` carry exactly the fields the Run Instrumentation
Specification names for `turn` and `tool_call`, including `channel`, `salvage`,
`content_sha256`, `prefill_ms`/`decode_ms` and `served_context_length`. They are not
restated here: two copies of a field list is one copy too many, and the instrumentation
document is the one CI lints against.

## The port

```python
class Worker(Protocol):
    """Executes one attempt inside a provisioned sandbox and returns a claim.

    Implementations are stateless between attempts. Nothing survives a claim except
    what the claim references by content hash.
    """

    def identity(self) -> Mapping[str, str]:
        """Adaptor identity for the fingerprint: executor name, commit SHA resolved
        through any redirect, adaptor version, runtime image digest, and the id set of
        assertions this adaptor is able to make. Read before dispatch; recorded."""

    def required_assertions(self) -> frozenset[str]: ...

    def dispatch(self, handle: SandboxHandle, spec: WorkerSpec) -> WorkerClaim:
        """Run one attempt. Bounded by `spec.timeouts.dispatch_s`.

        Raises `ContainmentFailure`, `WorkerFault` or `ClaimIncomplete`. Returns in
        every other case, including every way the agent can fail.
        """

    def abort(self, run_id: RunId, *, timeout_s: float) -> None:
        """Idempotent (I5). Returns a claim through `dispatch` with
        `outcome = ABORTED` if the trajectory had started."""

    def teardown(self, run_id: RunId, *, timeout_s: float) -> None:
        """Destroy the container. Idempotent. Failure to tear down is an
        infrastructure fault and is never silent — a surviving container is a
        surviving credential-free but state-carrying environment."""
```

Timeouts are declared as parameters or as `Timeouts` fields on every method, because
`failure-semantics` requires every port method to declare one, and because an unbounded
wait in the execution plane is a lane that never returns.

## Faults, and how `indeterminate` is decided

```python
class WorkerError(Exception):
    taxonomy_class: str

class ContainmentFailure(WorkerError):
    """A required assertion is absent, failed, or was not executed."""
    taxonomy_class = "contract_violation"

class WorkerFault(WorkerError):
    """The executor could not be shown to have run the attempt it was given."""
    taxonomy_class = "infrastructure"

class ClaimIncomplete(WorkerError):
    """A claim was produced but cannot be trusted as a record of the attempt —
    persisted event count below observed, read log inconsistent with the stream,
    a condensation or approval event present, an observed fingerprint field that
    differs from the dispatched one."""
    taxonomy_class = "contract_violation"
```

The mapping is fixed, and it is the whole point of the split:

| Return | Verdict | Counted in merge rate | Retry |
|---|---|---|---|
| `WorkerClaim(AGENT_STOPPED)` | decided downstream by `CriterionRunner` | yes | within the retry budget, visible criteria only |
| `WorkerClaim(BUDGET_EXHAUSTED)` | escalation with the attempt bundle | denominator | no |
| `WorkerClaim(POLICY_VIOLATION)` | terminate | denominator, recorded as an attempt | **never** |
| `WorkerClaim(ABORTED)` | `indeterminate` | neither | operator decision |
| `ContainmentFailure` | run does not start | neither | not until the environment is rebuilt |
| `WorkerFault` | `indeterminate` | neither | bounded requeue, fingerprint preserved |
| `ClaimIncomplete` | `indeterminate` | neither | bounded requeue |

**The worker never returns `indeterminate` itself.** It returns a claim or it raises;
the verdict vocabulary belongs to the harness. An executor able to report its own run as
indeterminate is an executor able to report it as fine.

## Verdict-shaped fields

`WorkerClaim` and every type it transitively contains are forbidden from declaring a
field whose name is in the verdict vocabulary: `verdict`, `pass`, `passed`, `fail`,
`failed`, `indeterminate`, `merged`, `complete`, `completed`, `blocked`, `approved`,
`score`. CI lints the annotations, exactly as it lints agent-invoking node returns (I17),
because a graph engine raises only on concurrent unreducered writes and a sequential
write to a verdict field raises nothing at all.

`WorkerOutcome.AGENT_STOPPED` is deliberately not called `SUCCESS`. The agent stopping is
an event, not an achievement.

## Read recording is an obligation on the adaptor, not on the agent

D26 makes read-recording part of this port from Phase 1. Three properties make it worth
having, and all three fail if the agent is the source:

- **Derivation.** `reads` is derived from the executor's action/observation event stream.
  An agent-reported read log is an agent-authored summary of its own behaviour.
- **Completeness.** The adaptor must be able to demonstrate the log is complete, which is
  what `persisted_event_count` buys: if the executor's durable event count is below the
  count the adaptor observed, events were lost and the read log is a subset of unknown
  size. That is `ClaimIncomplete`, not a smaller log.
- **Ordering.** Reads carry `turn_index` and `call_index`, so the observed context can be
  replayed in the order it entered the model, which is what makes a fingerprint over
  nondeterministic retrieval meaningful at all.

### What "complete" means here, stated exactly, because it is weaker than it sounds

`persisted_event_count` proves the durable event count matches what the adaptor observed.
That closes one gap — events lost between the executor and the store — and **it cannot
prove the executor emitted an event for everything the agent did.** If an action occurs
with no event, both counts agree and the log is silently short. The completeness
demonstration is therefore *relative to the executor's emitted stream*, and it is only as
complete as that stream is.

Two consequences, both structural rather than incidental:

- **The log's granularity is the action, not the file read.** A shell action records the
  command; the files that command opened are not enumerated as reads. `cat`, a `grep`, a
  test run, or any subprocess reads content that enters the transcript and therefore the
  model's context, while the event stream records one action. *(Inferred from the
  executor's documented action/observation model; like every other executor-specific
  premise in this document, it is **unverified first-hand** and is the first thing an
  adaptor's instrumentation-completeness demonstration must measure — a scripted agent
  reading three files through a shell command must produce a log that says so, or say
  plainly that it cannot.)*
- **What bounds the read set is containment, not the log.** C9 fixes the mount set and C12
  makes everything outside the repo tree read-only, so the set of bytes the agent *could*
  have read is bounded and asserted even where the per-read event is missing. That bound
  is a stronger forensic object than the log in the one direction that matters after an
  incident, and it is already enforced.

**So the honest claim, and it is the one that belongs in the threat model:** the read log
is *positive* evidence — content it records did enter context, which is enough to identify
an injected payload that arrived through a recorded read, and enough for the
retrieval-miss-rate measurement (task failed *and* the needed file was never read, read as
*never recorded as read*). It is **not** *negative* evidence: "the agent never read X" does
not follow from X's absence from the log, and that is precisely the claim an injection
post-mortem wants. The upper bound on what could have been read comes from the mount set.

An independent observation channel — filesystem-level read auditing inside the container —
was considered and **rejected on cost against containment**, not on effort. The kernel
audit subsystem is not namespaced, `fanotify` and eBPF attachment need capabilities
(`CAP_AUDIT_CONTROL`, `CAP_SYS_ADMIN` or `CAP_BPF`) that the sandbox does not have and
should not be given, and the runtime here is a Linux VM under a desktop hypervisor where
host-side audit rules do not resolve to container-scoped paths cleanly. Buying a more
complete forensic trail by enlarging the privilege set of the thing being observed trades
the containment the trail exists to bound. Revisit if a run is ever executed on a Linux
host Alfred owns, where a host-side `fanotify` watcher outside the container's capability
set becomes available without granting the container anything.

## Fingerprint obligations

`spec.fingerprint` carries the full D19/D40 field set. The worker's own contribution —
and every one of these is a field something else can change without notice:

| Field | Why it is here |
|---|---|
| `executor_name`, `executor_commit_sha` | The canonical repository path redirects; the destination is what gets pinned, and the repository has no tags. |
| `adaptor_version` | Harness identity alone moves the same model by percentage points. |
| `runtime_image_digest` | Pinned by digest, mirrored locally, pulled outside the sandbox network namespace. |
| `oracle_denylist_version` | The D50 denylist is policy configuration; a run measured under one denylist is not comparable to a run measured under a weaker one. |
| `tool_description_sha256[]` | Descriptions change behaviour without names changing. |
| `seed_layer_order_sha256` | Reordering the seed invalidates every cached prefix and re-pays full prefill. |

`dispatch` compares `observed_fingerprint` against `spec.fingerprint` field by field and
raises `ClaimIncomplete` on any difference, including a field the executor reports and
the spec does not declare. **An adaptor records what it verified, never what it hoped
for** — the same rule the lane fingerprint assertion already implements.

## Replaceability, and what an adaptor must prove

The premise of the whole architecture is that workers are replaceable. That is only true
if replacement is *checkable*, so an adaptor is admitted only when it demonstrates:

1. **Assertion coverage.** `required_assertions()` is a superset of the containment set
   the Sandbox Specification marks mandatory. An adaptor that cannot assert compaction
   off, or cannot assert its executor exposes no approval surface, is not admissible —
   not "admissible with a note".
2. **Instrumentation completeness.** Every field in the Run Instrumentation
   Specification is derivable from what the adaptor returns, demonstrated against the
   scripted-agent verification suite, which replaces the model with fixed trajectories.
3. **Fault fidelity.** Injected faults produce the right side of the split. Kill the
   executor mid-trajectory → `WorkerFault`. Drop events → `ClaimIncomplete`. Deny a
   protected path → `WorkerClaim(POLICY_VIOLATION)`. An adaptor that reports a killed
   executor as an agent failure is the failure this port exists to prevent, and it is
   the single most likely defect in any adaptor.
4. **An epoch boundary is declared.** Adopting a different executor invalidates prior
   autonomy grants and makes historical wall-clock-per-merged-task incomparable. The
   swap is cheap; pretending the measurements survive it is not.

## Enforcement

- Schema: `WorkerSpec`, `WorkerClaim` and the record types are Pydantic models with
  `schema_version`; a claim that fails validation is `ClaimIncomplete`.
- Lint: no verdict-vocabulary field name anywhere in the claim closure; no import from
  any adaptor module into the verdict module (D39).
- Test: the adaptor conformance suite above runs on every adaptor change and on every
  change to `runtime_image_digest` or `executor_commit_sha`.
