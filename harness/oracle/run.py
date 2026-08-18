"""Runs the oracle image. Outside the container, and it never imports the oracle.

D54's split is that the oracle's outputs cross the boundary as data and its code never
crosses at all. This module is where that is enforced rather than assumed: it starts a
container, reads a JSON file, and holds no import path to anything CriMe installs.

The run posture is the interesting part, and every element of it answers a specific hole
in D50's closure list:

  --network none        acquisition during the run. The image was built with network; the
                        run has none, so the oracle cannot fetch and nothing can leave.
  --read-only           a run that can write into its own site-packages can install the
                        thing the next run asserts is absent.
  no repo mount         the container sees no Alfred source at all. Agent-authored code
                        does not execute here, and the way to guarantee that is to make it
                        unreachable rather than to promise not to run it.
  --user 10001          non-root, matching the image's own user.
  no environment        no credential is passed, so a compromised oracle has none to leak.

The one writable path is the output directory, and it is a fresh host directory per run.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.oracle.pins import IMAGE_TAG, ORACLE_COMMIT_SHA, PLATFORM


class OracleRunFailed(RuntimeError):
    """The oracle did not produce a usable extract. Nothing is loaded."""


@dataclass(frozen=True)
class OracleRun:
    report: dict[str, Any]
    exit_code: int
    image_id: str

    @property
    def findings(self) -> list[str]:
        return list(self.report.get("findings", []))


def image_exists(tag: str = IMAGE_TAG) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", tag], capture_output=True, text=True, check=False
    )
    return result.returncode == 0


def _image_id(tag: str) -> str:
    return subprocess.run(
        ["docker", "image", "inspect", tag, "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def run_oracle(*, tag: str = IMAGE_TAG, out_dir: Path | None = None) -> OracleRun:
    if not image_exists(tag):
        raise OracleRunFailed(
            f"oracle image {tag} is not built. Build it from harness/oracle/Dockerfile; "
            "it is not built on demand because a build silently pulling a different "
            "resolved dependency set is exactly what the pin exists to prevent."
        )

    with tempfile.TemporaryDirectory(prefix="alfred-oracle-") as tmp:
        out = Path(out_dir) if out_dir else Path(tmp)
        out.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                "docker", "run", "--rm",
                "--platform", PLATFORM,
                "--network", "none",
                "--read-only",
                "--user", "10001",
                # CriMe writes plots and logs; a small tmpfs keeps --read-only workable
                # without giving the run a durable writable path. /home/oracle is
                # deliberately NOT a tmpfs: it holds the pyximport build cache warmed
                # at image build time, and a tmpfs would shadow it and send the run
                # back to compiling on every invocation.
                "--tmpfs", "/tmp:rw,size=256m",
                "--volume", f"{out}:/out",
                tag,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        report_path = out / "oracle_extract.json"
        if not report_path.exists():
            raise OracleRunFailed(
                "the oracle produced no extract file. "
                f"exit={proc.returncode} stderr={proc.stderr[-2000:]}"
            )
        report = json.loads(report_path.read_text())

    # The image is asked what it is, rather than told. A tag can be moved; the recorded
    # SHA comes from `git rev-parse` inside the container.
    observed = report.get("environment", {}).get("oracle_commit_sha")
    if observed != ORACLE_COMMIT_SHA:
        raise OracleRunFailed(
            f"image reports oracle commit {observed}, pins say {ORACLE_COMMIT_SHA}"
        )

    return OracleRun(report=report, exit_code=proc.returncode, image_id=_image_id(tag))
