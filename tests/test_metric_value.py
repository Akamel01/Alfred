"""`MetricValue`, the boundary form (ADR-0001).

The measurements that decided ADR-0001 are re-asserted here rather than trusted:
Pydantic v2 still serializes a bare `+inf` to `null`, which is what makes the
tagged arm necessary, and a test that only exercises the tagged arm would not
notice if that stopped being true.
"""

from __future__ import annotations

import json
import math

import pytest
from pydantic import BaseModel, ValidationError

from domain.errors import ContractViolation
from metrics.reasons import Reason
from metrics.value import (
    METRIC_VALUE_ADAPTER,
    Defined,
    Infinite,
    MetricValue,
    Undefined,
    defined,
    infinite,
    same_claim,
    undefined,
    upstream,
)


def _round_trip(value: MetricValue) -> MetricValue:
    payload = METRIC_VALUE_ADAPTER.dump_json(value)
    json.loads(payload)  # RFC 8259 valid: a strict decoder must accept it
    return METRIC_VALUE_ADAPTER.validate_json(payload)


@pytest.mark.parametrize(
    "value",
    [
        defined(2.4),
        defined(0.0),
        defined(-0.0),
        defined(5e-324),
        infinite("+"),
        infinite("-"),
        undefined(Reason.NO_CONFLICT_AREA),
        undefined(Reason.SINGLE_OCCUPANCY),
        upstream(Reason.INSUFFICIENT_SAMPLES),
    ],
)
def test_every_arm_round_trips_losslessly_through_rfc_valid_json(value: MetricValue) -> None:
    assert same_claim(_round_trip(value), value)


def test_the_wire_shapes_are_the_ones_the_adr_publishes() -> None:
    assert json.loads(METRIC_VALUE_ADAPTER.dump_json(defined(2.4))) == {
        "kind": "defined",
        "value": 2.4,
    }
    assert json.loads(METRIC_VALUE_ADAPTER.dump_json(infinite("+"))) == {
        "kind": "infinite",
        "sign": "+",
    }
    payload = json.loads(METRIC_VALUE_ADAPTER.dump_json(undefined(Reason.NO_CONFLICT_AREA)))
    assert payload["kind"] == "undefined"
    assert payload["reason"] == "NO_CONFLICT_AREA"


def test_reason_crosses_the_wire_as_a_name_never_as_an_integer() -> None:
    payload = json.loads(METRIC_VALUE_ADAPTER.dump_json(undefined(Reason.NO_DATA)))
    assert payload["reason"] == "NO_DATA"
    assert not isinstance(payload["reason"], int)


def test_nan_is_never_a_metric_output() -> None:
    with pytest.raises((ContractViolation, ValidationError)):
        defined(math.nan)


def test_infinity_cannot_be_carried_as_a_bare_float() -> None:
    for value in (math.inf, -math.inf):
        with pytest.raises((ContractViolation, ValidationError)):
            defined(value)


def test_pydantic_still_turns_a_bare_infinity_into_null() -> None:
    """ADR-0001's decisive measurement, re-run.

    If this ever stops holding, the ADR's reasoning changes and someone should be
    told — but the tagged form stays either way, because `Infinity` is not valid
    JSON.
    """

    class Naive(BaseModel):
        v: float

    assert json.loads(Naive(v=math.inf).model_dump_json()) == {"v": None}


def test_undefined_cannot_claim_to_be_defined() -> None:
    with pytest.raises((ContractViolation, ValidationError)):
        Undefined(reason="DEFINED")


def test_an_unknown_reason_name_decodes_to_unknown_code_not_to_a_defined_value() -> None:
    value = Undefined(reason="SOMETHING_A_LATER_VERSION_KNOWS")
    assert value.reason == "UNKNOWN_CODE"
    assert value.kind == "undefined"


def test_composition_never_absorbs() -> None:
    value = upstream(Reason.NO_CONFLICT_AREA)
    assert value.reason == "UPSTREAM_UNDEFINED"
    assert value.cause == "NO_CONFLICT_AREA"
    assert same_claim(_round_trip(value), value)


def test_upstream_refuses_a_defined_cause() -> None:
    with pytest.raises(ContractViolation):
        upstream(Reason.DEFINED)


def test_comparison_is_total_and_matches_on_kind_first() -> None:
    # The distinction a `float | None` representation loses exactly where it matters.
    assert not same_claim(undefined(Reason.NO_CONFLICT_AREA), undefined(Reason.SINGLE_OCCUPANCY))
    assert not same_claim(infinite("+"), undefined(Reason.NO_CONFLICT_AREA))
    assert not same_claim(infinite("+"), infinite("-"))
    assert not same_claim(defined(0.0), undefined(Reason.NO_DATA))
    assert same_claim(defined(1.5), defined(1.5))


def test_infinite_arm_denotes_the_right_float() -> None:
    assert Infinite(sign="+").as_float() == math.inf
    assert Infinite(sign="-").as_float() == -math.inf


def test_discriminated_union_rejects_a_missing_or_wrong_tag() -> None:
    with pytest.raises(ValidationError):
        METRIC_VALUE_ADAPTER.validate_python({"value": 1.0})
    with pytest.raises(ValidationError):
        METRIC_VALUE_ADAPTER.validate_python({"kind": "maybe", "value": 1.0})


def test_arms_are_frozen_and_reject_extra_fields() -> None:
    with pytest.raises(ValidationError):
        Defined(value=1.0, extra_field=2)  # pyright: ignore[reportCallIssue] — the extra field is deliberate: this asserts the frozen arms reject it
    value = defined(1.0)
    with pytest.raises(ValidationError):
        value.value = 2.0
