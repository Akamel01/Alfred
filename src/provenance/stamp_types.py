"""Shared stamp vocabulary: record types, tolerance, assumption set, the input hash.

These are **not** versioned, and nothing here is inside any schema version's encoder.
Each frozen stamp module (`stamp_v1` and its successors) spells its own encoding of
`AssumptionSet` and `Tolerance` privately, so an edit in this file can never move a
stored digest. Treat that as the contract of this module: it defines validation and
in-memory shape, never wire bytes.

Every hash reached from here goes through ACS-1 with **domain separation**, so a result
stamp and an evidence row with coincidentally identical content cannot collide
(ADR-0003 §9).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Final

from pydantic import Field, field_validator

from domain.base import AlfredModel
from domain.errors import ContractViolation
from provenance.encoding import AcsValue, acs_sha256

__all__ = [
    "RECORD_TYPE_INPUT",
    "RECORD_TYPE_STAMP",
    "RECORD_TYPE_STAMPED_RESULT",
    "AssumptionSet",
    "Tolerance",
    "hash_inputs",
]

# Domain separation tags. Distinct record types are what stop two structurally identical
# records hashing the same; they are part of the preimage, never of the document.
#
# `RECORD_TYPE_STAMP` is deliberately **not** versioned alongside `stamp_schema_version`:
# see `ResultStampV1.digest` for why a second place to bump is a second place to drift.
RECORD_TYPE_INPUT: Final[str] = "alfred.metric_input"
RECORD_TYPE_STAMP: Final[str] = "alfred.result_stamp"
RECORD_TYPE_STAMPED_RESULT: Final[str] = "alfred.stamped_result"


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
        """Convenience form for callers outside a stamp. **Not** the v1 wire encoding."""
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
        """Convenience form for callers outside a stamp. **Not** the v1 wire encoding."""
        return {
            "name": self.name,
            "version": self.version,
            "entries": dict(sorted(self.entries.items())),
        }
