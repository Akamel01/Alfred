"""The three S5 ports as types: `TrajectorySource`, `Metric`, `ReplayHarness`.

The ports are factory and every implementation behind them is domain, so there is nothing
here to test for behaviour. What is testable is the property the ports exist for: **the
defects they are meant to make unrepresentable stay unrepresentable.** A metric returning a
bare float, a replay result naming a path instead of a hash, and a scenario reference that
cannot distinguish two revisions are each a specific past failure, and a `Protocol` that
quietly accepts them is a `Protocol` that is not doing its job.

`isinstance` against a non-runtime-checkable `Protocol` is a type error, so structural
conformance is checked the way it is actually enforced — by `pyright` over this file. The
stubs below exist to be type-checked; the assertions only keep the runtime suite honest
about them having been constructed at all.
"""

from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Mapping, Sequence

import numpy as np
import pytest

from domain.trajectory import AgentTrack
from ingest.port import ScenarioRef, TrajectorySource
from metrics.port import Metric
from metrics.series import MetricSeries
from provenance.stamp import StampedResult
from replay.port import ReplayHarness, ReplayResult

_ORG = uuid.uuid4()
_PROJECT = uuid.uuid4()


def _track(ref: str = "a") -> AgentTrack:
    return AgentTrack(
        org_id=_ORG,
        project_id=_PROJECT,
        track_id=uuid.uuid4(),
        agent_ref=ref,
        agent_type="car",
        t=np.array([0.0, 0.1, 0.2]),
        x=np.array([0.0, 1.0, 2.0]),
        y=np.array([0.0, 0.0, 0.0]),
        length_m=4.5,
        width_m=1.8,
    )


# ------------------------------------------------------------------ conforming stubs


class _Source:
    """Satisfies `TrajectorySource` structurally. Named nothing about any dataset."""

    def identity(self) -> Mapping[str, str]:
        return {"dataset": "stub", "revision": "0", "adapter_version": "0"}

    def scenarios(self) -> Sequence[ScenarioRef]:
        return (ScenarioRef("stub", "s-1", "r-1"),)

    def load(self, ref: ScenarioRef) -> Sequence[AgentTrack]:
        return (_track(ref.scenario_id),)


class _Metric:
    """Satisfies `Metric`. Returns a series, which is the whole point of the port."""

    @property
    def metric_id(self) -> str:
        return "stub"

    @property
    def arity(self) -> int:
        return 1

    def citation(self) -> Mapping[str, str]:
        return {"source": "stub", "equation": "0"}

    def evaluate(self, tracks: Sequence[AgentTrack]) -> MetricSeries:
        track = tracks[0]
        return MetricSeries(
            t=np.asarray(track.t, dtype=np.float64),
            values=np.zeros(track.n_samples, dtype=np.float64),
            reasons=np.zeros(track.n_samples, dtype=np.uint8),
        )


class _Harness:
    """Satisfies `ReplayHarness`. `replay` raises rather than fabricating a stamp: the
    port's shape is what is under test, and a stub that invented a `StampedResult` would
    be testing the stub."""

    def identity(self) -> Mapping[str, str]:
        return {"harness": "stub", "version": "0"}

    def replay(self, source: TrajectorySource, ref: ScenarioRef, metric: Metric) -> ReplayResult:
        raise NotImplementedError(
            f"{metric.metric_id} over {ref.scenario_id} from {source.identity()['dataset']}"
        )


def _export(module: object, name: str) -> object:
    """`getattr` behind a typed boundary, so the strict type gate sees `object` rather
    than a module's partially-unknown attribute type."""
    return getattr(module, name)


def _is_protocol(obj: object) -> bool:
    return getattr(obj, "_is_protocol", False) is True


def _accepts_source(source: TrajectorySource) -> Sequence[ScenarioRef]:
    return source.scenarios()


def _accepts_metric(metric: Metric) -> MetricSeries:
    return metric.evaluate((_track(),))


def _accepts_harness(harness: ReplayHarness) -> Mapping[str, str]:
    return harness.identity()


# ------------------------------------------------------------------------- the tests


