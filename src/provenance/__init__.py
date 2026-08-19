"""Result stamping and the one ACS-1 door (ADR-0003, ADR-0004, ADR-0006).

Cannot be retrofitted: results computed before stamping exists are permanently
unrecallable.

`ResultStamp` is the **current** schema version, for writers. Readers go through
`provenance.verify.verify_stamp`, which selects the encoder from the document rather
than from this module's idea of "current".
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
    STAMP_SCHEMA_VERSION_V1,
    AssumptionSet,
    ResultStamp,
    ResultStampV1,
    StampedResult,
    Tolerance,
    hash_inputs,
)
from provenance.upstream import (
    RECORD_TYPE_UPSTREAM_CONFIG,
    CorpusUpstream,
    SimulatedUpstream,
    UnknownReason,
    UnknownUpstream,
    UpstreamToolchain,
    corpus_upstream,
    unknown_upstream,
)
from provenance.verify import (
    HIGHEST_KNOWN_SCHEMA,
    SCHEMA_VERSION_KEY,
    StampVerification,
    StampVerificationResult,
    verify_stamp,
    verify_stamp_bytes,
)

__all__ = [
    "ACS_VERSION",
    "HIGHEST_KNOWN_SCHEMA",
    "RECORD_TYPE_INPUT",
    "RECORD_TYPE_STAMP",
    "RECORD_TYPE_STAMPED_RESULT",
    "RECORD_TYPE_UPSTREAM_CONFIG",
    "SCHEMA_VERSION_KEY",
    "STAMP_SCHEMA_VERSION_V1",
    "AcsError",
    "AcsValue",
    "AssumptionSet",
    "CorpusUpstream",
    "ResultStamp",
    "ResultStampV1",
    "SimulatedUpstream",
    "StampVerification",
    "StampVerificationResult",
    "StampedResult",
    "Tolerance",
    "UnknownReason",
    "UnknownUpstream",
    "UpstreamToolchain",
    "acs_sha256",
    "canonicalize",
    "corpus_upstream",
    "hash_inputs",
    "metric_value_to_acs",
    "parse_strict",
    "unknown_upstream",
    "verify_stamp",
    "verify_stamp_bytes",
]
