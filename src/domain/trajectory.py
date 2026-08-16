"""Trajectory schemas — the load-bearing abstraction everything downstream reads.

One `AgentTrack` per observed road user, stored as parallel arrays over a shared
timebase. The array layout is not an optimization detail: it is the shape ADR-0001
requires metrics to compute in, and a per-sample object schema here would force
every metric to convert before it could do arithmetic.

Contract violations raise (E20 unsorted or duplicate timestamps, E25 self-pairing,
mismatched lengths). Degeneracies do not: a zero-length track, a single-sample
track and a lone agent are all legal inputs, answered downstream with an explicit
`Undefined(reason)`.
"""

from __future__ import annotations

from typing import Self
from uuid import UUID

import numpy as np
from pydantic import Field, model_validator

from domain.arrays import FiniteFloat64Array
from domain.base import Tenanted
from domain.errors import LengthMismatch, SelfPairing, UnsortedTimestamps

__all__ = ["AgentTrack", "ObservedWindow", "check_distinct"]


class ObservedWindow(Tenanted):
    """The interval a track was actually observed over.

    E21/E22 make this part of the result rather than an implementation detail:
    an agent appearing or disappearing mid-scenario is evaluated only over its
    observed window, and absence is never read as a stationary agent parked at
    the last known position.
    """

    t_start: float
    t_end: float
    n_samples: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.t_end < self.t_start:
            raise ValueError(f"observed window ends before it starts: {self}")
        return self


class AgentTrack(Tenanted):
    """One road user's observed motion, in a local metric frame.

    Coordinates are metres in a scenario-local east/north frame and `t` is
    seconds. E29 is the reason the frame is local: differencing UTM-scale
    coordinates to resolve sub-metre separations loses precision silently, so the
    translation to a local origin happens at ingest, not inside a metric.
    """

    track_id: UUID
    agent_ref: str = Field(min_length=1, description="Stable identifier in the source dataset.")
    agent_type: str = Field(min_length=1, description="Dataset-declared class: car, pedestrian, …")

    t: FiniteFloat64Array
    x: FiniteFloat64Array
    y: FiniteFloat64Array

    length_m: float = Field(gt=0.0, description="Bounding-box extent along the heading.")
    width_m: float = Field(gt=0.0, description="Bounding-box extent across the heading.")

    @model_validator(mode="after")
    def _check_contract(self) -> Self:
        n = self.t.size
        if self.x.size != n or self.y.size != n:
            raise LengthMismatch(
                f"track {self.agent_ref}: t/x/y lengths differ "
                f"({n}, {self.x.size}, {self.y.size})"
            )
        if n > 1 and not bool(np.all(np.diff(self.t) > 0.0)):
            # E20. Duplicate timestamps fail the same check as unsorted ones,
            # which is intended: both make "the sample at time t" ambiguous.
            raise UnsortedTimestamps(
                f"track {self.agent_ref}: timestamps are not strictly increasing"
            )
        return self

    @property
    def n_samples(self) -> int:
        return int(self.t.size)

    def observed_window(self) -> ObservedWindow:
        """The window this track covers. Empty tracks report a zero-width window
        at t=0 with `n_samples=0`; the count, not the width, is what a caller
        must branch on."""
        if self.n_samples == 0:
            t_start = t_end = 0.0
        else:
            t_start, t_end = float(self.t[0]), float(self.t[-1])
        return ObservedWindow(
            org_id=self.org_id,
            project_id=self.project_id,
            caused_by=self.track_id,
            t_start=t_start,
            t_end=t_end,
            n_samples=self.n_samples,
        )


def check_distinct(a: AgentTrack, b: AgentTrack) -> None:
    """Refuse a pairwise evaluation of a track against itself (E25).

    A self-pair is a caller bug, and it is worth catching explicitly because the
    formulas do not fail on it — relative velocity and gap are both identically
    zero, so the metric returns a confident `0.0` meaning "collision".
    """
    if a.track_id == b.track_id:
        raise SelfPairing(f"track {a.agent_ref} paired against itself")
