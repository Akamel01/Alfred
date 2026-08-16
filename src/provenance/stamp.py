"""Result stamping — metric version, code commit, assumption set, input hash, tolerance.

Cannot be retrofitted. A result computed before the stamp exists is permanently
unrecallable: there is no way, afterwards, to say which formula version and which
assumptions produced it, so an advisory naming affected results cannot be written
and the recall mechanism the product sells does not exist for those rows.

Every hash here goes through ACS-1 with **domain separation**, so a result stamp
and an evidence row with coincidentally identical content cannot collide
(ADR-0003 §9).
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Final

from pydantic import Field, field_validator

from domain.base import AlfredModel
from domain.errors import ContractViolation
from metrics.reasons import REASON_CODEBOOK_VERSION
from metrics.value import MetricValue
from provenance.encoding import ACS_VERSION, AcsValue, acs_sha256, metric_value_to_acs

__all__ = [
    "RECORD_TYPE_INPUT",
    "RECORD_TYPE_STAMP",
    "RECORD_TYPE_STAMPED_RESULT",
    "AssumptionSet",
    "ResultStamp",
    "StampedResult",
    "Tolerance",
    "hash_inputs",
]

# Domain separation tags. Distinct record types are what stop two structurally
# identical records hashing the same; they are part of the preimage, never of the
# document.
RECORD_TYPE_INPUT: Final[str] = "alfred.metric_input"
RECORD_TYPE_STAMP: Final[str] = "alfred.result_stamp"
RECORD_TYPE_STAMPED_RESULT: Final[str] = "alfred.stamped_result"

_SHA256_HEX = re.compile(r"\A[0-9a-f]{64}\Z")
_COMMIT_HEX = re.compile(r"\A[0-9a-f]{40}\Z")
_SEMVERISH = re.compile(r"\A[0-9]+\.[0-9]+\.[0-9]+\Z")


def hash_inputs(payload: AcsValue) -> str:
    """The input hash of a metric evaluation: ACS-1 over the declared inputs.

    Trajectory arrays are *artifacts* and are content-addressed as stored bytes
    (ADR-0003); what passes through here is the structured description that names
    them — artifact digests, pair identity, evaluation window, parameters.
    """
    return acs_sha256(RECORD_TYPE_INPUT, payload)


class Tolerance(AlfredModel):
    """The numeric tolerance a result was accepted under.

    Stamped because "reproduces the oracle" is meaningless without it, and because
    a tolerance loosened between versions is exactly the kind of change an audit
    has to be able to see.
    """

    atol: float = Field(ge=0.0)
    rtol: float = Field(ge=0.0)

    @field_validator("atol", "rtol")
    @classmethod
    def _finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ContractViolation("tolerance must be finite")
        return value

    def to_acs(self) -> dict[str, AcsValue]:
        return {"atol": self.atol, "rtol": self.rtol}


class AssumptionSet(AlfredModel):
    """The named, versioned set of modelling assumptions in force.

    Constant-velocity extrapolation, bounding-box inflation, the evaluation
    horizon: choices that change the number without changing the formula. Two
    results differing only in assumptions must be distinguishable, so the set is
    identified by name *and* version and its entries enter the hash.
    """

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    entries: Mapping[str, str | int | float | bool] = Field(default_factory=dict)

    @field_validator("entries")
    @classmethod
    def _finite_entries(
        cls, entries: Mapping[str, str | int | float | bool]
    ) -> Mapping[str, str | int | float | bool]:
        for key, value in entries.items():
            if isinstance(value, float) and not math.isfinite(value):
                raise ContractViolation(f"assumption {key!r} is non-finite; ACS-1 forbids it")
        return dict(entries)

    def to_acs(self) -> dict[str, AcsValue]:
        return {
            "name": self.name,
            "version": self.version,
            "entries": dict(sorted(self.entries.items())),
        }


class ResultStamp(AlfredModel):
    """Everything needed to re-derive a number, and to recall it if it was wrong."""

    metric_id: str = Field(min_length=1, description="Catalog identifier, e.g. 'ttc'.")
    metric_version: str = Field(description="Version of the formula implementation.")
    code_commit: str = Field(description="40-hex commit of the tree that computed it.")
    assumption_set: AssumptionSet
    input_hash: str = Field(description="ACS-1 digest of the declared inputs.")
    tolerance: Tolerance
    reason_codebook_version: int = Field(default=REASON_CODEBOOK_VERSION, ge=1)
    acs_version: str = Field(default=ACS_VERSION)

    @field_validator("metric_version")
    @classmethod
    def _semverish(cls, value: str) -> str:
        if not _SEMVERISH.match(value):
            raise ContractViolation(f"metric_version must be MAJOR.MINOR.PATCH, got {value!r}")
        return value

    @field_validator("code_commit")
    @classmethod
    def _commit(cls, value: str) -> str:
        # No "unknown", no short hashes, no dirty markers. A stamp that cannot
        # name the tree is not a stamp; it is a comment.
        if not _COMMIT_HEX.match(value):
            raise ContractViolation(f"code_commit must be 40 lowercase hex, got {value!r}")
        return value

    @field_validator("input_hash")
    @classmethod
    def _digest(cls, value: str) -> str:
        if not _SHA256_HEX.match(value):
            raise ContractViolation(f"input_hash must be 64 lowercase hex, got {value!r}")
        return value

    def to_acs(self) -> dict[str, AcsValue]:
        return {
            "acs_version": self.acs_version,
            "assumption_set": self.assumption_set.to_acs(),
            "code_commit": self.code_commit,
            "input_hash": self.input_hash,
            "metric_id": self.metric_id,
            "metric_version": self.metric_version,
            "reason_codebook_version": self.reason_codebook_version,
            "tolerance": self.tolerance.to_acs(),
        }

    def digest(self) -> str:
        return acs_sha256(RECORD_TYPE_STAMP, self.to_acs())


class StampedResult(AlfredModel):
    """A metric value that can be re-derived and, if necessary, recalled.

    The only shape in which a number leaves the system. An unstamped result is not
    a cheaper result; it is an unrecallable one.
    """

    value: MetricValue
    stamp: ResultStamp

    def to_acs(self) -> dict[str, AcsValue]:
        # `value` uses the ADR-0001 tagged form because ACS-1 refuses a raw
        # infinity: the arm that makes the value JSON-legal is the same arm that
        # makes it hashable.
        return {"stamp": self.stamp.to_acs(), "value": metric_value_to_acs(self.value)}

    def content_hash(self) -> str:
        return acs_sha256(RECORD_TYPE_STAMPED_RESULT, self.to_acs())
