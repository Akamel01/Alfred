"""`MetricValue` — the tagged form every metric result takes on every boundary (ADR-0001).

```json
{"kind": "defined",   "value": 2.4}
{"kind": "infinite",  "sign": "+"}
{"kind": "undefined", "reason": "NO_CONFLICT_AREA"}
```

The tag is not decoration. Infinity cannot cross a JSON boundary as a float —
RFC 8259 has no infinity literal, and Pydantic v2's default serializer turns
`+inf` into `null`, which under a `float | None` representation would silently
convert "the event provably never occurs" into "the quantity is undefined" with
no error raised anywhere. ACS-1 refuses a non-finite float outright for the same
reason, so the tagged arm is what makes a result hashable at all.

`pyright --strict` cannot be talked out of the discriminator: a consumer has to
narrow on `kind` before it can do arithmetic, which is the property option B of
ADR-0001 (`value: float` plus a `defined: bool`) failed to have.
"""

from __future__ import annotations

import math
from typing import Annotated, Literal

from pydantic import Field, TypeAdapter, field_validator

from domain.base import AlfredModel
from domain.errors import ContractViolation
from metrics.reasons import Reason, reason_from_name

__all__ = [
    "METRIC_VALUE_ADAPTER",
    "Defined",
    "Infinite",
    "MetricValue",
    "Undefined",
    "defined",
    "infinite",
    "same_claim",
    "undefined",
    "upstream",
]


class Defined(AlfredModel):
    """A finite, meaningful number. `0.0` is a defined value, not an error signal."""

    kind: Literal["defined"] = "defined"
    value: float

    @field_validator("value")
    @classmethod
    def _finite(cls, value: float) -> float:
        # NaN is never an output anywhere in Alfred, and infinity has its own arm.
        # Admitting either here would put a number in the place a consumer reads
        # without narrowing further, which is the whole failure mode.
        if math.isnan(value):
            raise ContractViolation("NaN is never a metric output")
        if math.isinf(value):
            raise ContractViolation("infinity is carried by the 'infinite' arm, not as a float")
        return value


class Infinite(AlfredModel):
    """The event provably never occurs on the declared horizon (E1, E7 gap measures)."""

    kind: Literal["infinite"] = "infinite"
    sign: Literal["+", "-"] = "+"

    def as_float(self) -> float:
        """The in-memory value this arm denotes. Never serialized as a float."""
        return math.inf if self.sign == "+" else -math.inf


class Undefined(AlfredModel):
    """The quantity is not defined for this input. Carries the reason, by name."""

    kind: Literal["undefined"] = "undefined"
    reason: str
    cause: str | None = Field(
        default=None,
        description=(
            "For UPSTREAM_UNDEFINED, the originating reason. Composition never absorbs: "
            "an undefined input yields UPSTREAM_UNDEFINED carrying its cause, so the "
            "chain survives. Silent absorption is NaN with extra steps."
        ),
    )

    @field_validator("reason", "cause")
    @classmethod
    def _known_and_not_defined(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value == Reason.DEFINED.name:
            raise ContractViolation("the undefined arm cannot carry DEFINED as its reason")
        # An unrecognized name decodes to UNKNOWN_CODE rather than being rejected:
        # a result written by a newer codebook must remain readable, and readable
        # as explicitly-unknown rather than as anything more comfortable.
        return reason_from_name(value).name


type MetricValue = Annotated[Defined | Infinite | Undefined, Field(discriminator="kind")]

METRIC_VALUE_ADAPTER: TypeAdapter[MetricValue] = TypeAdapter(MetricValue)


# ------------------------------------------------------------------- constructors


def defined(value: float) -> Defined:
    return Defined(value=value)


def infinite(sign: Literal["+", "-"] = "+") -> Infinite:
    return Infinite(sign=sign)


def undefined(reason: Reason | str) -> Undefined:
    name = reason.name if isinstance(reason, Reason) else reason
    return Undefined(reason=name)


def upstream(cause: Reason | str) -> Undefined:
    """`Undefined(UPSTREAM_UNDEFINED)` carrying the originating reason.

    The one legal way for a composed metric to answer an undefined input.
    """
    name = cause.name if isinstance(cause, Reason) else cause
    if name == Reason.DEFINED.name:
        raise ContractViolation("a defined input is not an upstream-undefined cause")
    return Undefined(reason=Reason.UPSTREAM_UNDEFINED.name, cause=name)


# --------------------------------------------------------------------- comparison


def same_claim(left: MetricValue, right: MetricValue) -> bool:
    """Total comparison: match on `kind` first, then within the arm.

    This is what lets the criterion runner tell `Undefined(NO_CONFLICT_AREA)`
    from `Undefined(SINGLE_OCCUPANCY)` at verdict time — the distinction a
    `float | None` representation loses precisely where it matters most.
    """
    if left.kind != right.kind:
        return False
    if isinstance(left, Defined) and isinstance(right, Defined):
        return left.value == right.value
    if isinstance(left, Infinite) and isinstance(right, Infinite):
        return left.sign == right.sign
    if isinstance(left, Undefined) and isinstance(right, Undefined):
        return left.reason == right.reason and left.cause == right.cause
    return False  # pragma: no cover — unreachable while the union has three arms
