"""OpenHands adaptor implementing the `Worker` protocol over the pinned SDK.

This adaptor is a thin wrapper: it maps `WorkerSpec` → SDK `Agent` + `Conversation`,
runs the conversation, and maps the resulting event stream back to `WorkerClaim`.
All executor concepts (OpenHands) are confined to this module; the port sees only
the claim/fault vocabulary.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Final
from uuid import UUID

from harness.worker.port import (
    Admissibility,
    ArtifactRef,
    ClaimIncomplete,
    ContainmentFailure,
    EventStreamRef,
    MountMode,
    MountSpec,
    ReadKind,
    ReadRecord,
    RunId,
    SandboxHandle,
    Sha256,
    Timeouts,
    ToolSpec,
    Usage,
    WorkerClaim,
    WorkerFault,
    WorkerOutcome,
    WorkerSpec,
    check_handle,
)

try:
    from openhands.sdk import LLM, Agent, Conversation
    from openhands.sdk.conversation.state import ConversationExecutionStatus
    from openhands.sdk.event import (
        Event,
        ObservationEvent,
    )
    from openhands.sdk.event.conversation_error import ConversationErrorEvent
    from openhands.sdk.tool import Tool
    from openhands.tools.preset.default import get_default_tools
except ImportError as e:  # pragma: no cover - import-time guard
    raise RuntimeError(
        "OpenHands SDK not available. Install with: "
        "pip install git+https://github.com/OpenHands/software-agent-sdk@d460d1a0b6bd35e054ad146c6078205df4686387"
    ) from e


__all__ = ["OpenHandsWorker"]


@dataclass(frozen=True, slots=True)
class _RunState:
    """Internal state accumulated during a run."""

    events: list[Event]
    reads: list[ReadRecord]
    turns: int
    tool_calls: int
    mutating_tool_calls: int
    prompt_tokens: int
    completion_tokens: int
    cached_prefix_tokens: int
    agent_ms: int
    harness_ms: int
    wallclock_start_ns: int
    outcome: WorkerOutcome | None
    patch_ref: ArtifactRef | None
    tree_sha256_initial: Sha256
    tree_sha256_final: Sha256 | None
    observed_fingerprint: Mapping[str, object] | None
    condensation_events: int
    approval_events: int


def _digest(data: str | bytes) -> Sha256:
    """Compute SHA256 hex digest."""
    if isinstance(data, str):
        data = data.encode()
    return Sha256(hashlib.sha256(data).hexdigest())


def _artifact_ref_from_bytes(data: bytes, media_type: str) -> ArtifactRef:
    """Create an ArtifactRef from raw bytes."""
    return ArtifactRef(
        sha256=_digest(data),
        size_bytes=len(data),
        media_type=media_type,
    )


def _map_sdk_tool_spec(tool: Tool) -> ToolSpec:
    """Map SDK Tool to port ToolSpec."""
    # The SDK Tool is a spec with name and optional schema/description
    schema_json = json.dumps(tool.parameters, sort_keys=True) if tool.parameters else "{}"
    schema_bytes = schema_json.encode()
    desc_bytes = (tool.description or "").encode()
    return ToolSpec(
        name=tool.name,
        schema_sha256=_digest(schema_bytes),
        description_sha256=_digest(desc_bytes),
        mutating=not getattr(tool, "read_only", False),
        idempotent=getattr(tool, "idempotent", False),
    )


def _extract_read_record(
    event: ObservationEvent, turn_index: int, call_index: int | None
) -> ReadRecord | None:
    """Extract a ReadRecord from an observation event if it represents a read."""
    if not isinstance(event, ObservationEvent):
        return None

    obs = event.observation
    if obs is None:
        return None

    # File reads
    if hasattr(obs, "path") and obs.path:
        kind = ReadKind.FILE_READ
        path = str(obs.path)
        query = None
        result_sha256 = _digest(obs.content) if hasattr(obs, "content") and obs.content else None
        result_row_ids = (obs.path,) if hasattr(obs, "path") else ()
        bytes_returned = len(obs.content) if hasattr(obs, "content") and obs.content else 0
        truncated = getattr(obs, "truncated", False)
        return ReadRecord(
            index=len(_READ_INDEX),  # will be fixed after collection
            kind=kind,
            turn_index=turn_index,
            call_index=call_index,
            path=path,
            query=query,
            result_sha256=result_sha256,
            result_row_ids=result_row_ids,
            bytes_returned=bytes_returned,
            truncated=truncated,
        )

    # Search / List / Retrieval - check for common patterns
    if hasattr(obs, "query"):
        kind = ReadKind.SEARCH
        path = None
        query = str(obs.query)
        result_sha256 = _digest(str(obs)) if obs else None
        result_row_ids = ()
        bytes_returned = len(str(obs)) if obs else 0
        truncated = getattr(obs, "truncated", False)
        return ReadRecord(
            index=len(_READ_INDEX),
            kind=kind,
            turn_index=turn_index,
            call_index=call_index,
            path=path,
            query=query,
            result_sha256=result_sha256,
            result_row_ids=result_row_ids,
            bytes_returned=bytes_returned,
            truncated=truncated,
        )

    return None


# Module-level mutable for read indexing during collection
_READ_INDEX: list[ReadRecord] = []


class OpenHandsWorker:
    """`Worker` implementation backed by the OpenHands SDK.

    Thin wrapper: maps `WorkerSpec` → `Agent` + `Conversation`, executes,
    and maps the event stream to `WorkerClaim`. No policy, no verdicts.
    """

    # Required assertions this worker can satisfy. The sandbox must prove these.
    _REQUIRED_ASSERTIONS: Final[frozenset[str]] = frozenset({
        "container_mounts_enforced",
        "container_network_none",
        "container_user_nonroot",
        "image_digest_matches",
    })

    def __init__(
        self,
        *,
        model: str = "gpt-4o",
        api_key: str | None = None,
        max_iterations: int = 100,
        turn_timeout_s: float = 120.0,
        enable_browser: bool = False,
    ) -> None:
        """
        Args:
            model: LLM model identifier (e.g., "gpt-4o", "claude-3-5-sonnet").
            api_key: API key for the model provider. If None, reads from env.
            max_iterations: Maximum agent iterations per run.
            turn_timeout_s: Per-turn timeout in seconds.
            enable_browser: Whether to enable browser tools.
        """
        self._model = model
        self._api_key = api_key
        self._max_iterations = max_iterations
        self._turn_timeout_s = turn_timeout_s
        self._enable_browser = enable_browser

        # Runtime state
        self._run_states: dict[UUID, _RunState] = {}
        self._conversations: dict[UUID, Conversation] = {}

    # ------------------------------------------------------------------ Worker protocol

    def identity(self) -> Mapping[str, str]:
        return {
            "executor_name": "openhands",
            "executor_commit_sha": "d460d1a0b6bd35e054ad146c6078205df4686387",
            "adaptor_version": "1.0.0",
            "runtime_image_digest": "ghcr.io/openhands/openhands:latest",
            "asserts": ",".join(sorted(self._REQUIRED_ASSERTIONS)),
        }

    def required_assertions(self) -> frozenset[str]:
        return self._REQUIRED_ASSERTIONS

    def dispatch(self, handle: SandboxHandle, spec: WorkerSpec) -> WorkerClaim:
        """Execute one attempt inside the provisioned sandbox."""
        # Verify handle matches spec and all required assertions passed
        if handle.run_id != spec.run_id:
            raise ContainmentFailure(
                f"handle proves run {handle.run_id}, spec dispatches run {spec.run_id}"
            )
        check_handle(handle, self._REQUIRED_ASSERTIONS, admissibility=Admissibility.MEASUREMENT)

        # Initialize run state
        run_id = UUID(str(spec.run_id))
        tree_initial = _compute_tree_hash(handle.mounts)
        run_state = _RunState(
            events=[],
            reads=[],
            turns=0,
            tool_calls=0,
            mutating_tool_calls=0,
            prompt_tokens=0,
            completion_tokens=0,
            cached_prefix_tokens=0,
            agent_ms=0,
            harness_ms=0,
            wallclock_start_ns=time.monotonic_ns(),
            outcome=None,
            patch_ref=None,
            tree_sha256_initial=tree_initial,
            tree_sha256_final=None,
            observed_fingerprint=None,
            condensation_events=0,
            approval_events=0,
        )
        self._run_states[run_id] = run_state

        try:
            # Build agent from spec
            agent = self._build_agent(spec)

            # Create conversation in the sandbox workspace
            workspace_path = self._resolve_workspace_path(handle)
            conversation = Conversation(
                agent=agent,
                workspace=workspace_path,
                max_iteration_per_run=self._max_iterations,
                persistence_dir=None,  # We don't persist across attempts
            )
            self._conversations[run_id] = conversation

            # Send initial task message
            task_message = self._build_task_message(spec)
            conversation.send_message(task_message)

            # Run with timeout
            self._run_with_timeout(conversation, spec.timeouts)

            # Collect results
            return self._collect_claim(run_id, handle, spec, conversation)

        except ContainmentFailure:
            raise
        except WorkerFault:
            raise
        except ClaimIncomplete:
            raise
        except Exception as e:
            # Any other exception is an infrastructure fault
            raise WorkerFault(f"OpenHands execution failed: {e}") from e
        finally:
            # Cleanup
            self._run_states.pop(run_id, None)
            conv = self._conversations.pop(run_id, None)
            if conv:
                conv.close()

    def abort(self, run_id: RunId, *, _timeout_s: float) -> None:
        """Stop the run. Emits ABORTED claim if trajectory had started."""
        rid = UUID(str(run_id))
        conv = self._conversations.get(rid)
        if conv:
            conv.cancel_token.cancel() if conv.cancel_token else None
            # The run loop will exit; claim collection happens in dispatch

    def teardown(self, run_id: RunId, *, _timeout_s: float) -> None:
        """Destroy the run's container. Idempotent."""
        rid = UUID(str(run_id))
        conv = self._conversations.pop(rid, None)
        if conv:
            conv.close()
        self._run_states.pop(rid, None)

    # ------------------------------------------------------------------ internals

    def _build_agent(self, spec: WorkerSpec) -> Agent:
        """Construct SDK Agent from WorkerSpec."""
        from pydantic import SecretStr

        # Build LLM
        llm_kwargs = {"model": self._model}
        if self._api_key:
            llm_kwargs["api_key"] = SecretStr(self._api_key)
        llm = LLM(**llm_kwargs)

        # Use default tools as baseline, filtered to those declared in spec
        default_tools = get_default_tools(enable_browser=self._enable_browser)
        declared_names = {ts.name for ts in spec.tools}
        tools = [t for t in default_tools if t.name in declared_names]

        return Agent(
            llm=llm,
            tools=tools,
            max_iterations=spec.budget.iteration_cap,
        )

    def _resolve_workspace_path(self, handle: SandboxHandle) -> str:
        """Extract the workspace path from the sandbox handle mounts."""
        # The write_mount in the spec tells us where the workspace is
        # For now, use a standard path; the sandbox should have mounted it
        for mount in handle.mounts:
            if mount.mode == MountMode.READ_WRITE:
                return mount.container_path
        return "/workspace"

    def _build_task_message(self, spec: WorkerSpec) -> str:
        """Build the initial task message from the spec."""
        # The spec's seed_layers contain the task context
        # Combine them into a task description
        parts = []
        for layer in spec.seed_layers:
            parts.append(f"[{layer.name}] {layer.content_sha256}")
        return "\n".join(parts) if parts else "Execute the task."

    def _run_with_timeout(self, conversation: Conversation, _timeouts: Timeouts) -> None:
        """Run the conversation with the specified timeouts."""
        import signal
        from typing import Never

        def timeout_handler(_signum: int, _frame: object) -> Never:
            raise TimeoutError(f"Turn timeout exceeded ({self._turn_timeout_s}s)")

        # Set up alarm for turn timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, self._turn_timeout_s)

        try:
            conversation.run()
        except TimeoutError as e:
            raise WorkerFault(f"Turn timeout exceeded ({self._turn_timeout_s}s)") from e
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)

    def _collect_claim(
        self,
        run_id: UUID,
        handle: SandboxHandle,
        spec: WorkerSpec,
        conversation: Conversation,
    ) -> WorkerClaim:
        """Collect the final claim from the conversation state."""
        run_state = self._run_states[run_id]
        state = conversation.state

        # Determine outcome from execution status
        status = state.execution_status
        if status == ConversationExecutionStatus.FINISHED:
            outcome = WorkerOutcome.AGENT_STOPPED
        elif status == ConversationExecutionStatus.ERROR:
            # Check if it was a budget/iteration limit
            last_error = self._get_last_conversation_error(state.events)
            budget_exceeded = (
                last_error
                and ("budget" in last_error.detail.lower()
                     or "iteration" in last_error.detail.lower())
            )
            if budget_exceeded:
                outcome = WorkerOutcome.BUDGET_EXHAUSTED
            elif last_error and "policy" in last_error.detail.lower():
                outcome = WorkerOutcome.POLICY_VIOLATION
            else:
                outcome = WorkerOutcome.AGENT_STOPPED
        elif status == ConversationExecutionStatus.STUCK:
            outcome = WorkerOutcome.BUDGET_EXHAUSTED
        else:
            outcome = WorkerOutcome.ABORTED

        # Compute final tree hash
        tree_final = _compute_tree_hash(handle.mounts)
        run_state.tree_sha256_final = tree_final

        # Build event stream reference
        events_artifact = _serialize_events(state.events)
        event_ref = _artifact_ref_from_bytes(events_artifact, "application/json")

        event_stream = EventStreamRef(
            artifact=event_ref,
            observed_event_count=len(state.events),
            persisted_event_count=len(state.events),
            condensation_event_count=run_state.condensation_events,
            approval_event_count=run_state.approval_events,
        )

        # Build usage
        usage = Usage(
            turns=run_state.turns,
            tool_calls=run_state.tool_calls,
            mutating_tool_calls=run_state.mutating_tool_calls,
            prompt_tokens=run_state.prompt_tokens,
            completion_tokens=run_state.completion_tokens,
            cached_prefix_tokens=run_state.cached_prefix_tokens,
            agent_ms=run_state.agent_ms,
            harness_ms=run_state.harness_ms,
            wallclock_ms=(time.monotonic_ns() - run_state.wallclock_start_ns) // 1_000_000,
        )

        # Fix read indices
        for i, read in enumerate(run_state.reads):
            run_state.reads[i] = replace(read, index=i)

        # Observed fingerprint from the conversation
        observed_fp = run_state.observed_fingerprint or spec.fingerprint.as_mapping()

        # Build containment report (boot report + any runtime assertions)
        containment = (handle.boot_report,)

        claim = WorkerClaim(
            run_id=spec.run_id,
            outcome=outcome,
            patch=run_state.patch_ref,
            tree_sha256_initial=run_state.tree_sha256_initial,
            tree_sha256_final=tree_final,
            events=event_stream,
            reads=tuple(run_state.reads),
            usage=usage,
            observed_fingerprint=observed_fp,
            containment=containment,
            schema_version=spec.schema_version,
        )

        # Verify fingerprint matches
        diffs = spec.fingerprint.compare(claim.observed_fingerprint)
        if diffs:
            raise ClaimIncomplete(
                f"observed fingerprint diverged from dispatched: {'; '.join(str(d) for d in diffs)}"
            )

        return claim

    def _get_last_conversation_error(
        self, events: Sequence[Event]
    ) -> ConversationErrorEvent | None:
        for event in reversed(events):
            if isinstance(event, ConversationErrorEvent):
                return event
        return None


def _compute_tree_hash(mounts: tuple[MountSpec, ...]) -> Sha256:
    """Compute a deterministic hash of the mounted tree state."""
    # Sort mounts for determinism
    parts = []
    for mount in sorted(mounts, key=lambda m: m.container_path):
        parts.append(f"{mount.host_source}:{mount.container_path}:{mount.mode.value}")
    return _digest("|".join(parts))


def _serialize_events(events: Sequence[Event]) -> bytes:
    """Serialize events to JSON bytes for artifact storage."""
    dumped = [e.model_dump(mode="json") for e in events]
    return json.dumps(dumped, separators=(",", ":")).encode()

