"""Property tests over the representation types.

Generated inputs, because the failures these guard against are exactly the ones a
hand-picked example misses: a reason code nobody thought to allocate, a float at
a boundary, an assumption key that normalizes to another one.
"""

from __future__ import annotations

import math

import numpy as np
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from metrics.reasons import DEFINED_CODE, Reason, decode_reason, reason_name
from metrics.series import MetricSeries
from metrics.value import METRIC_VALUE_ADAPTER, Defined, Infinite, MetricValue, same_claim
from provenance.encoding import canonicalize, parse_strict
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
