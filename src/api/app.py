"""Health and identity. The identity is the load-bearing half.

------------------------------------------------------ why the version comes from the image

`/version` reports what the *running artifact* is, read from the environment baked in at
image build time. It does not read the repository, a mounted file, or a git command.

That is the whole reason rollback is falsifiable. If the served identity were read from
anything outside the image, a rollback would report the old release while the new code
kept serving, and the verification would agree with it. The check would pass in exactly
the situation it exists to detect. So the identity travels *inside* the artifact, and a
container that cannot state which release it is refuses to start.
"""

from __future__ import annotations

import os
from typing import Final

from fastapi import FastAPI
from pydantic import BaseModel

# Set by the Dockerfile from a build argument. No default: a service that cannot say which
# release it is has nothing useful to report to a rollback verifier, and a default would
# make every unstamped image indistinguishable from every other.
RELEASE_ENV_VAR: Final = "ALFRED_RELEASE_ID"
DIGEST_ENV_VAR: Final = "ALFRED_RELEASE_DIGEST"


class BuildIdentity(BaseModel):
    """What this artifact is. Frozen at build time, never derived at request time."""

    release_id: str
    source_digest: str


class Health(BaseModel):
    status: str
    release_id: str


def build_identity() -> BuildIdentity:
    release_id = os.environ.get(RELEASE_ENV_VAR)
    source_digest = os.environ.get(DIGEST_ENV_VAR)
    if not release_id or not source_digest:
        raise RuntimeError(
            f"{RELEASE_ENV_VAR} and {DIGEST_ENV_VAR} must be baked into the image. "
            "An artifact that cannot state which release it is makes rollback unverifiable: "
            "the verifier would have nothing to compare and would report success either way."
        )
    return BuildIdentity(release_id=release_id, source_digest=source_digest)


app = FastAPI(title="Alfred", version="0.0.0")


@app.get("/health")
def health() -> Health:
    # Deliberately more than a 200: a healthcheck that cannot distinguish two releases
    # reports "up" across a failed rollback, which is the one moment it is consulted.
    return Health(status="ok", release_id=build_identity().release_id)


@app.get("/version")
def version() -> BuildIdentity:
    return build_identity()
