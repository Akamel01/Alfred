"""Metric representation types (ADR-0001, ADR-0002).

`MetricSeries` inside computation, `MetricValue` on every boundary, one declared
conversion point between them (`MetricSeries.to_value`). Metric implementations
themselves land here in Phase 1; this package is the representation they must
return in.
"""

from __future__ import annotations

from metrics.reasons import (
    ALLOCATION_CEILING,
    DEFINED_CODE,
    REASON_CODEBOOK_VERSION,
    UNKNOWN_CODE,
    CodebookError,
    Reason,
    check_codebook,
    decode_reason,
    reason_from_name,
    reason_name,
)
from metrics.series import MetricSeries
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

__all__ = [
    "ALLOCATION_CEILING",
    "DEFINED_CODE",
    "METRIC_VALUE_ADAPTER",
    "REASON_CODEBOOK_VERSION",
    "UNKNOWN_CODE",
    "CodebookError",
    "Defined",
    "Infinite",
    "MetricSeries",
    "MetricValue",
    "Reason",
    "Undefined",
    "check_codebook",
    "decode_reason",
    "defined",
    "infinite",
    "reason_from_name",
    "reason_name",
    "same_claim",
    "undefined",
    "upstream",
]
