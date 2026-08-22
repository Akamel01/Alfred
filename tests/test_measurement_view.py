"""The measurement-view partition, bound where the schema it guards lives.

`AgentTrack` declares which of its fields can change a measurement and therefore enter
`input_hash`. Both failure modes are silent in production — a field omitted from the view
changes measurements its digest never sees; a field included wrongly puts tenancy or a
wall-clock timestamp inside a digest that must be identical across two loads. This module is
the control that makes them loud instead: the partition must be total and exclusive over
`model_fields`, so adding, removing or renaming any schema field fails here until its
digest consequence has been decided on the model, next to the declaration.
"""

from __future__ import annotations

from uuid import uuid4

import numpy as np

from domain.trajectory import AgentTrack


def _track() -> AgentTrack:
    return AgentTrack(
        org_id=uuid4(),
        project_id=uuid4(),
        track_id=uuid4(),
        agent_ref="lead",
        agent_type="car",
        t=np.array([0.0, 0.1, 0.2]),
        x=np.array([0.0, 1.0, 2.0]),
        y=np.array([0.0, 0.5, 0.0]),
        length_m=4.5,
        width_m=1.8,
    )


def test_every_schema_field_is_declared_on_exactly_one_side() -> None:
    """Total and exclusive: no third state exists for any `model_fields` key."""
    fields = set(AgentTrack.model_fields)
    assert not (AgentTrack.MEASUREMENT_FIELDS & AgentTrack.EXCLUDED_FROM_MEASUREMENT)
    assert fields == AgentTrack.MEASUREMENT_FIELDS | AgentTrack.EXCLUDED_FROM_MEASUREMENT


def test_the_view_covers_exactly_the_measurement_fields() -> None:
    view = set(_track().measurement_view())
    assert view == AgentTrack.MEASUREMENT_FIELDS


def test_arrays_enter_the_view_in_full_not_by_shape() -> None:
    """A digest over shapes would collide two scenarios with equal sample counts."""
    track = _track()
    view = track.measurement_view()
    for axis in ("t", "x", "y"):
        column = view[axis]
        assert isinstance(column, list)
        assert len(column) == track.n_samples  # pyright: ignore[reportUnknownArgumentType]


def test_tenancy_identity_and_wall_clock_are_out_of_the_digest_path() -> None:
    """`created_at` defaults to `utc_now()` and ids are minted per instance: either inside
    the view and two loads of one scenario could never agree."""
    view = _track().measurement_view()
    assert view.keys().isdisjoint(AgentTrack.EXCLUDED_FROM_MEASUREMENT)


def test_two_views_of_identical_motion_are_equal() -> None:
    """The property the determinism criterion rests on, at the projection itself."""
    first, second = _track(), _track()
    assert first.measurement_view() == second.measurement_view()
