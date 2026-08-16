"""`MetricSeries` — the internal, vectorized form (ADR-0001).

`values: float64[]` alongside `reasons: uint8[]` over a shared timebase. The
reason array **is** the mask: `0` means the value at that index is defined, and
any non-zero code means it must not be read. That costs one byte per sample and,
unlike a boolean mask or a `MaskedArray`, keeps the *reason* per timestep — which
is what stops E7, E8 and E16 collapsing into one another.

Per-timestep objects measured ~60x slower than vectorized evaluation on a
TTC-shaped formula (29.5 ms vs 0.5 ms over 200,000 values), so this is the shape
metrics compute in. `to_value` is the single declared conversion point to the
boundary form; nothing else in the system is allowed to be one.

NaN never appears in `values`. A degenerate timestep carries a reason code
instead — that substitution is the entire point of the type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

import numpy as np
from numpy.typing import NDArray

from domain.errors import ContractViolation, LengthMismatch, UnsortedTimestamps
from metrics.reasons import DEFINED_CODE, REASON_CODEBOOK_VERSION, Reason, decode_reason
from metrics.value import Defined, Infinite, MetricValue, Undefined

__all__ = ["MetricSeries"]


def _frozen(array: NDArray[np.float64] | NDArray[np.uint8]) -> None:
    array.setflags(write=False)


@dataclass(frozen=True, slots=True)
class MetricSeries:
    """A metric evaluated over a timebase, with per-sample definedness.

    Not a Pydantic model: this type never crosses a boundary. Anything persisted
    or sent is `MetricValue`, which is why `reason_codebook_version` travels with
    the series — a stored array's dtype and code meanings live inside a versioned
    envelope (ADR-0002).
    """

    t: NDArray[np.float64]
    values: NDArray[np.float64]
    reasons: NDArray[np.uint8]
    reason_codebook_version: int = REASON_CODEBOOK_VERSION

    def __post_init__(self) -> None:
        if self.t.ndim != 1 or self.values.ndim != 1 or self.reasons.ndim != 1:
            raise LengthMismatch("MetricSeries arrays must be 1-D")
        if self.t.dtype != np.float64 or self.values.dtype != np.float64:
            raise ContractViolation("t and values must be float64")
        if self.reasons.dtype != np.uint8:
            raise ContractViolation("reasons must be uint8 (ADR-0002)")
        n = self.t.size
        if self.values.size != n or self.reasons.size != n:
            raise LengthMismatch(
                f"MetricSeries lengths differ: t={n} values={self.values.size} "
                f"reasons={self.reasons.size}"
            )
        if n and not bool(np.isfinite(self.t).all()):
            raise ContractViolation("timebase contains NaN or infinity")
        if n > 1 and not bool(np.all(np.diff(self.t) > 0.0)):
            raise UnsortedTimestamps("MetricSeries timebase is not strictly increasing")
        if n and bool(np.isnan(self.values).any()):
            # The invariant the whole architecture exists to hold. A degenerate
            # timestep carries a reason code; it never carries NaN, because NaN
            # propagates silently and `NaN != NaN` defeats equality-based detection.
            raise ContractViolation("MetricSeries values contain NaN; use a reason code instead")
        _frozen(self.t)
        _frozen(self.values)
        _frozen(self.reasons)

    # ------------------------------------------------------------ constructors

    @classmethod
    def all_defined(cls, t: NDArray[np.float64], values: NDArray[np.float64]) -> Self:
        """Every sample defined. `+inf` is legal here; NaN is not."""
        return cls(
            t=np.asarray(t, dtype=np.float64),
            values=np.asarray(values, dtype=np.float64),
            reasons=np.zeros(np.asarray(t).size, dtype=np.uint8),
        )

    @classmethod
    def all_undefined(cls, t: NDArray[np.float64], reason: Reason) -> Self:
        """Every sample undefined for one reason — E23, E24 and the other whole-input cases."""
        if reason is Reason.DEFINED:
            raise ContractViolation("all_undefined requires a non-zero reason code")
        size = np.asarray(t).size
        return cls(
            t=np.asarray(t, dtype=np.float64),
            values=np.zeros(size, dtype=np.float64),
            reasons=np.full(size, int(reason), dtype=np.uint8),
        )

    # --------------------------------------------------------------- accessors

    def __len__(self) -> int:
        return int(self.t.size)

    @property
    def defined_mask(self) -> NDArray[np.bool_]:
        return self.reasons == DEFINED_CODE

    def reason_at(self, index: int) -> Reason:
        """The decoded reason. An integer this codebook version does not know is
        `UNKNOWN_CODE`, never `DEFINED`."""
        return decode_reason(int(self.reasons[index]))

    # ------------------------------------------------- the one conversion point

    def to_value(self, index: int) -> MetricValue:
        """Convert one sample to its boundary form.

        The single declared conversion point of ADR-0001. Undefined samples never
        read `values[index]`, so whatever is parked there — 0.0, a stale
        intermediate — cannot escape as a plausible number.
        """
        reason = self.reason_at(index)
        if reason is not Reason.DEFINED:
            return Undefined(reason=reason.name)
        value = float(self.values[index])
        if value == float("inf"):
            return Infinite(sign="+")
        if value == float("-inf"):
            return Infinite(sign="-")
        return Defined(value=value)

    def to_values(self) -> list[MetricValue]:
        return [self.to_value(i) for i in range(len(self))]
