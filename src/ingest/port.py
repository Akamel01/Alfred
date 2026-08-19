"""The `TrajectorySource` port — how observed motion enters the system, and in what frame.

One of the three S5 ports. The ports are factory; every implementation behind them is
domain, so this module names no dataset. A CommonRoad-specific term in a signature here
means the port is wrong.

Two rules generate the shape:

1. **The adapter converts; the system never does.** A source returns `AgentTrack`, which
   is already metres in a scenario-local east/north frame with a strictly increasing
   timebase. Translating to a local origin at ingest is E29: differencing UTM-scale
   coordinates to resolve sub-metre separations loses precision silently, and a metric that
   received global coordinates would produce a wrong number rather than an error.
2. **Enumeration is separate from loading.** `scenarios()` is cheap and total; `load()` is
   neither. A source that could only answer "here is everything" would make a run's scope
   a function of how much memory it had, and the scenario set is a fingerprint input.

`identity()` exists for the same reason the `Worker` port has one: the dataset and its
revision are part of what a measurement was taken on. A reproduced number against an
unnamed dataset revision is not reproduced.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from domain.trajectory import AgentTrack

__all__ = ["ScenarioRef", "TrajectorySource"]


@dataclass(frozen=True)
class ScenarioRef:
    """One scenario, named so that two runs can be shown to have used the same bytes.

    `revision` is not optional and has no default. A dataset that publishes corrections
    under a stable id is the ordinary case, not the exotic one, and a reference that cannot
    distinguish two revisions cannot support a reproduction claim.
    """

    dataset: str
    scenario_id: str
    revision: str


class TrajectorySource(Protocol):
    """A source of observed motion. Stateless between calls; holds no run state."""

    def identity(self) -> Mapping[str, str]:
        """Dataset name, revision and adapter version, for the fingerprint. Recorded."""
        ...

    def scenarios(self) -> Sequence[ScenarioRef]:
        """Every scenario this source can load. Enumerated, never inferred by the caller."""
        ...

    def load(self, ref: ScenarioRef) -> Sequence[AgentTrack]:
        """The tracks for one scenario, already in the local metric frame.

        Raises rather than returning an empty sequence when the scenario is unknown: a
        scenario that legitimately holds zero tracks and one that failed to load are
        different facts, and only the first is a result.
        """
        ...
