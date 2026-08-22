"""Property tests over the representation types.

Generated inputs, because the failures these guard against are exactly the ones a
hand-picked example misses: a reason code nobody thought to allocate, a float at
a boundary, an assumption key that normalizes to another one.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from metrics.reasons import DEFINED_CODE, Reason, decode_reason, reason_name
from metrics.series import MetricSeries
from metrics.value import (
    METRIC_VALUE_ADAPTER,
    Defined,
    Infinite,
    MetricValue,
    defined,
    same_claim,
    upstream,
)
from provenance.encoding import canonicalize, metric_value_to_acs, parse_strict
from provenance.stamp import AssumptionSet, ResultStamp, StampedResult, Tolerance, hash_inputs
from provenance.upstream import CorpusUpstream

_ALLOCATED = {int(member) for member in Reason}

COMMIT = "0" * 39 + "a"


@given(code=st.integers(min_value=0, max_value=255))
def test_decoding_never_invents_definedness(code: int) -> None:
    """The invariant ADR-0002 exists for: no integer decodes to DEFINED unless it is 0."""
    decoded = decode_reason(code)
    if code == DEFINED_CODE:
        assert decoded is Reason.DEFINED
    else:
        assert decoded is not Reason.DEFINED
        assert int(decoded) != DEFINED_CODE
    if code not in _ALLOCATED:
        assert decoded is Reason.UNKNOWN_CODE


@given(code=st.integers(min_value=0, max_value=255))
def test_every_code_names_itself_stably(code: int) -> None:
    assert reason_name(code) == decode_reason(code).name
    assert reason_name(code).isupper()


@given(
    values=st.lists(
        st.one_of(
            st.floats(allow_nan=False, allow_infinity=False, width=64),
            st.sampled_from([math.inf, -math.inf, 0.0, -0.0]),
        ),
        min_size=0,
        max_size=40,
    ),
    codes=st.lists(st.integers(min_value=0, max_value=255), min_size=0, max_size=40),
)
def test_series_conversion_is_total(values: list[float], codes: list[int]) -> None:
    """Every sample converts to exactly one arm, and no undefined sample yields a number."""
    n = min(len(values), len(codes))
    series = MetricSeries(
        t=np.arange(n, dtype=np.float64),
        values=np.array(values[:n], dtype=np.float64),
        reasons=np.array(codes[:n], dtype=np.uint8),
    )
    for i, out in enumerate(series.to_values()):
        if codes[i] == DEFINED_CODE:
            assert isinstance(out, (Defined, Infinite))
            if isinstance(out, Defined):
                assert math.isfinite(out.value)
        else:
            assert out.kind == "undefined"


@given(value=st.floats(allow_nan=False, allow_infinity=False, width=64))
def test_defined_values_round_trip_through_the_boundary(value: float) -> None:
    parsed = METRIC_VALUE_ADAPTER.validate_json(
        METRIC_VALUE_ADAPTER.dump_json(Defined(value=value))
    )
    assert isinstance(parsed, Defined)
    # -0.0 and 0.0 are the same claim; ACS-1 normalizes them, so equality here is
    # deliberately value equality rather than bit equality.
    assert parsed.value == value


def _undefined_from_name(name: str) -> MetricValue:
    return METRIC_VALUE_ADAPTER.validate_python({"kind": "undefined", "reason": name})


@st.composite
def metric_values(draw: st.DrawFn) -> MetricValue:
    return draw(
        st.one_of(
            st.builds(
                Defined,
                value=st.floats(allow_nan=False, allow_infinity=False, width=64),
            ),
            st.builds(Infinite, sign=st.sampled_from(["+", "-"])),
            st.builds(
                _undefined_from_name,
                name=st.sampled_from([m.name for m in Reason if m is not Reason.DEFINED]),
            ),
        )
    )


@settings(max_examples=100)
@given(value=metric_values(), horizon=st.floats(min_value=0.1, max_value=100.0))
def test_stamped_results_hash_deterministically_and_reparse(
    value: MetricValue, horizon: float
) -> None:
    assume(math.isfinite(horizon))
    stamp = ResultStamp(
        metric_id="ttc",
        metric_version="1.0.0",
        code_commit=COMMIT,
        assumption_set=AssumptionSet(
            name="baseline", version="1.0.0", entries={"horizon_s": horizon}
        ),
        input_hash=hash_inputs({"scenario": "s1"}),
        tolerance=Tolerance(atol=1e-9, rtol=1e-6),
        upstream=CorpusUpstream(
            corpus_name="CommonRoad",
            corpus_version="2020a",
            scenario_id="ZAM_Urban-7_1_S-2",
            corpus_digest="2" * 64,
        ),
    )
    result = StampedResult(value=value, stamp=stamp)
    first = result.content_hash()
    assert first == StampedResult(value=value, stamp=stamp).content_hash()
    assert len(first) == 64

    payload = canonicalize(result.to_acs())
    assert canonicalize(parse_strict(payload)) == payload

    # And the boundary form survives a JSON round trip unchanged.
    reparsed = METRIC_VALUE_ADAPTER.validate_json(METRIC_VALUE_ADAPTER.dump_json(value))
    assert same_claim(reparsed, value)


# ------------------------------------------------------- wire form ↔ hash form binding


def _wire_without_nulls(form: dict[str, object]) -> dict[str, object]:
    """The wire's `cause: null` and the hash form's absent key are the same claim.

    Declared here because it is exactly where the two serializers could drift apart
    silently: pydantic serializes an unset field, `metric_value_to_acs` omits it. A
    consumer parsing either form must read the same value; this normalization is the
    pinned statement of that equivalence, and the property below is what notices if
    anything else about the two shapes ever disagrees.
    """
    return {k: v for k, v in form.items() if v is not None}


@settings(max_examples=100)
@given(value=metric_values())
def test_wire_form_and_hash_form_are_one_shape(value: MetricValue) -> None:
    """The pydantic boundary (what a customer parses) and the ACS preimage (what the
    audit chain hashes) are deliberately two spellings — stamp_v1 freezes its encoders
    so a shared one could not rewrite v1 digests. Deliberate independence is not
    permission to drift: for every arm, both forms must carry the identical claim."""
    wire = _wire_without_nulls(json.loads(METRIC_VALUE_ADAPTER.dump_json(value)))
    assert wire == metric_value_to_acs(value)


@pytest.mark.parametrize("sign", ["+", "-"])
def test_infinite_arm_carries_the_sign_on_both_forms(sign: str) -> None:
    """E1/E7: which infinity is asserted matters (`+` = never collides). Neither
    serializer may lose it — pydantic's default would have turned inf into null."""
    wire = json.loads(METRIC_VALUE_ADAPTER.dump_json(Infinite(sign=sign)))
    assert wire == {"kind": "infinite", "sign": sign}
    assert metric_value_to_acs(Infinite(sign=sign)) == wire


def test_a_cause_chain_is_present_on_both_forms() -> None:
    """Composition never absorbs (ADR-0001): UPSTREAM_UNDEFINED carries the originating
    reason, so the chain survives on the wire as well as in the hash preimage."""
    value = upstream(Reason.NO_DATA)
    wire = json.loads(METRIC_VALUE_ADAPTER.dump_json(value))
    acs = metric_value_to_acs(value)
    expected = {
        "kind": "undefined",
        "reason": "UPSTREAM_UNDEFINED",
        "cause": "NO_DATA",
    }
    assert wire == acs == expected


def test_negative_zero_hashes_as_positive_zero() -> None:
    """ADR-0001: `-0.0` is normalized to `0.0` before hashing. Both spellings of the
    same number must therefore produce the same canonical bytes, or a re-derived
    stamp would read as tampering on a sign-of-zero."""
    assert canonicalize(metric_value_to_acs(defined(-0.0))) == canonicalize(
        metric_value_to_acs(defined(0.0))
    )
    # The wire form keeps the value's own equality (−0.0 == 0.0) without pretending
    # the bytes were never different before the canonicalizer saw them.
    assert json.loads(METRIC_VALUE_ADAPTER.dump_json(defined(-0.0)))["value"] == 0.0
