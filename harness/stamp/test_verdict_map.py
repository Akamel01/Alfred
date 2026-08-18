"""The verdict table's own tests, including its vacuity control.

The bridge to `StampVerification` lives in `tests/` because only the product-side suite may
import both trees. What is checkable from here is that the table is non-empty, that every
row lands in the three-valued vocabulary, and that an unmapped name raises rather than
defaulting.
"""

from __future__ import annotations

from typing import cast

import pytest

from harness.stamp.verdict_map import (
    VERDICT_FOR_VERIFICATION,
    VERDICT_WORDS,
    UnmappedVerification,
    verdict_for,
)

# The five rows ADR-0006 specifies, restated here rather than read from the module under
# test. A test that derives its expectation from its subject asserts nothing.
EXPECTED: dict[str, str] = {
    "VERIFIED": "pass",
    "MISMATCH": "fail",
    "UNVERIFIABLE_SCHEMA_TOO_NEW": "indeterminate",
    "UNVERIFIABLE_SCHEMA_RETIRED": "indeterminate",
    "INVALID": "fail",
}


def test_the_table_is_not_empty() -> None:
    """D57. A mapping with no rows would pass every row-wise test below for free."""
    assert len(VERDICT_FOR_VERIFICATION) > 0
    assert len(VERDICT_FOR_VERIFICATION) == len(EXPECTED)


@pytest.mark.parametrize(("name", "verdict"), sorted(EXPECTED.items()))
def test_each_adr_0006_row(name: str, verdict: str) -> None:
    assert verdict_for(name) == verdict


def test_every_verdict_is_in_the_three_valued_vocabulary() -> None:
    assert set(VERDICT_FOR_VERIFICATION.values()) <= VERDICT_WORDS


def test_unverifiable_is_never_fail_and_never_pass() -> None:
    """The distinction between 'upgrade your verifier' and 'you have been tampered with'."""
    for name, verdict in VERDICT_FOR_VERIFICATION.items():
        if name.startswith("UNVERIFIABLE"):
            assert verdict == "indeterminate", name


def test_an_unmapped_name_raises_rather_than_defaulting() -> None:
    with pytest.raises(UnmappedVerification):
        verdict_for("UNVERIFIABLE_SCHEMA_SIDEWAYS")


def test_the_table_is_not_writable() -> None:
    """A mapping a caller can extend at runtime is not a table; it is a suggestion."""
    writable = cast("dict[str, str]", VERDICT_FOR_VERIFICATION)
    with pytest.raises(TypeError):
        writable["VERIFIED"] = "fail"
