"""Result stamping — the shape in which a number leaves the system.

Cannot be retrofitted. A result computed before the stamp exists is permanently
unrecallable: there is no way, afterwards, to say which formula version and which
assumptions produced it, so an advisory naming affected results cannot be written
and the recall mechanism the product sells does not exist for those rows.

**Reading a stamp is two-stage** (ADR-0006). Parse as ACS-1, read `stamp_schema_version`,
*then* dispatch to that version's validator. A single model validating every version is
forbidden: it would have to make version-specific fields optional, reintroducing precisely
the optionality ADR-0006 rejects. Each schema version gets its own frozen module, and old
modules are never edited — the same discipline as the ADR log. `provenance.verify` is the
reader; `ResultStamp` below is an alias for the current version and is a *writer's*
convenience, never a reader's entry point.
"""

from __future__ import annotations

from domain.base import AlfredModel
from metrics.value import MetricValue
from provenance.encoding import AcsValue, acs_sha256, metric_value_to_acs
from provenance.stamp_types import (
    RECORD_TYPE_INPUT,
    RECORD_TYPE_STAMP,
    RECORD_TYPE_STAMPED_RESULT,
    AssumptionSet,
    Tolerance,
    hash_inputs,
)
from provenance.stamp_v1 import STAMP_SCHEMA_VERSION_V1, ResultStampV1

__all__ = [
    "RECORD_TYPE_INPUT",
    "RECORD_TYPE_STAMP",
    "RECORD_TYPE_STAMPED_RESULT",
    "STAMP_SCHEMA_VERSION_V1",
    "AssumptionSet",
    "ResultStamp",
    "ResultStampV1",
    "StampedResult",
    "Tolerance",
    "hash_inputs",
]

# The current schema version, for code that *writes* stamps. A reader must never bind to
# this name: it moves when v2 lands, and a reader that moved with it would be validating
# old documents against a new model, which is the thing ADR-0006 forbids outright.
# A plain assignment, not a `type` alias: callers construct through this name, and a
# PEP 695 alias is a type-position-only object that cannot be called or validated through.
ResultStamp = ResultStampV1


class StampedResult(AlfredModel):
    """A metric value that can be re-derived and, if necessary, recalled.

    The only shape in which a number leaves the system. An unstamped result is not
    a cheaper result; it is an unrecallable one.

    **This record carries no schema version of its own** (ADR-0016, amending ADR-0006). It
    is a stamp plus a value and has no independent shape axis: the contained stamp's
    `stamp_schema_version` is inside this record's preimage, so a reader two-stage-reads
    straight through it. A second version key here would be a second place to bump, which
    is a second place to drift — the same argument ADR-0006 makes against versioning the
    record type. The consequence is accepted deliberately: the two records' lifecycles are
    coupled, and a change to `MetricValue`'s tagged encoding is a stamp-schema bump.
    """

    value: MetricValue
    stamp: ResultStampV1

    def to_acs(self) -> dict[str, AcsValue]:
        # `value` uses the ADR-0001 tagged form because ACS-1 refuses a raw
        # infinity: the arm that makes the value JSON-legal is the same arm that
        # makes it hashable.
        return {"stamp": self.stamp.to_acs(), "value": metric_value_to_acs(self.value)}

    def content_hash(self) -> str:
        return acs_sha256(RECORD_TYPE_STAMPED_RESULT, self.to_acs())
