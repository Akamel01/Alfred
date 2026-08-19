"""Dataset adapters. The port is here; every adapter behind it is domain work.

`TrajectorySource` is factory — it fixes the shape a dataset must arrive in. Which
datasets, which scenarios and how each one is parsed is not decided here.
"""

from ingest.port import ScenarioRef, TrajectorySource

__all__ = ["ScenarioRef", "TrajectorySource"]
