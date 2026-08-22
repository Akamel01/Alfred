"""The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).

Every row of the ADR's verdict table is exercised here, and the mapping onto
`pass`/`fail`/`indeterminate` is checked against `harness/verdicts` — the
one place that may import both trees, because `harness/` imports nothing from `src` and the
lint forbids `src/` from returning the verdict vocabulary.

The property under test is the one ADR-0006 exists to obtain: **the encoder is chosen by
the document, not by the verifier's build**, so a legitimate schema change can no longer
present as tampering.
"""

from __future__ import annotations

import json
from typing import Final

import pytest
from harness.verdicts import VERDICT_FOR_VERIFICATION, verdict_for

from provenance.encoding import AcsValue, canonicalize
from provenance.stamp import AssumptionSet, ResultStampV1, Tolerance
from provenance.upstream import CorpusUpstream
from provenance.verify import (
    HIGHEST_KNOWN_SCHEMA,
    SCHEMA_VERSION_KEY,
    StampVerification,
    verify_stamp,
    verify_stamp_bytes,
)

CORPUS: Final = CorpusUpstream(
    corpus_name="CommonRoad",
    corpus_version="2020a",
    scenario_id="ZAM_Urban-7_1_S-2",
    corpus_digest="2" * 64,
)

STAMP: Final = ResultStampV1(
    metric_id="ttc",
    metric_version="1.0.0",
    code_commit="0" * 39 + "a",
    assumption_set=AssumptionSet(name="baseline", version="1.0.0", entries={"horizon_s": 10.0}),
    input_hash="1" * 64,
    tolerance=Tolerance(atol=1e-9, rtol=1e-6),
    upstream=CORPUS,
)


def _document() -> dict[str, AcsValue]:
    return STAMP.to_acs()


# ------------------------------------------------------------------- the five rows


def test_a_current_stamp_verifies() -> None:
    result = verify_stamp(_document(), STAMP.digest())
    assert result.verification is StampVerification.VERIFIED
    assert result.verified
    assert result.document_schema_version == HIGHEST_KNOWN_SCHEMA


def test_a_tampered_document_is_mismatch_not_invalid() -> None:
    """The digest is wrong and the shape is right. That is tampering, and only that."""
    document = _document()
    document["metric_id"] = "pet"
    result = verify_stamp(document, STAMP.digest())
    assert result.verification is StampVerification.MISMATCH
    assert "recomputed" in result.detail


def test_a_future_version_is_unverifiable_and_never_mismatch() -> None:
    """The incident this ADR exists to prevent: *upgrade your verifier*, not *you have been
    tampered with*. A verifier that stripped the unknown fields and re-encoded would compute
    a mismatch and a naive implementation would report tampering."""
    document = _document()
    document[SCHEMA_VERSION_KEY] = HIGHEST_KNOWN_SCHEMA + 1
    document["upstream_attested"] = False
    result = verify_stamp(document, STAMP.digest())
    assert result.verification is StampVerification.UNVERIFIABLE_SCHEMA_TOO_NEW
    assert result.verification is not StampVerification.MISMATCH


def test_an_unverifiable_result_reports_the_verifier_ceiling() -> None:
    """Required by ADR-0006: without it the operator cannot act on the finding."""
    document = _document()
    document[SCHEMA_VERSION_KEY] = 99
    result = verify_stamp(document, STAMP.digest())
    assert result.verifier_highest_known_schema == HIGHEST_KNOWN_SCHEMA
    assert str(HIGHEST_KNOWN_SCHEMA) in result.detail
    assert result.document_schema_version == 99


@pytest.mark.parametrize(
    "version",
    [None, "1", 0, -1, True],
    ids=["absent", "string", "zero", "negative", "bool"],
)
def test_a_missing_or_malformed_version_is_invalid_not_unverifiable(version: object) -> None:
    """A document without the pinned field is not a stamp. Treating it as an old one would
    resurrect the unversioned eight-key shape as a permanent implicit version zero."""
    document = _document()
    if version is None:
        del document[SCHEMA_VERSION_KEY]
    else:
        document[SCHEMA_VERSION_KEY] = version  # pyright: ignore[reportArgumentType] — malformed is the point
    result = verify_stamp(document, STAMP.digest())
    assert result.verification is StampVerification.INVALID


def test_a_document_that_claims_a_known_version_and_does_not_fit_it_is_invalid() -> None:
    """Known-and-implemented plus non-validating is malformed, not unreadable."""
    document = _document()
    document["code_commit"] = "not-a-commit"
    result = verify_stamp(document, STAMP.digest())
    assert result.verification is StampVerification.INVALID
    assert result.document_schema_version == HIGHEST_KNOWN_SCHEMA


def test_a_non_object_document_is_invalid() -> None:
    assert verify_stamp([1, 2, 3], STAMP.digest()).verification is StampVerification.INVALID
    assert verify_stamp("not a stamp", STAMP.digest()).verification is StampVerification.INVALID


