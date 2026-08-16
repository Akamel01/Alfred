"""`MetricSeries`, the internal form, and the single conversion point (ADR-0001)."""

from __future__ import annotations

from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from domain.errors import ContractViolation, LengthMismatch, UnsortedTimestamps
from metrics.reasons import REASON_CODEBOOK_VERSION, Reason
from metrics.series import MetricSeries
from metrics.value import Defined, Infinite, Undefined


def _t(n: int) -> NDArray[np.float64]:
    return np.arange(n, dtype=np.float64) * 0.1


def test_reason_array_is_the_mask_and_keeps_the_reason_per_timestep() -> None:
    series = MetricSeries(
        t=_t(4),
        values=np.array([1.0, 0.0, np.inf, 0.0]),
        reasons=np.array(
            [
                Reason.DEFINED,
                Reason.NO_CONFLICT_AREA,
                Reason.DEFINED,
                Reason.SINGLE_OCCUPANCY,
            ],
            dtype=np.uint8,
        ),
    )
    values = series.to_values()
    assert isinstance(values[0], Defined)
    assert isinstance(values[1], Undefined)
    assert isinstance(values[2], Infinite)
    assert isinstance(values[3], Undefined)
    # A boolean mask would have collapsed these two into one bit.
    assert values[1].reason == "NO_CONFLICT_AREA"
    assert values[3].reason == "SINGLE_OCCUPANCY"
    assert series.defined_mask.tolist() == [True, False, True, False]


def test_undefined_samples_never_leak_the_number_parked_beside_them() -> None:
    series = MetricSeries(
        t=_t(2),
        values=np.array([42.0, 99.0]),  # plausible, stale, and unreadable
        reasons=np.array([Reason.NO_DATA, Reason.NO_COUNTERPART], dtype=np.uint8),
    )
    for value in series.to_values():
        assert isinstance(value, Undefined)


def test_infinity_is_a_legal_value_inside_the_series() -> None:
    series = MetricSeries.all_defined(_t(2), np.array([np.inf, -np.inf]))
    assert [v.sign for v in series.to_values() if isinstance(v, Infinite)] == ["+", "-"]


def test_nan_is_refused_in_values() -> None:
    with pytest.raises(ContractViolation, match="NaN"):
        MetricSeries.all_defined(_t(2), np.array([1.0, np.nan]))


def test_nan_is_refused_even_where_the_sample_is_undefined() -> None:
    with pytest.raises(ContractViolation, match="NaN"):
        MetricSeries(
            t=_t(1),
            values=np.array([np.nan]),
            reasons=np.array([Reason.NO_DATA], dtype=np.uint8),
        )


def test_unknown_stored_code_decodes_to_unknown_not_defined() -> None:
    series = MetricSeries(
        t=_t(1),
        values=np.array([7.0]),
        reasons=np.array([200], dtype=np.uint8),  # written by a later codebook
    )
    assert series.reason_at(0) is Reason.UNKNOWN_CODE
    value = series.to_value(0)
    assert isinstance(value, Undefined)
    assert value.reason == "UNKNOWN_CODE"


def test_length_mismatch_is_a_contract_violation() -> None:
    with pytest.raises(LengthMismatch):
        MetricSeries(
            t=_t(3),
            values=np.array([1.0, 2.0]),
            reasons=np.zeros(3, dtype=np.uint8),
        )


def test_unsorted_timebase_is_a_contract_violation() -> None:
    with pytest.raises(UnsortedTimestamps):
        MetricSeries.all_defined(np.array([0.0, 0.2, 0.1]), np.zeros(3))


def test_duplicate_timestamps_fail_the_same_check() -> None:
    with pytest.raises(UnsortedTimestamps):
        MetricSeries.all_defined(np.array([0.0, 0.0]), np.zeros(2))


def test_reasons_must_be_uint8() -> None:
    with pytest.raises(ContractViolation, match="uint8"):
        # A deliberately wrong dtype: the cast is what lets the runtime guard be
        # exercised at all, since the static type would otherwise forbid the call.
        wrong_width = cast("NDArray[np.uint8]", np.zeros(1, dtype=np.uint16))
        MetricSeries(t=_t(1), values=np.array([1.0]), reasons=wrong_width)


def test_arrays_are_read_only() -> None:
    series = MetricSeries.all_defined(_t(3), np.ones(3))
    with pytest.raises(ValueError, match="read-only"):
        series.values[0] = 5.0


def test_empty_series_is_legal() -> None:
    series = MetricSeries.all_defined(np.zeros(0), np.zeros(0))
    assert len(series) == 0
    assert series.to_values() == []


def test_all_undefined_refuses_the_defined_code() -> None:
    with pytest.raises(ContractViolation):
        MetricSeries.all_undefined(_t(2), Reason.DEFINED)


def test_series_carries_its_codebook_version() -> None:
    assert MetricSeries.all_defined(_t(1), np.zeros(1)).reason_codebook_version == (
        REASON_CODEBOOK_VERSION
    )
