"""Conformance tests for ACS-1 against the published vector suite.

Two jobs. First, verify this implementation against `vectors.json` — the same file an
independent implementation is checked against, so passing here means the same thing it
would mean in another language. Second, assert the properties the vectors sample but
cannot exhaust.

    python3 -m pytest harness/acs/test_acs1.py -q

Passing here is necessary and not sufficient: a suite that asserts too little passes
too. `harness/acs/mutate.py` is the control that says how much this one asserts, and
every rule below is sized by it.
"""

from __future__ import annotations

import json
import random
import struct
from pathlib import Path

import pytest

from acs1 import (
    AcsError,
    acs_sha256,
    canonicalize,
    decode_float,
    encode_float,
    hash_input,
    is_canonical,
    parse_strict,
)
from gen_vectors import build

VECTORS = json.loads((Path(__file__).resolve().parent / "vectors.json").read_text())


# ------------------------------------------------------------------ vector conformance


@pytest.mark.parametrize("case", VECTORS["encode"], ids=lambda c: c["id"])
def test_encode_vector(case: dict) -> None:
    value = build(case["input"])
    assert canonicalize(value).hex() == case["canonical_hex"], case["note"]
    assert acs_sha256(case["record_type"], value) == case["sha256"]


@pytest.mark.parametrize("case", VECTORS["encode_errors"], ids=lambda c: c["id"])
def test_encode_error_vector(case: dict) -> None:
    with pytest.raises(AcsError) as exc:
        canonicalize(build(case["input"]))
    assert exc.value.code == case["error"], case["note"]


@pytest.mark.parametrize("case", VECTORS["hash"], ids=lambda c: c["id"])
def test_hash_vector(case: dict) -> None:
    """The record_type is hashed input, so it needs vectors of its own: NFC applies to
    it, and the NUL separators are what stop its boundary with the payload being
    forged."""
    digest = acs_sha256(build(case["record_type"]), build(case["input"]))
    assert digest == case["sha256"], case["note"]


@pytest.mark.parametrize(
    "case", [c for c in VECTORS["hash"] if c["equals"]], ids=lambda c: c["id"]
)
def test_hash_normalization_pairs(case: dict) -> None:
    """A decomposed record_type must hash as its composed twin, or the same record
    type stored twice produces two different chains."""
    twin = next(c for c in VECTORS["hash"] if c["id"] == case["equals"])
    assert case["sha256"] == twin["sha256"], case["note"]


@pytest.mark.parametrize("case", VECTORS["hash_errors"], ids=lambda c: c["id"])
def test_hash_error_vector(case: dict) -> None:
    with pytest.raises(AcsError) as exc:
        acs_sha256(build(case["record_type"]), build(case["input"]))
    assert exc.value.code == case["error"], case["note"]


@pytest.mark.parametrize("case", VECTORS["canonical"], ids=lambda c: c["id"])
def test_canonical_vector(case: dict) -> None:
    """The mirror of the non-canonical section. It fails if the parser mangles what a
    correct encoder emitted, which no encode vector can catch."""
    assert is_canonical(bytes.fromhex(case["input_hex"])), case["note"]


@pytest.mark.parametrize("case", VECTORS["parse"], ids=lambda c: c["id"])
def test_parse_vector(case: dict) -> None:
    data = bytes.fromhex(case["input_hex"])
    if case["error"] is None:
        parse_strict(data)
    elif case["error"] == "PARSE_ERROR":
        # Malformed JSON. Rejection is normative; the code is not, and here not even
        # the exception type is: a host that rejects the construct in its own
        # tokenizer raises its own error. See `parse_note` in the vector file.
        with pytest.raises(ValueError):
            parse_strict(data)
    else:
        # An ACS-1 semantic refusal — duplicate key, integer range, non-finite
        # constant. The input is well-formed JSON, so nothing but ACS-1's own rules
        # can be what rejects it.
        with pytest.raises(AcsError):
            parse_strict(data)


@pytest.mark.parametrize("case", VECTORS["non_canonical"], ids=lambda c: c["id"])
def test_non_canonical_vector(case: dict) -> None:
    assert not is_canonical(bytes.fromhex(case["input_hex"])), case["note"]


# ------------------------------------------------------------------ identity claims


def _sha(case_id: str) -> str:
    return next(c["sha256"] for c in VECTORS["encode"] if c["id"] == case_id)


def test_negative_zero_normalizes() -> None:
    assert _sha("f-zero") == _sha("f-neg-zero")


