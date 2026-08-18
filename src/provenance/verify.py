"""The two-stage stamp read, and what a verifier says about a version it does not know.

ADR-0006's central property: **the encoder is chosen by the document, not by the
verifier's build.** Given stored bytes and a digest, read `stamp_schema_version` first,
select *that* version's encoder, then recompute. Match is authentic-old-shape; mismatch is
tampering. Without the two-stage read a legitimate schema change presents as tampering,
in the product whose thesis is tamper-evident re-derivability.

**Not "ignore the unknown fields."** The unknown fields are inside the digest. A verifier
that strips them and re-encodes computes a mismatch and reports *tampering* — this ADR's
own failure, relocated from the writer into the reader. And a verifier that hashes the raw
stored bytes reports VERIFIED while silently discarding every field it did not understand;
if a future v3 adds `upstream_attested: false`, that verifier returns "verified" for a
stamp whose single most important qualifier it never read.

This module deliberately returns its **own** vocabulary and never the three-valued verdict
words. Two reasons, and only the first is a lint: `scripts/lint_verdict_boundary.py` fails
any `src/` module returning `Literal["pass","fail","indeterminate"]` (D16/D39). The second
is that "I cannot check this" and "this failed the check" are different findings, and here
the difference is between *upgrade your verifier* and *you have been tampered with*. The
mapping onto failure semantics lives outside the product tree, in
`harness/stamp/verdict_map.py`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Final

from pydantic import ValidationError

from domain.errors import AlfredError
from provenance.encoding import AcsError, AcsValue, canonicalize, parse_strict
from provenance.stamp_v1 import STAMP_SCHEMA_VERSION_V1, ResultStampV1

# **The verifier is total.** Every input reaches one of the five outcomes and none of them is
# an exception: a reader that raises on a malformed stamp is not fail-closed, it is absent,
# and the caller who wrapped it in a bare `except` gets to choose what a failed verification
# means. `ContractViolation` is an `AlfredError`, which is **not** a `ValueError`, so a
# pydantic validator raising one escapes the obvious `except ValueError` — that is how this
# was found, and it is why the tuple is written out rather than narrowed by instinct.
_VALIDATION_FAILURES: Final = (ValidationError, ValueError, AlfredError)
_DECODE_FAILURES: Final = (AcsError, UnicodeDecodeError, ValueError, AlfredError)

__all__ = [
    "HIGHEST_KNOWN_SCHEMA",
    "SCHEMA_VERSION_KEY",
    "StampVerification",
    "StampVerificationResult",
    "encoder_for",
    "known_schema_versions",
    "verify_stamp",
    "verify_stamp_bytes",
]

# Pinned forever. Never renamed, never nested, never retyped, never optional: every future
# schema version's readability depends on this one field being unconditionally locatable.
SCHEMA_VERSION_KEY: Final[str] = "stamp_schema_version"

# One frozen encoder per schema version, kept for as long as any stamp under it exists.
# **No version is ever retired while a stamp under it exists** — that is this mechanism's
# real and permanent cost, and it is paid in maintenance rather than in trust.
_ENCODERS: Final[Mapping[int, type[ResultStampV1]]] = {STAMP_SCHEMA_VERSION_V1: ResultStampV1}

HIGHEST_KNOWN_SCHEMA: Final[int] = max(_ENCODERS)


def known_schema_versions() -> tuple[int, ...]:
    """Every schema version this build can verify, ascending.

    Public because the ADR-0006 enforcement checks iterate the registry, and a check that
    reached into a private name would be coupled to this module's internals rather than to
    the property it asserts.
    """
    return tuple(sorted(_ENCODERS))


def encoder_for(version: int) -> type[ResultStampV1] | None:
    """The frozen model for one schema version, or None when this build cannot read it."""
    return _ENCODERS.get(version)


class StampVerification(Enum):
    """What a verifier concluded. Never collapsed into a boolean.

    `UNVERIFIABLE_*` is never `MISMATCH` and never `VERIFIED`, and is fail-closed at the
    product boundary: a result whose stamp cannot be verified does not ship as verified.
    """

    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    UNVERIFIABLE_SCHEMA_TOO_NEW = "UNVERIFIABLE_SCHEMA_TOO_NEW"
    # Should be unreachable, since retirement is forbidden while stamps exist. Specified so
    # that reaching it is loud rather than convenient.
    UNVERIFIABLE_SCHEMA_RETIRED = "UNVERIFIABLE_SCHEMA_RETIRED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class StampVerificationResult:
    """The conclusion, plus what an operator needs in order to act on it."""

    verification: StampVerification
    detail: str
    # Carried on **every** result, not only the unverifiable ones: an operator told
    # "cannot verify" without being told what this verifier can read cannot act.
    verifier_highest_known_schema: int = HIGHEST_KNOWN_SCHEMA
    document_schema_version: int | None = None

    @property
    def verified(self) -> bool:
        return self.verification is StampVerification.VERIFIED


def _read_schema_version(document: AcsValue) -> int | None:
    """Stage one. Returns None when the document is not a stamp at all.

    A missing, non-integer or below-1 version is `INVALID`, never `UNVERIFIABLE`: a
    document without the pinned field is not an old stamp, and treating it as one would
    resurrect the unversioned eight-key shape as a permanent implicit version zero —
    which zero persisted stamps lets us refuse outright.
    """
    if not isinstance(document, dict):
        return None
    raw = document.get(SCHEMA_VERSION_KEY)
    # `bool` is an `int` in Python, and `True` is not a schema version.
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 1:
        return None
    return raw


def verify_stamp(document: AcsValue, expected_digest: str) -> StampVerificationResult:
    """Two-stage: read the version, dispatch to its encoder, recompute, compare."""
    version = _read_schema_version(document)
    if version is None:
        return StampVerificationResult(
            verification=StampVerification.INVALID,
            detail=(
                f"{SCHEMA_VERSION_KEY!r} is absent, non-integer or below 1; "
                "the document is not a stamp"
            ),
        )

    encoder = encoder_for(version)
    if encoder is None:
        # The two unverifiable arms are distinguished by which side of the verifier's own
        # ceiling the document sits on. Above it means upgrade; at or below it means an
        # encoder that should still exist does not.
        too_new = version > HIGHEST_KNOWN_SCHEMA
        return StampVerificationResult(
            verification=(
                StampVerification.UNVERIFIABLE_SCHEMA_TOO_NEW
                if too_new
                else StampVerification.UNVERIFIABLE_SCHEMA_RETIRED
            ),
            detail=(
                f"schema version {version} is not implemented here "
                f"(highest known: {HIGHEST_KNOWN_SCHEMA})"
            ),
            document_schema_version=version,
        )

    try:
        stamp = encoder.model_validate(document)
    except _VALIDATION_FAILURES as exc:
        # The version is one this verifier implements, and the document still does not fit
        # it. That is a malformed stamp, not an unreadable one.
        return StampVerificationResult(
            verification=StampVerification.INVALID,
            detail=f"document does not validate against schema version {version}: {exc}",
            document_schema_version=version,
        )

    try:
        recomputed = stamp.digest()
    except _DECODE_FAILURES as exc:  # pragma: no cover — a validated stamp is always encodable
        return StampVerificationResult(
            verification=StampVerification.INVALID,
            detail=f"validated stamp could not be encoded: {exc}",
            document_schema_version=version,
        )

    if recomputed != expected_digest:
        return StampVerificationResult(
            verification=StampVerification.MISMATCH,
            detail=f"expected {expected_digest}, recomputed {recomputed}",
            document_schema_version=version,
        )
    return StampVerificationResult(
        verification=StampVerification.VERIFIED,
        detail=f"schema version {version}",
        document_schema_version=version,
    )


def verify_stamp_bytes(stored: bytes, expected_digest: str) -> StampVerificationResult:
    """The same read, starting from stored canonical bytes rather than a parsed document.

    Parsing is strict and is part of the verification: bytes that are not ACS-1 canonical
    form are `INVALID` before any digest is computed. A verifier that hashed them anyway
    would report on a document nobody can reproduce.

    **Strict parsing alone is not a canonicality check.** `parse_strict` refuses duplicate
    keys and the non-standard numeric literals, but it is `json.loads` underneath and so
    accepts insignificant whitespace and unsorted keys — both of which change the bytes and
    therefore the digest. The check is a re-encode: canonical form is injective, so
    `canonicalize(parse_strict(b)) == b` holds for exactly the canonical inputs.
    """
    try:
        document = parse_strict(stored)
    except _DECODE_FAILURES as exc:
        return StampVerificationResult(
            verification=StampVerification.INVALID,
            detail=f"stored bytes are not readable as ACS-1: {exc}",
        )

    try:
        reencoded = canonicalize(document)
    except _DECODE_FAILURES as exc:  # pragma: no cover — parse_strict output re-encodes
        return StampVerificationResult(
            verification=StampVerification.INVALID,
            detail=f"stored bytes did not survive a re-encode: {exc}",
        )

    if reencoded != stored:
        return StampVerificationResult(
            verification=StampVerification.INVALID,
            detail=(
                "stored bytes are not ACS-1 canonical form: they parse, but re-encoding "
                "produces different bytes, so the digest they claim is not computable from them"
            ),
        )
    return verify_stamp(document, expected_digest)
