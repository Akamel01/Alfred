"""The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.

Domain-neutral throughout. It names no dataset and no measure — it runs whatever
`TrajectorySource` and `Metric` it is handed, which is what makes it factory work under the
ownership rule while every implementation behind those ports is not.

**Byte-identical determinism is the property, and the digest is how it is checked.** Two
replays of the same scenario through the same metric must produce the same
`content_sha256`; a replay of *different* inputs must not. The second half is the one that
makes the first half mean something, and it is why `input_hash` is computed from the tracks
that were actually loaded rather than from the reference that asked for them. A hash over the
`ScenarioRef` alone would be stable across a source that silently returned different data,
which is precisely the failure a determinism check exists to catch.

**Why the stamp's non-derivable fields are supplied rather than discovered.** `code_commit`,
`upstream`, `tolerance`, `assumption_set` and `metric_version` come in through
`StampContext`. The harness could reach for a `git` call or an environment variable, and
D40's argument against that is the same one S8 made about release identity: a fact read from
outside the artifact describes the reader's situation, not the artifact's. The caller knows
these; the harness does not, and guessing would produce a stamp that is confidently wrong
rather than absent.

**Nothing here is a metric.** `MetricSeries.to_value` is the single declared conversion point
(ADR-0001/ADR-0002) and this module calls it rather than reimplementing any part of it. A
degeneracy arrives as `Undefined(reason)` and is stamped like any other value; a contract
violation raises and produces no result at all.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, cast

from domain.trajectory import AgentTrack
from ingest.port import ScenarioRef, TrajectorySource
from metrics.port import Metric
from provenance.encoding import AcsValue
from provenance.stamp import ResultStampV1, StampedResult, hash_inputs
from provenance.stamp_types import AssumptionSet, Tolerance
from replay.port import ReplayResult

if TYPE_CHECKING:
    from provenance.upstream import UpstreamToolchain

__all__ = ["DeterministicReplay", "ReplayContractViolation", "StampContext"]

HARNESS_NAME: Final = "alfred.replay"
HARNESS_VERSION: Final = "1.0.0"


class ReplayContractViolation(RuntimeError):
    """The replay could not complete. No partial result is returned.

    A `ReplayResult` meaning "some of it worked" is a result nothing downstream could refuse,
    so the failure is an exception and the caller gets no number at all.
    """


@dataclass(frozen=True)
class StampContext:
    """The stamp fields the harness cannot derive from what it was handed."""

    metric_version: str
    code_commit: str
    assumption_set: AssumptionSet
    tolerance: Tolerance
    upstream: UpstreamToolchain


class DeterministicReplay:
    """A `ReplayHarness`. Structural, not nominal — the Protocol is satisfied by shape."""

    def __init__(self, context: StampContext, *, version: str = HARNESS_VERSION) -> None:
        self._context = context
        self._version = version

    def identity(self) -> Mapping[str, str]:
        # A fingerprint field, not a log line: harness identity alone moves a measurement.
        return {"name": HARNESS_NAME, "version": self._version}

    def replay(self, source: TrajectorySource, ref: ScenarioRef, metric: Metric) -> ReplayResult:
        tracks: Sequence[AgentTrack] = source.load(ref)
        if not tracks:
            # D57 at the product boundary. A metric over zero tracks returns something, and
            # that something would be stamped and stored as a measurement of a scenario
            # nobody loaded.
            raise ReplayContractViolation(
                f"{ref.dataset}/{ref.scenario_id}@{ref.revision} loaded zero tracks; "
                "a measurement over nothing is not a measurement"
            )

        series = metric.evaluate(tracks)
        if metric.arity != len(series):
            raise ReplayContractViolation(
                f"metric {metric.metric_id} declares arity {metric.arity} and returned "
                f"{len(series)} values; the declaration and the result disagree"
            )

        payload: dict[str, AcsValue] = {
            "harness": dict(self.identity()),
            "source": dict(source.identity()),
            "scenario": {
                "dataset": ref.dataset,
                "scenario_id": ref.scenario_id,
                "revision": ref.revision,
            },
            "metric_id": metric.metric_id,
            "metric_citation": dict(metric.citation()),
            # Sorted by the dataset's own identifier, not by load order: a source free to
            # return tracks in any order would otherwise produce a different digest per run
            # and fail the determinism check for a reason that is not about determinism.
            #
            # The field list lives on `AgentTrack.measurement_view` — this seam only re-types
            # it for ACS-1, so a schema change cannot silently omit itself from the digest.
            "tracks": [
                cast("dict[str, AcsValue]", t.measurement_view())
                for t in sorted(tracks, key=lambda t: t.agent_ref)
            ],
        }

        stamp = ResultStampV1(
            metric_id=metric.metric_id,
            metric_version=self._context.metric_version,
            code_commit=self._context.code_commit,
            assumption_set=self._context.assumption_set,
            input_hash=hash_inputs(payload),
            tolerance=self._context.tolerance,
            upstream=self._context.upstream,
        )
        stamped = StampedResult(value=series.to_value(0), stamp=stamp)
        return ReplayResult(stamped=stamped, content_sha256=stamped.content_hash())