def test_nfc_and_nfd_hash_identically() -> None:
    assert _sha("s-nfc") == _sha("s-nfd")


def test_record_type_separates_identical_content() -> None:
    assert _sha("sep-evidence") != _sha("sep-result")


# ----------------------------------------------------------------------- properties


def _random_doubles(n: int, seed: int = 20260812) -> list[float]:
    rng = random.Random(seed)
    out: list[float] = []
    while len(out) < n:
        f = struct.unpack("<d", struct.pack("<Q", rng.getrandbits(64)))[0]
        if f == f and f not in (float("inf"), float("-inf")):
            out.append(f)
    return out


def test_float_grammar_round_trips_bit_exactly() -> None:
    """The encoding is lossless or it is not an encoding. Bit comparison rather than
    equality, so that -0.0 is not accepted as a round trip of 0.0."""
    for f in _random_doubles(50_000):
        recovered = decode_float(encode_float(f))
        expected = 0.0 if f == 0.0 else f  # -0.0 normalizes by design
        assert struct.pack("<d", recovered) == struct.pack("<d", expected)


def test_float_grammar_shape() -> None:
    """Exactly one digit before the point, at least one after, no '+' on the exponent,
    no leading zeros in the exponent."""
    for f in _random_doubles(20_000):
        text = encode_float(f)
        mantissa, _, exponent = text.partition("e")
        body = mantissa.lstrip("-")
        assert body.count(".") == 1
        head, tail = body.split(".")
        assert len(head) == 1 and head.isdigit()
        assert tail and tail.isdigit()
        assert "+" not in exponent
        digits = exponent.lstrip("-")
        assert digits.isdigit()
        assert digits == "0" or not digits.startswith("0")


def test_canonical_output_is_canonical() -> None:
    values = [
        {"b": 1, "a": [1.5, None, True], "": {}},
        [],
        {},
        {"kind": "undefined", "reason": "NO_CONFLICT_AREA"},
        {"nested": {"deep": {"deeper": [0.0, -1.0]}}},
    ]
    for v in values:
        assert is_canonical(canonicalize(v))


def test_key_insertion_order_does_not_matter() -> None:
    a = {"z": 1, "a": 2, "m": 3}
    b = {"m": 3, "z": 1, "a": 2}
    assert canonicalize(a) == canonicalize(b)


def test_array_order_does_matter() -> None:
    assert canonicalize([1, 2, 3]) != canonicalize([3, 2, 1])


def test_hash_preimage_is_domain_separated() -> None:
    pre = hash_input("evidence_row", {"v": 1})
    assert pre.startswith(b"ACS-1\x00evidence_row\x00")
    assert pre.count(b"\x00") == 2


def test_canonical_bytes_never_contain_nul() -> None:
    """What makes NUL a sound separator: control characters are escaped, so a raw NUL
    byte cannot appear inside canonical output and cannot be used to forge a boundary."""
    payload = canonicalize({"k": "\x00\x01"})
    assert b"\x00" not in payload
    assert payload == b'{"k":"\\u0000\\u0001"}'


def test_record_type_boundary_cannot_be_forged() -> None:
    """Without the NUL separators, a record type ending in a prefix of the payload
    could collide with a different (type, payload) split."""
    assert acs_sha256("ab", {"": 1}) != acs_sha256("a", {"b": 1})


# ------------------------------------------------------------- host-language traps


def test_bool_is_not_int() -> None:
    """`isinstance(True, int)` is true in Python. An encoder that checks int first
    emits `1` for `True` and collapses two distinct values into one digest."""
    assert canonicalize(True) == b"true"
    assert canonicalize(1) == b"1"
    assert acs_sha256("vector", True) != acs_sha256("vector", 1)


def test_non_string_key_rejected() -> None:
    with pytest.raises(AcsError) as exc:
        canonicalize({1: "a"})
    assert exc.value.code == "BAD_KEY_TYPE"


def test_unsupported_type_rejected() -> None:
    with pytest.raises(AcsError) as exc:
        canonicalize(b"bytes")
    assert exc.value.code == "UNSUPPORTED_TYPE"


def test_lone_surrogate_rejected() -> None:
    with pytest.raises(AcsError) as exc:
        canonicalize("\ud800")
    assert exc.value.code == "LONE_SURROGATE"


def test_stock_parser_would_have_accepted_the_duplicate() -> None:
    """Pins the reason `parse_strict` exists: the default parser is silent here."""
    assert json.loads('{"a":1,"a":2}') == {"a": 2}
    with pytest.raises(AcsError):
        parse_strict(b'{"a":1,"a":2}')
