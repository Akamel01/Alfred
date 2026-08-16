"""Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004)."""

from __future__ import annotations

import json
import math

import pytest
from pydantic import ValidationError

from domain.errors import ContractViolation
from metrics.reasons import Reason
from metrics.value import MetricValue, defined, infinite, undefined, upstream
from provenance.encoding import (
    ACS_VERSION,
    AcsError,
    AcsValue,
    acs_sha256,
    canonicalize,
    metric_value_to_acs,
    parse_strict,
)
from provenance.stamp import (
    RECORD_TYPE_STAMP,
    RECORD_TYPE_STAMPED_RESULT,
    AssumptionSet,
    ResultStamp,
    StampedResult,
    Tolerance,
    hash_inputs,
)

COMMIT = "0" * 39 + "a"


def make_stamp(**overrides: object) -> ResultStamp:
    fields: dict[str, object] = {
        "metric_id": "ttc",
        "metric_version": "1.0.0",
        "code_commit": COMMIT,
        "assumption_set": AssumptionSet(
            name="baseline",
            version="1.0.0",
            entries={"horizon_s": 10.0, "extrapolation": "constant_velocity"},
        ),
        "input_hash": hash_inputs({"scenario": "s1", "pair": ["a", "b"]}),
        "tolerance": Tolerance(atol=1e-9, rtol=1e-6),
    }
    fields.update(overrides)
    return ResultStamp.model_validate(fields)


def stamped(value: MetricValue) -> StampedResult:
    return StampedResult(value=value, stamp=make_stamp())


# ----------------------------------------------------------- the encoder is one


def test_stamp_hashes_identically_through_the_harness_encoder() -> None:
    result = stamped(defined(2.4))
    direct = acs_sha256(RECORD_TYPE_STAMPED_RESULT, result.to_acs())
    assert result.content_hash() == direct


def test_hash_is_stable_across_construction_order() -> None:
    a = stamped(defined(2.4))
    b = StampedResult(stamp=make_stamp(), value=defined(2.4))
    assert a.content_hash() == b.content_hash()


def test_canonical_bytes_are_reparseable_and_key_sorted() -> None:
    payload = canonicalize(stamped(defined(2.4)).to_acs())
    assert b" " not in payload
    round_tripped = parse_strict(payload)
    assert canonicalize(round_tripped) == payload


def test_floats_cross_acs_as_strings_in_the_pinned_grammar() -> None:
    document = json.loads(canonicalize({"v": 2.4, "w": 1.0, "z": -0.0}).decode())
    assert document == {"v": "2.4e0", "w": "1.0e0", "z": "0.0e0"}


def test_acs_version_is_recorded_in_the_stamp() -> None:
    assert make_stamp().acs_version == ACS_VERSION


# -------------------------------------------------------- domain separation §9


def test_record_types_separate_structurally_identical_records() -> None:
    document = stamped(defined(2.4)).to_acs()
    assert acs_sha256(RECORD_TYPE_STAMP, document) != acs_sha256(
        RECORD_TYPE_STAMPED_RESULT, document
    )


def test_stamp_digest_differs_from_the_stamped_result_digest() -> None:
    result = stamped(defined(2.4))
    assert result.stamp.digest() != result.content_hash()


# ------------------------------------------- every stamped field enters the hash


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("metric_id", "pet"),
        ("metric_version", "1.0.1"),
        ("code_commit", "b" * 40),
        ("input_hash", hash_inputs({"scenario": "s2"})),
        ("tolerance", Tolerance(atol=1e-8, rtol=1e-6)),
        (
            "assumption_set",
            AssumptionSet(name="baseline", version="1.0.1", entries={"horizon_s": 10.0}),
        ),
        ("reason_codebook_version", 2),
    ],
)
def test_changing_any_stamped_field_changes_the_hash(field: str, value: object) -> None:
    base = StampedResult(value=defined(2.4), stamp=make_stamp())
    changed = StampedResult(value=defined(2.4), stamp=make_stamp(**{field: value}))
    assert base.content_hash() != changed.content_hash()


