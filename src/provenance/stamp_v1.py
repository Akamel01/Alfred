"""Result stamp, schema version 1 — the ten-key shape (ADR-0006).

**This file is frozen.** Once any stamp has been persisted under version 1, nothing here
may be edited: not a key name, not a type, not how a value canonicalizes. A change to any
of those changes the digest input, and a v1 digest must remain recomputable for as long as
a single v1 stamp exists. A future v2 is a *new module* beside this one, and this one is
never revisited. That is ADR-0004's "the vectors are the specification" applied to the
stamp shape, and it is the entire mechanism by which a legitimate schema change stops
presenting as tampering.

**The encoding is spelled here, in full, and calls nothing shared.** `AssumptionSet` and
`Tolerance` are shared, unversioned, editable models; if `to_acs()` on either were called
from this module, a future edit to either would silently rewrite v1's encoder output and
every stored v1 digest would read as `MISMATCH` — ADR-0006's own defect, one level down.
The six duplicated lines below are the price of that not being possible. Same reason
`metric_value_to_acs` spells `MetricValue`'s wire shape rather than calling `model_dump()`.
"""

from __future__ import annotations

import re
from typing import Final

from pydantic import Field, field_validator

from domain.base import AlfredModel
from domain.errors import ContractViolation
from metrics.reasons import REASON_CODEBOOK_VERSION
from provenance.encoding import ACS_VERSION, AcsValue, acs_sha256
from provenance.stamp_types import RECORD_TYPE_STAMP, AssumptionSet, Tolerance
from provenance.upstream import (
    CorpusUpstream,
    SimulatedUpstream,
    UnknownUpstream,
    UpstreamToolchain,
)

__all__ = ["STAMP_SCHEMA_VERSION_V1", "ResultStampV1"]

# An integer, not a semver. A stamp shape has no minor or patch axis: any change to the key
# set, to a key's type, or to how a value canonicalizes changes the digest input and is
# major by construction. Consistent with `reason_codebook_version`, already an integer.
#
# The eight-key shape that preceded this receives no number and is declared never-emitted,
# because it never was: zero stamps were ever persisted under it.
STAMP_SCHEMA_VERSION_V1: Final[int] = 1

_SHA256_HEX: Final = re.compile(r"\A[0-9a-f]{64}\Z")
_COMMIT_HEX: Final = re.compile(r"\A[0-9a-f]{40}\Z")
_SEMVERISH: Final = re.compile(r"\A[0-9]+\.[0-9]+\.[0-9]+\Z")


# ------------------------------------------------------- the v1 encoding, spelled out


def _assumption_set_v1_acs(value: AssumptionSet) -> dict[str, AcsValue]:
    """v1's encoding of an assumption set. Never delegates to `AssumptionSet.to_acs()`."""
    return {
        "entries": dict(sorted(value.entries.items())),
        "name": value.name,
        "version": value.version,
    }


def _tolerance_v1_acs(value: Tolerance) -> dict[str, AcsValue]:
    """v1's encoding of a tolerance. Never delegates to `Tolerance.to_acs()`."""
    return {"atol": value.atol, "rtol": value.rtol}


def _upstream_v1_acs(value: UpstreamToolchain) -> dict[str, AcsValue]:
    """v1's encoding of the upstream arm.

    Optional fields are **omitted when absent** rather than emitted as null, matching
    `metric_value_to_acs`'s treatment of `cause`. A declared blank and an absent field must
    not canonicalize to the same bytes.
    """
    if isinstance(value, SimulatedUpstream):
        out: dict[str, AcsValue] = {
            "config_digest": value.config_digest,
            "kind": "simulated",
            "tool_name": value.tool_name,
            "tool_version": value.tool_version,
        }
        if value.tool_build is not None:
            out["tool_build"] = value.tool_build
        if value.config_ref is not None:
            out["config_ref"] = value.config_ref
        return out
    if isinstance(value, CorpusUpstream):
        return {
            "corpus_digest": value.corpus_digest,
            "corpus_name": value.corpus_name,
            "corpus_version": value.corpus_version,
            "kind": "corpus",
            "scenario_id": value.scenario_id,
        }
    # The third arm. `UpstreamToolchain` is a closed union, so exhaustiveness here is a
    # type-checked fact; adding a fourth arm without extending this function fails pyright
    # — and a fourth arm is a `stamp_schema_version` bump anyway, never an edit to this file.
    unknown_value: UnknownUpstream = value
    # The reason travels as its **name**, never its ordinal (ADR-0002).
    return {"kind": "unknown", "reason": unknown_value.reason.name}


