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

# The committed side of the normalization cross-check. Lives in the build context because
# the Dockerfile COPYs it into the image; one file, so the two sides cannot drift apart by
# somebody updating a copy.
VECTORS_PATH = Path(__file__).resolve().parent / "normalization_vectors.json"


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


def build_image(*, tag: str = IMAGE_TAG) -> str:
    """Build the oracle image under the tag the rest of this module expects.

    A helper rather than a documented command line, because the two were briefly out of
    step: the image was built under a hand-typed tag one character longer than
    `IMAGE_TAG`, so `image_exists` returned False and the integration test *skipped*
    rather than failed. A skip is the quietest possible way for a check to stop running,
    and the tag had two sources of truth. Now it has one.
    """
    subprocess.run(
        [
            "docker", "build",
            "--platform", PLATFORM,
            "-t", tag,
            str(Path(__file__).resolve().parent),
        ],
        check=True,
    )
    return tag


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


def run_fingerprints(*, tag: str = IMAGE_TAG, out_dir: Path | None = None) -> dict[str, Any]:
    """Run the fingerprint emitter and refuse a run whose normalization disagrees with ours.

    Same posture as `run_oracle`, with the entrypoint overridden: the image's default path
    stays the extractor, so nothing here gives the image a second way to be invoked by
    accident. What differs is the check afterwards.

    **The cross-check is the reason this is a function and not a documented command.** The
    normalization C15 clause 3 compares against exists twice — inside the image, because D54
    forbids the oracle's source crossing the boundary, and in `patch_side.py`, because that is
    where the diff is. If they drift, every digest in the register is a digest of something
    else, clause 3 matches nothing, and the result is indistinguishable from a clean patch.
    So the emitter answers the committed vectors in its own output and this refuses the run on
    any disagreement, rather than writing a register nobody could trust.
    """
    if not image_exists(tag):
        raise OracleRunFailed(f"oracle image {tag} is not built; see build_image()")

    with tempfile.TemporaryDirectory(prefix="alfred-fingerprints-") as tmp:
        out = Path(out_dir) if out_dir else Path(tmp)
        out.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                "docker", "run", "--rm",
                "--platform", PLATFORM,
                "--network", "none",
                "--read-only",
                "--user", "10001",
                "--tmpfs", "/tmp:rw,size=256m",
                "--volume", f"{out}:/out",
                "--entrypoint", "python",
                tag,
                "/oracle/fingerprints.py",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        report_path = out / "oracle_fingerprints.json"
        if not report_path.exists():
            raise OracleRunFailed(
                f"no fingerprint report was produced. exit={proc.returncode} "
                f"stderr={proc.stderr[-2000:]}"
            )
        report: dict[str, Any] = json.loads(report_path.read_text())

    if report.get("findings"):
        raise OracleRunFailed(f"the emitter reported findings: {report['findings']}")

    observed = report.get("oracle_commit_sha")
    if observed != ORACLE_COMMIT_SHA:
        raise OracleRunFailed(f"image reports oracle commit {observed}, pins say {ORACLE_COMMIT_SHA}")

    committed = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]
    expected = {vector["name"]: vector["normalized_sha256"] for vector in committed}
    answered = {v["name"]: v["normalized_sha256"] for v in report.get("normalization_vectors", [])}
    if not answered:
        # D57. Zero vectors answered is not agreement; it is a cross-check that did not run.
        raise OracleRunFailed("the emitter answered no normalization vectors")
    disagreements = sorted(name for name, digest in expected.items() if answered.get(name) != digest)
    if disagreements:
        raise OracleRunFailed(
            f"the in-image normalization disagrees with patch_side.py on {disagreements}; "
            "every digest this run produced would be a digest of something else"
        )

    return report
