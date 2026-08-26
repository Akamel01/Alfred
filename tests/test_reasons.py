"""The reason codebook invariants (ADR-0002).

Each test here corresponds to a clause the ADR says CI asserts. Every one of them
was checked by mutation — deleting the guard it covers makes it fail — because a
test that still passes with the feature removed is not a test.
"""

from __future__ import annotations

import pytest

from metrics.reasons import (
    ALLOCATION_CEILING,
    DEFINED_CODE,
    FROZEN_CODEBOOK,
    UNKNOWN_CODE,
    CodebookError,
    Reason,
    allocated_reasons,
    check_codebook,
    decode_reason,
    reason_from_name,
    reason_name,
)


def test_codebook_passes_every_invariant() -> None:
    check_codebook()


def test_zero_is_defined_and_255_is_unknown() -> None:
    assert Reason.DEFINED == DEFINED_CODE
    assert Reason.UNKNOWN_CODE == UNKNOWN_CODE


def test_names_and_integers_are_bijective() -> None:
    mapping = allocated_reasons()
    assert len(set(mapping.values())) == len(mapping)


def test_enum_matches_the_frozen_codebook() -> None:
    assert dict(allocated_reasons()) == dict(FROZEN_CODEBOOK)


def test_a_renumbered_code_is_rejected() -> None:
    # Integers are stable within a codebook version. Renumbering silently changes
    # the meaning of every stored MetricSeries written under the old one.
    drifted = dict(FROZEN_CODEBOOK)
    drifted["NO_DATA"] = 8
    with pytest.raises(CodebookError, match="FROZEN_CODEBOOK"):
        check_codebook(drifted, frozen=FROZEN_CODEBOOK)


def test_a_renamed_code_is_rejected() -> None:
    # Names are stable and never reused: they are what the wire format and the
    # content-addressed hash carry.
    drifted = dict(FROZEN_CODEBOOK)
    drifted["NO_SAMPLES"] = drifted.pop("NO_DATA")
    with pytest.raises(CodebookError, match="FROZEN_CODEBOOK"):
        check_codebook(drifted, frozen=FROZEN_CODEBOOK)


def test_no_member_allocates_a_reserved_code() -> None:
    reserved = {member.name for member in Reason if int(member) in (DEFINED_CODE, UNKNOWN_CODE)}
    assert reserved == {"DEFINED", "UNKNOWN_CODE"}


@pytest.mark.parametrize("code", [8, 9, 100, 199, 253, 254])
def test_unrecognised_code_decodes_to_unknown_never_to_defined(code: int) -> None:
    decoded = decode_reason(code)
    assert decoded is Reason.UNKNOWN_CODE
    assert decoded is not Reason.DEFINED
    assert int(decoded) != DEFINED_CODE
    assert reason_name(code) == "UNKNOWN_CODE"


def test_known_codes_round_trip() -> None:
    for member in Reason:
        assert decode_reason(int(member)) is member
        assert reason_from_name(member.name) is member


def test_unrecognised_name_decodes_to_unknown_never_to_defined() -> None:
    assert reason_from_name("A_REASON_FROM_A_LATER_CODEBOOK") is Reason.UNKNOWN_CODE
    assert reason_from_name("") is Reason.UNKNOWN_CODE


def test_code_outside_uint8_is_a_contract_violation() -> None:
    with pytest.raises(CodebookError):
        decode_reason(256)
    with pytest.raises(CodebookError):
        decode_reason(-1)


# --------------------------------------------------------------- the CI ceiling


def _synthetic(count: int) -> dict[str, int]:
    """A codebook with `count` allocated codes plus the two reserved ones."""
    codes = {"DEFINED": 0, "UNKNOWN_CODE": 255}
    for i in range(1, count + 1):
        codes[f"SYNTHETIC_{i}"] = i
    return codes


def test_ceiling_admits_199_allocated_codes() -> None:
    check_codebook(_synthetic(ALLOCATION_CEILING - 1))


def test_build_fails_at_200_allocated_codes() -> None:
    with pytest.raises(CodebookError, match="ceiling"):
        check_codebook(_synthetic(ALLOCATION_CEILING))


def test_build_fails_past_the_ceiling_but_below_uint8_exhaustion() -> None:
    # The point of ADR-0002: the failure lands at 80%, well before 254, so the
    # widening decision is scheduled rather than an emergency.
    with pytest.raises(CodebookError, match="ceiling"):
        check_codebook(_synthetic(230))


def test_ceiling_is_below_the_usable_width() -> None:
    assert ALLOCATION_CEILING < 254


def test_duplicate_integer_is_rejected() -> None:
    codes = _synthetic(3)
    codes["SYNTHETIC_COLLIDING"] = 2
    with pytest.raises(CodebookError, match="bijective"):
        check_codebook(codes)


def test_reserved_codes_cannot_be_reallocated() -> None:
    stolen_zero = _synthetic(3)
    stolen_zero["SYNTHETIC_ZERO"] = 0
    with pytest.raises(CodebookError):
        check_codebook(stolen_zero)

    stolen_255 = _synthetic(3)
    stolen_255["SYNTHETIC_MAX"] = 255
    with pytest.raises(CodebookError):
        check_codebook(stolen_255)


def test_missing_reserved_allocation_is_rejected() -> None:
    with pytest.raises(CodebookError, match="DEFINED"):
        check_codebook({"UNKNOWN_CODE": 255})
    with pytest.raises(CodebookError, match="UNKNOWN_CODE"):
        check_codebook({"DEFINED": 0})


def test_code_wider_than_uint8_is_rejected() -> None:
    codes = _synthetic(2)
    codes["SYNTHETIC_WIDE"] = 300
    with pytest.raises(CodebookError, match="uint8"):
        check_codebook(codes)


def test_the_seven_catalog_reasons_are_present() -> None:
    # The Edge Case catalog's 30 rows reduce to these; most rows resolve to
    # defined values or raise as contract violations instead.
    expected = {
        "NO_CONFLICT_AREA",
        "SINGLE_OCCUPANCY",
        "INSUFFICIENT_SAMPLES",
        "NO_RELATIVE_MOTION",
        "NO_DATA",
        "NO_COUNTERPART",
        "UPSTREAM_UNDEFINED",
    }
    allocated = {name for name, code in allocated_reasons().items() if code not in (0, 255)}
    assert allocated == expected