# --------------------------------------------------------------- the bytes-first entry point


def test_stored_canonical_bytes_verify() -> None:
    result = verify_stamp_bytes(canonicalize(_document()), STAMP.digest())
    assert result.verified


def test_non_canonical_stored_bytes_are_invalid_before_any_digest_is_computed() -> None:
    """A verifier that hashed them anyway would report on a document nobody can reproduce."""
    padded = canonicalize(_document()).replace(b'{"acs_version"', b'{ "acs_version"', 1)
    result = verify_stamp_bytes(padded, STAMP.digest())
    assert result.verification is StampVerification.INVALID
    assert "canonical" in result.detail


def test_bytes_that_are_not_json_at_all_are_invalid() -> None:
    assert (
        verify_stamp_bytes(b"\xff\xfe not json", STAMP.digest()).verification
        is StampVerification.INVALID
    )


# ------------------------------------------------------- the bridge to failure semantics


def test_every_verification_member_has_a_verdict_row() -> None:
    """Direction one: a member added to the enum and not to the table fails here."""
    for member in StampVerification:
        assert member.value in VERDICT_FOR_VERIFICATION, member.name


def test_every_verdict_row_names_a_real_verification_member() -> None:
    """Direction two: a row naming nothing is a row nobody will ever reach."""
    names = {member.value for member in StampVerification}
    assert set(VERDICT_FOR_VERIFICATION) == names


def test_the_bridge_scans_something() -> None:
    """D57. Both directions above are set comparisons and would agree on two empty sets."""
    assert len(StampVerification) == 5
    assert len(VERDICT_FOR_VERIFICATION) == 5


def test_the_verdicts_are_the_ones_the_adr_specifies() -> None:
    assert verdict_for(StampVerification.VERIFIED.value) == "pass"
    assert verdict_for(StampVerification.MISMATCH.value) == "fail"
    assert verdict_for(StampVerification.INVALID.value) == "fail"
    assert verdict_for(StampVerification.UNVERIFIABLE_SCHEMA_TOO_NEW.value) == "indeterminate"
    assert verdict_for(StampVerification.UNVERIFIABLE_SCHEMA_RETIRED.value) == "indeterminate"


def test_unverifiable_is_never_verified_at_the_product_boundary() -> None:
    """Fail-closed: a result whose stamp cannot be verified does not ship as verified."""
    document = _document()
    document[SCHEMA_VERSION_KEY] = HIGHEST_KNOWN_SCHEMA + 1
    assert verify_stamp(document, STAMP.digest()).verified is False


# ---------------------------------------------------------------------- the verifier is total


def test_unsorted_keys_are_not_canonical_even_though_they_parse() -> None:
    """Strict parsing is not a canonicality check: `parse_strict` is `json.loads` underneath
    and accepts unsorted keys, which change the bytes and therefore the digest."""
    # Round-trip the canonical bytes through a plain parser, reverse the key order, and
    # re-emit. The values are untouched — only the order changes, which is enough to make
    # the digest uncomputable from these bytes.
    parsed: dict[str, object] = json.loads(canonicalize(_document()).decode())
    reordered = {key: parsed[key] for key in reversed(list(parsed))}
    unsorted_bytes = json.dumps(reordered, separators=(",", ":"), ensure_ascii=False).encode()
    assert unsorted_bytes != canonicalize(_document())

    result = verify_stamp_bytes(unsorted_bytes, STAMP.digest())
    assert result.verification is StampVerification.INVALID
    assert "canonical" in result.detail


HOSTILE: Final[list[bytes]] = [
    b"",
    b"{}",
    b"null",
    b"[]",
    b"\xff\xfe not utf-8",
    b'{"stamp_schema_version":1}',
    b'{"stamp_schema_version":1,"stamp_schema_version":1}',
    b'{"stamp_schema_version":NaN}',
    b'{"stamp_schema_version":1e999}',
    b"{",
    b'{"code_commit":"not-a-commit","stamp_schema_version":1}',
]


@pytest.mark.parametrize("stored", HOSTILE, ids=range(len(HOSTILE)))
def test_no_input_makes_the_verifier_raise(stored: bytes) -> None:
    """Every input reaches one of the five outcomes. None of them is an exception.

    A reader that raises on a malformed stamp is not fail-closed — it is absent, and the
    caller who wrapped it in a bare `except` gets to decide what a failed verification means.
    This was a real defect: `ContractViolation` is an `AlfredError` and **not** a
    `ValueError`, so a pydantic validator raising one escaped the obvious `except ValueError`
    and propagated out of `verify_stamp` instead of returning `INVALID`.
    """
    result = verify_stamp_bytes(stored, STAMP.digest())
    assert result.verification in set(StampVerification)
    assert not result.verified


def test_the_hostile_table_is_not_empty() -> None:
    """D57. The parametrized check above would report nothing on an empty table."""
    assert len(HOSTILE) >= 10
