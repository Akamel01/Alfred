"""Byte-identical deterministic replay, and the control that stops it being trivial.

**P0-5 of the narrowed Phase 0 exit** (ADR-0022). The criterion is the harness's determinism,
not any measure's correctness, so the source and the metric are synthetic — the same argument
S4 makes for its criterion: a factory gate must not depend on a domain that may be written off.

**How this suite would be shown vacuous** (D57). Every test here would pass against a harness
that returned a constant digest. `test_a_changed_input_moves_the_digest` is what makes the
determinism tests mean something, and it is parametrized over each thing that should move the
hash so that a hash over a subset of the inputs fails at least one case. A determinism test
that never watches the digest change is a test that a constant would satisfy.
"""

from __future__ import annotations

import pytest

from harness.selftest.replay_fixtures import (
    SYNTHETIC_DATASET,
    SyntheticMetric,
    SyntheticSource,
    synthetic_ref,
)
from provenance.stamp_types import AssumptionSet, Tolerance
from provenance.upstream import CorpusUpstream
from replay.harness import DeterministicReplay, ReplayContractViolation, StampContext
from replay.port import ReplayResult

_COMMIT = "0" * 40


def _context(*, metric_version: str = "1.0.0", atol: float = 1e-9) -> StampContext:
    return StampContext(
        metric_version=metric_version,
        code_commit=_COMMIT,
        assumption_set=AssumptionSet(name="selftest", version="1", entries={}),
        tolerance=Tolerance(atol=atol, rtol=0.0),
        upstream=CorpusUpstream(
            corpus_name=SYNTHETIC_DATASET,
            corpus_version="1",
            scenario_id="straight-pair",
            corpus_digest="0" * 64,
        ),
    )


def _replay(*, source: SyntheticSource | None = None, **context: object) -> ReplayResult:
    harness = DeterministicReplay(_context(**context))  # pyright: ignore[reportArgumentType]
    return harness.replay(source or SyntheticSource(), synthetic_ref(), SyntheticMetric())


def test_two_replays_of_the_same_inputs_are_byte_identical() -> None:
    """The criterion itself. Separate harness instances, so no state is being reused."""
    assert _replay().content_sha256 == _replay().content_sha256


def test_the_digest_is_the_stamped_records_own_hash() -> None:
    """Not a second independent hash (I3).

    A digest computed by a different path can disagree with the one the evidence chain
    stores, and then neither is authoritative.
    """
    result = _replay()
    assert result.content_sha256 == result.stamped.content_hash()
    assert len(result.content_sha256) == 64


@pytest.mark.parametrize(
    ("label", "kwargs"),
    [
        # The source's data. The case that matters most: a digest that did not move here
        # would be a digest over the request rather than over what was loaded.
        ("more samples", {"source": SyntheticSource(samples=9)}),
        ("different geometry", {"source": SyntheticSource(offset_m=4.0)}),
        # Stamp fields. Each is in the preimage because each changes what the number means.
        ("metric version", {"metric_version": "1.0.1"}),
        ("tolerance", {"atol": 1e-8}),
    ],
)
def test_a_changed_input_moves_the_digest(label: str, kwargs: dict[str, object]) -> None:
    """The control. Without it every test above passes against a constant."""
    assert _replay().content_sha256 != _replay(**kwargs).content_sha256, label  # pyright: ignore[reportArgumentType]


def test_load_order_does_not_move_the_digest() -> None:
    """Tracks are hashed in the dataset's own order, not the order they arrived in.

    A source free to return tracks in any order would otherwise produce a different digest per
    run and fail the determinism criterion for a reason that has nothing to do with
    determinism.
    """

    class _Reversed(SyntheticSource):
        def load(self, ref: object) -> object:  # pyright: ignore[reportIncompatibleMethodOverride]
            return tuple(reversed(tuple(super().load(ref))))  # pyright: ignore[reportArgumentType]

    assert _replay().content_sha256 == _replay(source=_Reversed()).content_sha256


def test_a_source_returning_nothing_raises_rather_than_stamping() -> None:
    """D57 at the product boundary.

    A metric over zero tracks still returns something, and that something would be stamped and
    stored as a measurement of a scenario nobody loaded.
    """

    class _Empty(SyntheticSource):
        def load(self, ref: object) -> tuple[()]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return ()

    with pytest.raises(ReplayContractViolation, match="zero tracks"):
        _replay(source=_Empty())


def test_a_metric_whose_arity_disagrees_with_its_result_raises() -> None:
    """A declaration nobody checks is a comment. This is the check."""

    class _Lying(SyntheticMetric):
        arity = 7

    harness = DeterministicReplay(_context())
    with pytest.raises(ReplayContractViolation, match="arity"):
        harness.replay(SyntheticSource(), synthetic_ref(), _Lying())


def test_the_harness_identity_is_reported_and_enters_the_digest() -> None:
    """Harness identity alone moves a measurement, which is why it is a fingerprint field."""
    harness = DeterministicReplay(_context())
    assert harness.identity()["name"] == "alfred.replay"

    other = DeterministicReplay(_context(), version="2.0.0")
    a = harness.replay(SyntheticSource(), synthetic_ref(), SyntheticMetric())
    b = other.replay(SyntheticSource(), synthetic_ref(), SyntheticMetric())
    assert a.content_sha256 != b.content_sha256


def test_a_degeneracy_is_stamped_as_a_value_rather_than_raising() -> None:
    """ADR-0001: degeneracies are values, contract violations are exceptions.

    A single-track scenario has no counterpart, which is E24 -- well-formed input, undefined
    quantity. It must produce a stamped `Undefined`, not an error and not a number.
    """

    class _Single(SyntheticSource):
        def load(self, ref: object) -> object:  # pyright: ignore[reportIncompatibleMethodOverride]
            return (tuple(super().load(ref))[0],)  # pyright: ignore[reportArgumentType]

    result = _replay(source=_Single())
    assert result.stamped.value.kind == "undefined"
