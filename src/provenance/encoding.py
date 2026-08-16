"""The single door to ACS-1 (ADR-0003, ADR-0004).

Product code hashes structures through this module and nowhere else. ACS-1 itself
lives in `harness/`, outside the agent tree and in the protected set, and is
**imported, never reimplemented** — a second encoder is a second canonical form,
and the point of the scheme is that there is exactly one.

The conversion here is small but load-bearing. ACS-1 carries floats as strings and
refuses non-finite numbers outright, so a `MetricValue` must cross in its tagged
form: `{"kind":"infinite","sign":"+"}` hashes, `inf` raises. That refusal is a
feature — it is the last place a silent `+inf → null` could be caught.
"""

from __future__ import annotations

from harness.acs.acs1 import ACS_VERSION, AcsError, acs_sha256, canonicalize, parse_strict

from metrics.value import Defined, Infinite, MetricValue, Undefined

__all__ = [
    "ACS_VERSION",
    "AcsError",
    "AcsValue",
    "acs_sha256",
    "canonicalize",
    "metric_value_to_acs",
    "parse_strict",
]

type AcsScalar = str | int | float | bool | None
type AcsValue = AcsScalar | list[AcsValue] | dict[str, AcsValue]


def metric_value_to_acs(value: MetricValue) -> dict[str, AcsValue]:
    """The ACS-1-encodable form of a metric value.

    Explicit rather than `model_dump()` so the wire shape is pinned here and a
    later field addition to the Pydantic model cannot silently change a hash.
    """
    if isinstance(value, Defined):
        return {"kind": "defined", "value": value.value}
    if isinstance(value, Infinite):
        return {"kind": "infinite", "sign": value.sign}
    # The third arm. `MetricValue` is a closed union, so exhaustiveness here is a
    # type-checked fact rather than a runtime guess; adding a fourth arm without
    # extending this function fails pyright.
    undefined_value: Undefined = value
    out: dict[str, AcsValue] = {"kind": "undefined", "reason": undefined_value.reason}
    if undefined_value.cause is not None:
        out["cause"] = undefined_value.cause
    return out
