"""Alfred OpenHands Adaptor — the Worker implementation for the OpenHands executor.

This module implements the `Worker` protocol from `harness.worker.port`.
It runs inside the sandbox container, connects to the harness via the
dispatch mount, executes the agent, and returns a `WorkerClaim`.

The adaptor is stateless between attempts. Nothing survives a claim except
what the claim references by content hash.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from harness.worker.port import (
    Worker,
    WorkerSpec,
    WorkerClaim,
    WorkerOutcome,
    SandboxHandle,
    ArtifactRef,
    ReadRecord,
    ReadKind,
    EventStreamRef,
    Usage,
    Sha256,
    RunId,
    TaskId,
    AttemptId,
    ContainmentFailure,
    WorkerFault,
    ClaimIncomplete,
    AssertionReport,
    AssertionResult,
    AssertionOutcome,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("alfred.adaptor")


@dataclass
class AdaptorIdentity:
    """Identity information for the fingerprint."""

    executor_name: str = "OpenHands"
    executor_commit_sha: str = os.environ.get("EXECUTOR_COMMIT_SHA", "unknown")
    adaptor_version: str = "0.1.0"
    runtime_image_digest: str = os.environ.get("RUNTIME_IMAGE_DIGEST", "unknown")
    oracle_denylist_version: str = os.environ.get("ORACLE_DENYLIST_VERSION", "unknown")


class OpenHandsAdaptor(Worker):
    """Worker implementation for the OpenHands software agent executor."""

    def __init__(self) -> None:
        self._identity = AdaptorIdentity()
        self._current_run_id: RunId | None = None
        self._container_id: str | None = None

    def identity(self) -> Mapping[str, str]:
        """Adaptor identity for the fingerprint."""
        return {
            "executor_name": self._identity.executor_name,
            "executor_commit_sha": self._identity.executor_commit_sha,
            "adaptor_version": self._identity.adaptor_version,
            "runtime_image_digest": self._identity.runtime_image_digest,
            "oracle_denylist_version": self._identity.oracle_denylist_version,
        }

    def required_assertions(self) -> frozenset[str]:
        """The containment assertions this adaptor can make.

        Must be a superset of the mandatory set from the Sandbox Specification.
        """
        return frozenset({
            "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8",
            "C9", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17",
        })

    def dispatch(self, handle: SandboxHandle, spec: WorkerSpec) -> WorkerClaim:
        """Execute one attempt inside the provisioned sandbox.

        This is the main entry point. It:
        1. Validates the handle against required assertions
        2. Sets up the executor with the spec
        3. Runs the agent loop
        4. Collects the claim
        5. Returns the WorkerClaim

        Raises:
            ContainmentFailure: If a required assertion is absent or not passed.
            WorkerFault: If the executor could not be shown to have run.
            ClaimIncomplete: If a claim exists but cannot be trusted.
        """
        from harness.worker.port import check_handle

        # Structural refusal: verify the handle's boot report
        check_handle(handle, self.required_assertions())

        self._current_run_id = spec.run_id
        logger.info(f"Starting attempt {spec.attempt_id} for run {spec.run_id}")

        try:
            # Run the agent and collect the claim
            claim = asyncio.run(self._run_agent(handle, spec))
            return claim
        except ContainmentFailure:
            raise
        except WorkerFault:
            raise
        except ClaimIncomplete:
            raise
        except Exception as exc:
            # Any other exception is a WorkerFault — the executor could not
            # be shown to have run the attempt it was given
            logger.exception("Executor fault during dispatch")
            raise WorkerFault(f"Executor fault: {exc}") from exc

    async def _run_agent(self, handle: SandboxHandle, spec: WorkerSpec) -> WorkerClaim:
        """Run the OpenHands agent and collect the claim."""
        # This is a stub implementation. The real implementation would:
        # 1. Start the OpenHands agent server (FastAPI + WebSocket)
        # 2. Connect to it via the SDK
        # 3. Feed it the task from the dispatch mount
        # 4. Stream events and record reads
        # 5. Collect the patch output
        # 6. Build the WorkerClaim

        # For now, return a minimal valid claim indicating the agent stopped
        # without making changes (patch = None)
        return self._build_minimal_claim(spec)

    def _build_minimal_claim(self, spec: WorkerSpec) -> WorkerClaim:
        """Build a minimal valid claim for testing."""
        # Compute tree hashes
        initial_hash = self._compute_tree_hash(Path("/repo"))
        final_hash = initial_hash  # No changes in minimal claim

        return WorkerClaim(
            run_id=spec.run_id,
            outcome=WorkerOutcome.AGENT_STOPPED,
            patch=None,
            tree_sha256_initial=Sha256(initial_hash),
            tree_sha256_final=Sha256(final_hash),
            events=EventStreamRef(
                artifact=ArtifactRef(
                    sha256=Sha256("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
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
            observed_fingerprint={},
            containment=(handle.boot_report,),
            schema_version=spec.schema_version,
        )

    def _compute_tree_hash(self, path: Path) -> str:
        """Compute SHA256 of a directory tree."""
        hasher = hashlib.sha256()
        for root, dirs, files in sorted(os.walk(path)):
            dirs.sort()
            for file in sorted(files):
                filepath = Path(root) / file
                rel_path = filepath.relative_to(path)
                hasher.update(str(rel_path).encode())
                hasher.update(b"\0")
                try:
                    hasher.update(filepath.read_bytes())
                except OSError:
                    pass
                hasher.update(b"\0")
        return hasher.hexdigest()

    def abort(self, run_id: RunId, *, timeout_s: float) -> None:
        """Abort a running attempt. Idempotent."""
        logger.info(f"Aborting run {run_id} with timeout {timeout_s}s")
        # In a real implementation, this would signal the agent process
        # and wait for it to stop, then return a claim with ABORTED outcome.
        # For now, this is a no-op that would be called by the harness.

    def teardown(self, run_id: RunId, *, timeout_s: float) -> None:
        """Destroy the container. Idempotent."""
        logger.info(f"Tearing down run {run_id} with timeout {timeout_s}s")
        # The container is removed by the harness via cleanup_sandbox.
        # This method exists for the protocol but the actual teardown
        # happens outside the container.


def main() -> None:
    """Main entrypoint when run as a script (for testing)."""
    import argparse

    parser = argparse.ArgumentParser(description="Alfred OpenHands Adaptor")
    parser.add_argument("--dispatch", type=Path, required=True, help="Path to dispatch mount")
    parser.add_argument("--patch", type=Path, required=True, help="Path to patch output mount")
    parser.add_argument("--repo", type=Path, required=True, help="Path to repo mount")
    parser.add_argument("--cache", type=Path, required=True, help="Path to cache mount")
    args = parser.parse_args()

    # This would be called by the harness, not directly.
    # The real flow: harness calls provision_sandbox -> gets handle ->
    # calls adaptor.dispatch(handle, spec) -> gets claim.
    logger.info("Adaptor started (direct invocation for testing)")
    logger.info(f"Mounts: dispatch={args.dispatch}, patch={args.patch}, repo={args.repo}, cache={args.cache}")


if __name__ == "__main__":
    main()