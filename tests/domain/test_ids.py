"""`domain.ids.uuid7` and `harness.ids.uuid7`, and the claim that they agree (issue #80).

`harness/` is the protected inspector (D20) and duplicates `uuid7()` rather than importing
this module, so that a protected evidence writer never executes agent-writable code
(`harness/ids/__init__.py` explains the reasoning in full). Duplication is only safe if
divergence is loud, so this is the bridge test — the same shape as
`tests/test_stamp_verify.py` checking `harness.verdicts` against `provenance.verify`, and
the same claim-made-callable pattern as `harness/fingerprint/factory.py`'s
`d19_is_shared()`. `tests/` is the one place that may import both trees for verification;
neither `domain.ids` nor `harness.ids` imports the other at runtime, and this test does not
change that.

Both implementations take `timestamp_ms` and `random_bytes` as keyword arguments for exactly
this kind of deterministic comparison, so the check is exact equality over fixed inputs, not
"close enough to look right".
"""

from __future__ import annotations

from uuid import UUID

import pytest
from harness.ids import uuid7 as harness_uuid7

from domain.ids import uuid7 as product_uuid7

# Includes the top of the 48-bit timestamp range and both all-zero and all-one randomness,
# so the version/variant overwrite is exercised against bytes that would otherwise be 0x00
# or 0xFF in the bits being overwritten.
_CASES: tuple[tuple[int, bytes], ...] = (
    (0, b"\x00" * 10),
    (1, b"\x01" * 10),
    (1_700_000_000_000, bytes(range(10))),
    (2**48 - 1, b"\xff" * 10),
)


@pytest.mark.parametrize("timestamp_ms,random_bytes", _CASES)
def test_harness_and_product_uuid7_agree_byte_for_byte(
    timestamp_ms: int, random_bytes: bytes
) -> None:
    harness_value = harness_uuid7(timestamp_ms=timestamp_ms, random_bytes=random_bytes)
    product_value = product_uuid7(timestamp_ms=timestamp_ms, random_bytes=random_bytes)
    assert harness_value == product_value
    assert harness_value.bytes == product_value.bytes


def test_disagreement_is_not_vacuously_impossible_to_detect() -> None:
    """Negative control: two distinct inputs must not coincide, or the equality test above
    would pass no matter what either implementation did.
    """
    a = harness_uuid7(timestamp_ms=0, random_bytes=b"\x00" * 10)
    b = harness_uuid7(timestamp_ms=1, random_bytes=b"\x01" * 10)
    assert a != b


@pytest.mark.parametrize("timestamp_ms,random_bytes", _CASES)
def test_the_agreed_value_carries_the_v7_version_and_rfc9562_variant(
    timestamp_ms: int, random_bytes: bytes
) -> None:
    value = product_uuid7(timestamp_ms=timestamp_ms, random_bytes=random_bytes)
    assert value.version == 7
    # RFC 9562 variant: the top two bits of octet 8 are `10`.
    assert value.bytes[8] >> 6 == 0b10


@pytest.mark.parametrize("timestamp_ms,random_bytes", _CASES)
def test_the_agreed_value_carries_the_48_bit_big_endian_millisecond_prefix(
    timestamp_ms: int, random_bytes: bytes
) -> None:
    value = harness_uuid7(timestamp_ms=timestamp_ms, random_bytes=random_bytes)
    assert int.from_bytes(value.bytes[:6], byteorder="big") == timestamp_ms


def test_harness_uuid7_rejects_a_timestamp_outside_the_48_bit_range() -> None:
    with pytest.raises(ValueError, match="48-bit range"):
        harness_uuid7(timestamp_ms=2**48, random_bytes=b"\x00" * 10)


def test_harness_uuid7_rejects_random_bytes_of_the_wrong_length() -> None:
    with pytest.raises(ValueError, match="10 random bytes"):
        harness_uuid7(timestamp_ms=0, random_bytes=b"\x00" * 9)


def test_harness_uuid7_with_no_arguments_still_produces_a_valid_v7() -> None:
    value = harness_uuid7()
    assert isinstance(value, UUID)
    assert value.version == 7