def test_a_structural_implementation_satisfies_the_source_port() -> None:
    """The positive control. Without it every test below passes on an unsatisfiable port."""
    assert _accepts_source(_Source()) == (ScenarioRef("stub", "s-1", "r-1"),)


def test_a_structural_implementation_satisfies_the_metric_port() -> None:
    series = _accepts_metric(_Metric())
    assert isinstance(series, MetricSeries)


def test_the_metric_port_returns_a_series_and_not_a_number() -> None:
    """ADR-0001. A bare float has one channel for three meanings, and two of them then
    travel as `NaN` or `None` and change meaning at the first JSON boundary."""
    annotations = Metric.evaluate.__annotations__
    assert annotations["return"] is MetricSeries or annotations["return"] == "MetricSeries"


def test_the_metric_port_declares_its_arity() -> None:
    """A pairwise measure handed one track is a caller error the harness can only refuse
    if the metric says which it is."""
    assert _Metric().arity == 1
    assert "arity" in dir(Metric)


def test_a_structural_implementation_satisfies_the_replay_port() -> None:
    assert _accepts_harness(_Harness()) == {"harness": "stub", "version": "0"}


def test_a_scenario_reference_cannot_omit_its_revision() -> None:
    """A dataset publishing corrections under a stable id is the ordinary case. A
    reference that cannot tell two revisions apart cannot support a reproduction claim."""
    with pytest.raises(TypeError):
        ScenarioRef("stub", "s-1")  # pyright: ignore[reportCallIssue]


def test_a_scenario_reference_is_frozen_and_compares_by_value() -> None:
    ref = ScenarioRef("stub", "s-1", "r-1")
    assert ref == ScenarioRef("stub", "s-1", "r-1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.revision = "r-2"  # pyright: ignore[reportAttributeAccessIssue]


def test_a_replay_result_carries_a_hash_and_no_path() -> None:
    """I3. A path is a name for whatever is at it now, which is the guarantee under test."""
    names = {f.name for f in dataclasses.fields(ReplayResult)}
    assert names == {"stamped", "content_sha256"}
    assert not any("path" in name or "dir" in name for name in names)


def test_a_replay_result_holds_a_stamped_value_and_has_no_shape_for_an_unstamped_one() -> None:
    """An unstamped result is not a cheaper result; it is an unrecallable one."""
    field = {f.name: f for f in dataclasses.fields(ReplayResult)}["stamped"]
    assert field.type in (StampedResult, "StampedResult")


def test_the_ports_name_no_dataset_and_no_measure() -> None:
    """The ownership rule: the ports are factory, every implementation behind them is
    domain. A CommonRoad or TTC term in a signature here means the port is wrong."""
    import inspect

    import ingest.port
    import metrics.port
    import replay.port

    forbidden = ("commonroad", "crime", "ttc", "pet", "westhofen", "zam_urban")
    for module in (ingest.port, metrics.port, replay.port):
        # Signatures and type names only. The module docstrings cite the decisions these
        # ports come from, and citing S5's exit condition is not naming a measure in the API.
        api = [
            line
            for line in inspect.getsource(module).splitlines()
            if line.lstrip().startswith(("def ", "class "))
        ]
        assert api, f"{module.__name__}: no signatures found; this control did not run"
        assert not any(term in line.lower() for line in api for term in forbidden), module.__name__


def test_the_port_modules_carry_no_implementation() -> None:
    """Types only, per the ownership rule. A port that grew a default implementation is a
    port that decided something the domain owns."""
    import ingest.port
    import metrics.port
    import replay.port

    exported: list[tuple[str, object]] = [
        (f"{module.__name__}.{name}", _export(module, name))
        for module in (ingest.port, metrics.port, replay.port)
        for name in module.__all__
    ]
    assert exported, "no exports found; this control did not run"
    for qualified, obj in exported:
        # `hasattr` rather than `dataclasses.is_dataclass`: its TypeGuard leaves the
        # negative branch partially unknown, and the strict gate is right to say so.
        if isinstance(obj, type) and hasattr(obj, "__dataclass_fields__"):
            continue
        assert _is_protocol(obj), qualified