def test_assumption_entries_enter_the_hash() -> None:
    a = AssumptionSet(name="b", version="1.0.0", entries={"horizon_s": 10.0})
    b = AssumptionSet(name="b", version="1.0.0", entries={"horizon_s": 12.0})
    assert acs_sha256("t", a.to_acs()) != acs_sha256("t", b.to_acs())


def test_input_hash_is_domain_separated_from_the_stamp() -> None:
    payload: AcsValue = {"scenario": "s1"}
    assert hash_inputs(payload) != acs_sha256(RECORD_TYPE_STAMP, payload)


# --------------------------------------------- the tagged form is what crosses


def test_infinite_result_hashes_because_it_is_tagged() -> None:
    # A raw +inf cannot be hashed at all; the arm that makes the value JSON-legal
    # is the same arm that makes it re-derivable.
    digest = stamped(infinite("+")).content_hash()
    assert len(digest) == 64
    assert digest != stamped(infinite("-")).content_hash()


def test_a_raw_infinity_is_refused_by_acs() -> None:
    with pytest.raises(AcsError):
        canonicalize({"v": math.inf})
    with pytest.raises(AcsError):
        canonicalize({"v": math.nan})


def test_the_three_arms_hash_differently() -> None:
    digests = {
        stamped(defined(2.4)).content_hash(),
        stamped(infinite("+")).content_hash(),
        stamped(undefined(Reason.NO_CONFLICT_AREA)).content_hash(),
    }
    assert len(digests) == 3


def test_two_undefined_reasons_are_not_the_same_result() -> None:
    assert (
        stamped(undefined(Reason.NO_CONFLICT_AREA)).content_hash()
        != stamped(undefined(Reason.SINGLE_OCCUPANCY)).content_hash()
    )


def test_the_hashed_reason_is_the_name_not_the_integer() -> None:
    document = metric_value_to_acs(undefined(Reason.NO_CONFLICT_AREA))
    assert document["reason"] == "NO_CONFLICT_AREA"
    assert b"NO_CONFLICT_AREA" in canonicalize(document)


def test_the_upstream_cause_survives_into_the_hash() -> None:
    assert (
        stamped(upstream(Reason.NO_CONFLICT_AREA)).content_hash()
        != stamped(upstream(Reason.SINGLE_OCCUPANCY)).content_hash()
    )


# ------------------------------------------------------------------ validation


def test_a_stamp_must_name_a_real_tree() -> None:
    for bad in ("unknown", "abc123", COMMIT.upper(), COMMIT + "-dirty"):
        with pytest.raises((ContractViolation, ValidationError)):
            make_stamp(code_commit=bad)


def test_input_hash_must_be_a_sha256_digest() -> None:
    for bad in ("", "deadbeef", "z" * 64):
        with pytest.raises((ContractViolation, ValidationError)):
            make_stamp(input_hash=bad)


def test_metric_version_must_be_a_version() -> None:
    for bad in ("v1", "1.0", "latest"):
        with pytest.raises((ContractViolation, ValidationError)):
            make_stamp(metric_version=bad)


def test_tolerance_must_be_finite_and_non_negative() -> None:
    with pytest.raises((ContractViolation, ValidationError)):
        Tolerance(atol=math.inf, rtol=0.0)
    with pytest.raises((ContractViolation, ValidationError)):
        Tolerance(atol=-1.0, rtol=0.0)


def test_non_finite_assumption_is_refused_before_it_reaches_acs() -> None:
    with pytest.raises((ContractViolation, ValidationError)):
        AssumptionSet(name="b", version="1.0.0", entries={"horizon_s": math.inf})


def test_a_result_cannot_be_emitted_without_a_stamp() -> None:
    with pytest.raises(ValidationError):
        StampedResult(value=defined(1.0))  # pyright: ignore[reportCallIssue] — the missing stamp is the point: this asserts a result cannot be constructed without one
