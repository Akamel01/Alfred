"""Result stamping and the one ACS-1 door (ADR-0003, ADR-0004).

Cannot be retrofitted: results computed before stamping exists are permanently
unrecallable.
"""

from __future__ import annotations

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
    RECORD_TYPE_INPUT,
    RECORD_TYPE_STAMP,
    RECORD_TYPE_STAMPED_RESULT,
    AssumptionSet,
    ResultStamp,
    StampedResult,
    Tolerance,
    hash_inputs,
)

__all__ = [
    "ACS_VERSION",
    "RECORD_TYPE_INPUT",
    "RECORD_TYPE_STAMP",
    "RECORD_TYPE_STAMPED_RESULT",
    "AcsError",
    "AcsValue",
    "AssumptionSet",
    "ResultStamp",
    "StampedResult",
    "Tolerance",
    "acs_sha256",
    "canonicalize",
    "hash_inputs",
    "metric_value_to_acs",
    "parse_strict",
]
