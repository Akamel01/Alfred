"""The `Metric` port — what a measure is, and the one shape it may return in.

One of the three S5 ports. Factory: this module names no measure. TTC, PET and every
other implementation is domain work behind it.

**The port exists to make one defect unrepresentable.** A metric returning a bare `float`
has to encode "no conflict area", "the event provably never occurs" and "2.4 seconds" in
one channel, and the first two then travel as `NaN`, `inf` or `None` — each of which either
propagates silently or collapses into a different meaning at the first JSON boundary
(ADR-0001). So `evaluate` returns `MetricSeries`, which carries a reason code per timestep
beside the value, and the single declared conversion to the boundary form is
`MetricSeries.to_value`. Nothing else in the system is allowed to be one.

The second rule is the error/degeneracy split, already implemented in `domain.errors` and
`metrics.value` and restated here because it is the rule an implementer gets wrong:
**a degeneracy is a value, a contract violation is an exception.** A lone agent, a
zero-length track and two agents whose paths never cross are all legal inputs answered with
`Undefined(reason)`. Mismatched array lengths and a self-pairing are `ContractViolation`.
A metric that raises on a degeneracy makes a whole scenario unmeasurable; one that returns
a number for a contract violation makes a wrong measurement look like a right one.

`arity` is declared rather than inferred. A pairwise measure handed one track and a
single-agent measure handed two are both caller errors, and the harness can only refuse
them if the metric says which it is.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from domain.trajectory import AgentTrack
from metrics.series import MetricSeries

__all__ = ["Metric"]


class Metric(Protocol):
    """One measure, evaluated over a timebase. Stateless; holds no scenario state."""

    @property
    def metric_id(self) -> str:
        """Stable identifier. Part of what a stamped result claims to be."""
        ...

    @property
    def arity(self) -> int:
        """The number of independent observations a metric aggregates.

        This is the declared arity, not inferred from the input. Examples:
        - 3-hop chain metric → arity = 3
        - Single-point collision check → arity = 1
        - Derived metric combining 2 base metrics → arity = 2

        The harness asserts `metric.arity == len(series)` (per ADR-0037). A mismatch
        means data loss or an injector bug.
        """
        ...

    def citation(self) -> Mapping[str, str]:
        """The formula's source, pinned. A measure whose definition cannot be cited cannot
        be shown to reproduce anything, and the citation is a fingerprint input rather than
        a comment: two implementations of "TTC" from different papers are two measures."""
        ...

    def evaluate(self, tracks: Sequence[AgentTrack]) -> MetricSeries:
        """The measure over the shared timebase.

        Raises `ContractViolation` when `len(tracks) != arity`, when the tracks disagree on
        anything the measure needs, or when a track violates its own contract. Returns a
        series carrying reason codes — never a float, never `None`, never `NaN`.
        """
        ...
