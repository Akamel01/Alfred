"""The `ReplayHarness` port — determinism stated as a hash, not as an intention.

One of the three S5 ports, and the one that carries S5's exit condition: CriMe's asserted
values reproduced on the six named scenarios within a documented tolerance. A reproduction
claim rests on the run being repeatable, so "deterministic" has to be a property something
can check rather than a property the harness asserts about itself.

**So a replay returns a content hash, and never a path.** Two replays of the same scenario,
metric and source revision must produce equal `content_sha256`. A path is a name for
whatever is at it now, which is exactly the guarantee under test (I3, and the same rule the
`Worker` port's `ArtifactRef` states). The hash is over the `StampedResult`, so the stamp's
own inputs — the tolerance, the assumption set, the upstream provenance — are inside the
thing being compared rather than beside it.

**A result leaves this port stamped or not at all.** An unstamped result is not a cheaper
result; it is an unrecallable one, and the port has no shape for it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from ingest.port import ScenarioRef, TrajectorySource
from metrics.port import Metric
from provenance.stamp import StampedResult

__all__ = ["ReplayHarness", "ReplayResult"]


@dataclass(frozen=True)
class ReplayResult:
    """One replayed measurement, and the digest two runs are compared on.

    `content_sha256` is `stamped.content_hash()` at construction time rather than a second
    independent hash: a digest computed by a different path is a digest that can disagree
    with the one the evidence chain stores, and then neither is authoritative.
    """

    stamped: StampedResult
    content_sha256: str


class ReplayHarness(Protocol):
    """Runs one metric over one scenario, reproducibly."""

    def identity(self) -> Mapping[str, str]:
        """Harness name and version, for the fingerprint. Harness identity alone moves a
        measurement, which is why it is a fingerprint field rather than a log line."""
        ...

    def replay(
        self,
        source: TrajectorySource,
        ref: ScenarioRef,
        metric: Metric,
    ) -> ReplayResult:
        """Load, evaluate, stamp.

        Raises rather than returning a partial result: a replay that could not complete has
        produced no measurement, and a `ReplayResult` that means "some of it worked" would
        be a result nothing downstream could refuse.
        """
        ...