class ResultStampV1(AlfredModel):
    """Everything needed to re-derive a number, to recall it, and to say who produced it."""

    metric_id: str = Field(min_length=1, description="Catalog identifier, e.g. 'ttc'.")
    metric_version: str = Field(description="Version of the formula implementation.")
    code_commit: str = Field(description="40-hex commit of the tree that computed it.")
    assumption_set: AssumptionSet
    input_hash: str = Field(description="ACS-1 digest of the declared inputs.")
    tolerance: Tolerance

    # No default and no null arm. Absence is the ambiguity the design removes.
    upstream: UpstreamToolchain

    reason_codebook_version: int = Field(default=REASON_CODEBOOK_VERSION, ge=1)
    acs_version: str = Field(default=ACS_VERSION)

    # Versions the **document**; `acs_version` versions the **encoder**. Bumping one must
    # not imply the other. Pinned as a top-level integer key with exactly this name in every
    # schema version that will ever exist — never renamed, never nested, never retyped,
    # never optional. Every future version's readability depends on it being unconditionally
    # locatable, and it is inside `to_acs()` and therefore inside the preimage: a schema
    # version outside the digest is a claim anyone can rewrite.
    stamp_schema_version: int = Field(default=STAMP_SCHEMA_VERSION_V1)

    @field_validator("stamp_schema_version")
    @classmethod
    def _pinned(cls, value: int) -> int:
        if value != STAMP_SCHEMA_VERSION_V1:
            raise ContractViolation(
                f"this model is schema version {STAMP_SCHEMA_VERSION_V1}, got {value!r}; "
                "a different version is a different model, never this one with a field changed"
            )
        return value

    @field_validator("metric_version")
    @classmethod
    def _semverish(cls, value: str) -> str:
        if not _SEMVERISH.match(value):
            raise ContractViolation(f"metric_version must be MAJOR.MINOR.PATCH, got {value!r}")
        return value

    @field_validator("code_commit")
    @classmethod
    def _commit(cls, value: str) -> str:
        # No "unknown", no short hashes, no dirty markers. A stamp that cannot name the tree
        # is not a stamp; it is a comment.
        if not _COMMIT_HEX.match(value):
            raise ContractViolation(f"code_commit must be 40 lowercase hex, got {value!r}")
        return value

    @field_validator("input_hash")
    @classmethod
    def _input_digest(cls, value: str) -> str:
        if not _SHA256_HEX.match(value):
            raise ContractViolation(f"input_hash must be 64 lowercase hex, got {value!r}")
        return value

    @property
    def discharges_storage_duty(self) -> bool:
        """False iff `upstream` is the `unknown` arm.

        The instrument ADR-0006 asks for when it says the `unknown` state "must be visible,
        never silent". A count of stamps with this False is a defect count, and it is
        readable without parsing the arm.
        """
        return not isinstance(self.upstream, UnknownUpstream)

    def to_acs(self) -> dict[str, AcsValue]:
        """The ten keys, frozen. Sorted by UTF-8 byte sequence per ACS-1 rule 2."""
        return {
            "acs_version": self.acs_version,
            "assumption_set": _assumption_set_v1_acs(self.assumption_set),
            "code_commit": self.code_commit,
            "input_hash": self.input_hash,
            "metric_id": self.metric_id,
            "metric_version": self.metric_version,
            "reason_codebook_version": self.reason_codebook_version,
            "stamp_schema_version": self.stamp_schema_version,
            "tolerance": _tolerance_v1_acs(self.tolerance),
            "upstream": _upstream_v1_acs(self.upstream),
        }

    def digest(self) -> str:
        # The record type stays `alfred.result_stamp` across schema versions. Cross-version
        # collision is structurally impossible from the content: any v1 document carries
        # `"stamp_schema_version":1` and any v2 carries `2` at the same key, ACS-1 canonical
        # form is injective, so the preimages differ. Versioning the record type would
        # duplicate a guarantee already complete — and create a second place to bump.
        return acs_sha256(RECORD_TYPE_STAMP, self.to_acs())
