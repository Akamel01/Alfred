"""Build, deploy, roll back. Through `docker compose`, because that is the claim.

Phase 0's exit criterion is "`docker compose up` serves the API; deploy and rollback both
execute and are verified". So the driver goes through compose rather than around it: a
mechanism verified on a path the operator does not use has verified a different mechanism.

The image tag is selected by an environment variable the compose service reads, so a
deploy is "point compose at this release and bring it up" and a rollback is the same
operation aimed at an earlier one. Nothing is mutated in place, which is what makes the
two operations the same code with different targets — and a rollback that ran different
code from a deploy would be a path exercised for the first time during an incident.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from harness.deploy.ledger import Entry, Ledger

REPO_ROOT: Final = Path(__file__).resolve().parent.parent.parent
IMAGE_REPO: Final = "alfred-api"
SERVICE: Final = "api"
DEFAULT_PORT: Final = 58080
# Long enough for a cold container start, short enough that a hung service is a failure
# rather than a stall. Timeouts are set from observed starts, never from a round number
# that happens to be a default.
READY_TIMEOUT_S: Final = 60.0


class DeployError(RuntimeError):
    """A deploy or rollback did not complete. Nothing is recorded."""


@dataclass(frozen=True)
class Release:
    release_id: str
    image_ref: str
    source_digest: str


def _run(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args, capture_output=True, text=True, check=False, cwd=REPO_ROOT, env=env
    )
    if proc.returncode != 0:
        raise DeployError(f"{' '.join(args[:3])} failed ({proc.returncode}): {proc.stderr[-1500:]}")
    return proc


def _compose_env(image_ref: str, port: int) -> dict[str, str]:
    env = dict(os.environ)
    env["ALFRED_API_IMAGE"] = image_ref
    env["ALFRED_API_PORT"] = str(port)
    return env


def source_digest() -> str:
    """Content address of what is being released.

    `git rev-parse HEAD` is deliberately not used on its own: a dirty tree releases bytes
    no commit describes, and a release identified by a commit it does not match is the
    provenance defect D27 exists to prevent, occurring in the deploy path.
    """
    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    dirty = _run(["git", "status", "--porcelain"]).stdout.strip()
    return f"{head}{'+dirty' if dirty else ''}"


def build_release(release_id: str, *, digest: str | None = None) -> Release:
    image_ref = f"{IMAGE_REPO}:{release_id}"
    resolved = digest if digest is not None else source_digest()
    _run(
        [
            "docker", "build",
            "-f", "deploy/api.Dockerfile",
            "-t", image_ref,
            "--build-arg", f"ALFRED_RELEASE_ID={release_id}",
            "--build-arg", f"ALFRED_RELEASE_DIGEST={resolved}",
            ".",
        ]
    )
    return Release(release_id=release_id, image_ref=image_ref, source_digest=resolved)


def served_identity(*, port: int = DEFAULT_PORT, timeout_s: float = 5.0) -> dict[str, Any]:
    """What is answering right now. The only source of truth about what is deployed.

    Asked over HTTP rather than of `docker ps`, because "the container with the new tag is
    running" and "the new code is serving" are different claims, and the gap between them
    is where a failed rollback lives.
    """
    url = f"http://127.0.0.1:{port}/version"
    with urllib.request.urlopen(url, timeout=timeout_s) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise DeployError(f"/version returned {type(payload).__name__}, not an object")
    return payload


def _wait_until_serving(*, port: int, timeout_s: float = READY_TIMEOUT_S) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    last: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return served_identity(port=port)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last = exc
            time.sleep(0.5)
    raise DeployError(f"service did not serve /version within {timeout_s}s: {last}")


def _bring_up(image_ref: str, port: int) -> dict[str, Any]:
    env = _compose_env(image_ref, port)
    _run(["docker", "compose", "up", "-d", "--force-recreate", SERVICE], env=env)
    return _wait_until_serving(port=port)


def take_down(*, port: int = DEFAULT_PORT) -> None:
    env = _compose_env(f"{IMAGE_REPO}:none", port)
    subprocess.run(
        ["docker", "compose", "rm", "-sf", SERVICE],
        capture_output=True, text=True, check=False, cwd=REPO_ROOT, env=env,
    )


def deploy(release: Release, ledger: Ledger, *, port: int = DEFAULT_PORT, now: float) -> dict[str, Any]:
    """Bring the release up, confirm it is the one answering, and only then record it.

    Order matters: the ledger is written *after* the service is observed serving the
    intended release. Recording first would leave a history claiming a deploy that never
    took, and the rollback target is chosen from that history.
    """
    observed = _bring_up(release.image_ref, port)
    if observed.get("release_id") != release.release_id:
        raise DeployError(
            f"deployed {release.release_id!r} but {observed.get('release_id')!r} is serving; "
            "nothing recorded"
        )
    ledger.append(
        Entry(
            release_id=release.release_id,
            image_ref=release.image_ref,
            source_digest=release.source_digest,
            action="deploy",
            at=now,
        )
    )
    return observed


def rollback(ledger: Ledger, *, port: int = DEFAULT_PORT, now: float) -> dict[str, Any]:
    """Return to the last release that is not the one serving. Same code path as deploy."""
    target = ledger.rollback_target()
    observed = _bring_up(target.image_ref, port)
    if observed.get("release_id") != target.release_id:
        raise DeployError(
            f"rolled back to {target.release_id!r} but {observed.get('release_id')!r} is "
            "serving; nothing recorded"
        )
    ledger.append(
        Entry(
            release_id=target.release_id,
            image_ref=target.image_ref,
            source_digest=target.source_digest,
            action="rollback",
            at=now,
        )
    )
    return observed
