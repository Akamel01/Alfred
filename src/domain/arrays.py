"""Array-valued fields for Pydantic boundary models.

The domain is vectorized on purpose. ADR-0001 measured per-timestep objects at
~60x the cost of vectorized evaluation on a TTC-shaped formula (29.5 ms vs
0.5 ms over 200,000 values), and metrics are evaluated per timestep across a
scenario — so a scalar-first schema forces one Python object per timestep.

These annotated types are the single place ndarray fields are validated. They
copy on the way in and mark the result read-only, because a boundary model that
hands out a mutable view of its own state is not immutable in any useful sense.
"""

from __future__ import annotations

from typing import Annotated, cast

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pydantic import BeforeValidator, PlainSerializer

from domain.errors import LengthMismatch, UnitsViolation

__all__ = ["FiniteFloat64Array", "freeze_array", "readonly_float64"]


def freeze_array(array: NDArray[np.float64]) -> NDArray[np.float64]:
    """A read-only, C-contiguous copy."""
    out = np.array(array, dtype=np.float64, copy=True, order="C")
    out.setflags(write=False)
    return out


def readonly_float64(value: object) -> NDArray[np.float64]:
    """Coerce to a read-only 1-D float64 array, refusing non-finite entries.

    Non-finite coordinates are a contract violation rather than a degeneracy:
    NaN in an *input* is a caller bug, and admitting it here would let NaN reach
    a metric that the totality rule forbids from ever emitting one.
    """
    if not isinstance(value, (np.ndarray, list, tuple)):
        raise UnitsViolation(f"expected an array or sequence, got {type(value).__name__}")
    try:
        array = np.asarray(cast("ArrayLike", value), dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise UnitsViolation(f"value is not coercible to float64: {exc}") from exc
    if array.ndim != 1:
        raise LengthMismatch(f"expected a 1-D array, got {array.ndim} dimensions")
    if array.size and not bool(np.isfinite(array).all()):
        raise UnitsViolation("input array contains NaN or infinity")
    return freeze_array(array)


def _to_float_list(value: NDArray[np.float64]) -> list[float]:
    return [float(x) for x in value]


FiniteFloat64Array = Annotated[
    NDArray[np.float64],
    BeforeValidator(readonly_float64),
    PlainSerializer(_to_float_list, return_type=list[float]),
]
