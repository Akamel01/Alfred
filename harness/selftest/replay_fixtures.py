"""A synthetic source and a synthetic metric, so the replay harness can be exercised.

**Synthetic on purpose, and the precedent is S4's.** That stage's criterion is synthetic
"precisely so that a factory gate does not depend on a domain that may be written off", and
byte-identical replay is in Phase 0's narrowed exit for the same reason: the property being
checked is the harness's determinism, not any measure's correctness. A CommonRoad adapter and
a TTC implementation would test the same determinism and would also be domain content the
ownership rule assigns to the local models.

So these two are the thinnest things that satisfy the ports: a source that returns tracks it
computes from the reference, and a metric that returns a number derived from every sample it
was given. **The metric reads all of its input on purpose.** A metric returning a constant
would replay byte-identically no matter what the source did, and the determinism test would
pass against a harness that never loaded anything.

Neither of these is a measure. `separation` is a distance between two tracks with no safety
semantics, no citation to a paper, and no threshold — it exists to be a function of the input
that changes when the input changes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final
from uuid import UUID

import numpy as np

from domain.trajectory import AgentTrack
from ingest.port import ScenarioRef
from metrics.reasons import Reason
from metrics.series import MetricSeries

__all__ = ["SYNTHETIC_DATASET", "SyntheticMetric", "SyntheticSource", "synthetic_ref"]

SYNTHETIC_DATASET: Final = "alfred-synthetic"

# Fixed ids so two runs produce identical fixtures. A random UUID per run would move nothing
# in the digest -- track_id, org_id and project_id are deliberately absent from the input hash,
# because tenancy is not a property of the measurement -- but it would make a failing test's
# output impossible to compare across runs. Distinct per track: AgentTrack ids must be.
_ORG: Final = UUID("00000000-0000-4000-8000-00000000000a")
_PROJECT: Final = UUID("00000000-0000-4000-8000-00000000000b")
_LEAD: Final = UUID("00000000-0000-4000-8000-000000000001")
_FOLLOW: Final = UUID("00000000-0000-4000-8000-000000000002")


def synthetic_ref(scenario_id: str = "straight-pair", revision: str = "1") -> ScenarioRef:
    return ScenarioRef(dataset=SYNTHETIC_DATASET, scenario_id=scenario_id, revision=revision)


class SyntheticSource:
    """A `TrajectorySource` over generated tracks. Names no dataset that exists."""

    def __init__(self, *, samples: int = 8, offset_m: float = 3.0) -> None:
        self._samples = samples
        self._offset_m = offset_m

    def identity(self) -> Mapping[str, str]:
        # Both parameters are in the identity because both change the tracks. An identity
        # that did not vary with them would let two different sources stamp the same
        # provenance, which is the ambiguity the stamp exists to remove.
        return {
            "name": "alfred.selftest.synthetic",
            "version": "1.0.0",
            "samples": str(self._samples),
            "offset_m": repr(self._offset_m),
        }

    def scenarios(self) -> Sequence[ScenarioRef]:
        return (synthetic_ref(),)

    def load(self, ref: ScenarioRef) -> Sequence[AgentTrack]:
        if ref.dataset != SYNTHETIC_DATASET:
            raise KeyError(f"{ref.dataset!r} is not {SYNTHETIC_DATASET!r}")
        t = np.arange(self._samples, dtype=np.float64)
        return (
            AgentTrack(
                org_id=_ORG,
                project_id=_PROJECT,
                track_id=_LEAD,
                agent_ref="lead",
                agent_type="car",
                t=t,
                x=t * 2.0,
                y=np.zeros_like(t),
                length_m=4.5,
                width_m=1.8,
            ),
            AgentTrack(
                org_id=_ORG,
                project_id=_PROJECT,
                track_id=_FOLLOW,
                agent_ref="follow",
                agent_type="car",
                t=t,
                x=t * 2.0 - self._offset_m,
                y=np.zeros_like(t),
                length_m=4.5,
                width_m=1.8,
            ),
        )


class SyntheticMetric:
    """A `Metric` returning the minimum planar separation between the first two tracks.

    Not a safety measure and not presented as one. It reads every sample of both tracks, which
    is the only property this fixture needs: a value that moves when the input moves.
    """

    metric_id: Final = "alfred.selftest.separation"
    arity: Final = 1

    def citation(self) -> Mapping[str, str]:
        return {
            "source": "none",
            "note": "synthetic harness fixture; no formula in the literature is being implemented",
        }

    def evaluate(self, tracks: Sequence[AgentTrack]) -> MetricSeries:
        t = np.zeros(1, dtype=np.float64)
        if len(tracks) < 2:
            # A degeneracy, not a fault: the input is well formed and the quantity is not
            # defined over it. E24's code exactly. Undefined travels as a value; a fault
            # would raise and produce no result at all.
            return MetricSeries.all_undefined(t, Reason.NO_COUNTERPART)
        first, second = tracks[0], tracks[1]
        separation = float(
            np.min(np.hypot(first.x.astype(np.float64) - second.x, first.y.astype(np.float64) - second.y))
        )
        return MetricSeries.all_defined(t, np.array([separation], dtype=np.float64))
