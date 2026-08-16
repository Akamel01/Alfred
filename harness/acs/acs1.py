"""ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).

The canonical byte form of any structure whose hash is load-bearing: evidence-chain
rows and result stamps. Artifacts are hashed as stored bytes and never pass through
here.

The whole design exists so that a third party — an auditor recomputing the evidence
chain, in a language that is not Python — produces byte-identical output. Every rule
below is therefore stated as an algorithm with no appeal to a host language's
formatting defaults.

No third-party imports, deliberately: the encoder that guards the audit chain must not
depend on the supply chain the chain records.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from decimal import Decimal
from typing import Any

ACS_VERSION = "ACS-1"

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1

# Two-character escapes JSON defines. Every other control character below 0x20 is
# emitted as \u00xx with lowercase hex. Nothing else is ever escaped — not 0x7f,
# not '/', not any non-ASCII character.
_SHORT_ESCAPES = {
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0C: "\\f",
    0x0D: "\\r",
    0x22: '\\"',
    0x5C: "\\\\",
}


class AcsError(ValueError):
    """Base for every refusal. Each carries a stable code; the codes are part of the
    published test-vector suite, so an independent implementation can be checked on
    what it rejects and not merely on what it emits."""

    code = "ACS_ERROR"


class NotFinite(AcsError):
    code = "NOT_FINITE"


class IntOutOfRange(AcsError):
    code = "INT_OUT_OF_RANGE"


class DuplicateKey(AcsError):
    code = "DUPLICATE_KEY"


class BadKeyType(AcsError):
    code = "BAD_KEY_TYPE"


class UnsupportedType(AcsError):
    code = "UNSUPPORTED_TYPE"


class LoneSurrogate(AcsError):
    code = "LONE_SURROGATE"


# --------------------------------------------------------------------------- floats


def encode_float(value: float) -> str:
    """ACS-1 float grammar: normalized scientific, shortest round-tripping digits.

        sign? digit "." digit+ "e" "-"? exponent

    Always exactly one digit before the point, always at least one after, exponent
    with no leading zeros and no '+' sign. `1.0` is `"1.0e0"`, `100.0` is `"1.0e2"`,
    `2.4` is `"2.4e0"`, `1e-7` is `"1.0e-7"`.

    The presentation is pinned because "shortest round-trip" alone is not a
    specification: every correct implementation agrees on the *digits* and disagrees
    on the *formatting*. Python renders 1.0 as "1.0" and 1e16 as "1e+16"; JavaScript
    renders them "1" and "10000000000000000". Left to a host language's default, the
    string encoding would reintroduce the divergence it exists to remove.

    NaN and infinity are refused. Infinity is representable only through the tagged
    form of ADR-0001, and NaN is forbidden as an output anywhere in the system.
    """
    if value != value or value in (float("inf"), float("-inf")):
        raise NotFinite(f"float is not finite: {value!r}")

    if value == 0.0:
        return "0.0e0"  # also the normalization of -0.0

    sign, digits, exponent = Decimal(repr(value)).as_tuple()
    assert isinstance(exponent, int)

    # value == digits * 10**exponent, so in d.ddd * 10**e form:
    exp = (len(digits) - 1) + exponent

    # repr may carry trailing zeros that the shortest-digit form does not
    # (repr(100.0) == "100.0" -> digits (1,0,0,0)). Stripping them leaves `exp`
    # unchanged: dropping k trailing zeros shortens the digit string by k and raises
    # the decimal exponent by k, and exp is their sum.
    ds = "".join(str(d) for d in digits).rstrip("0") or "0"

    mantissa = ds[0] + "." + (ds[1:] or "0")
    return f"{'-' if sign else ''}{mantissa}e{exp}"


def decode_float(text: str) -> float:
    """Inverse of `encode_float`. Exact for every finite double."""
    return float(text)


# -------------------------------------------------------------------------- strings


def _normalize(text: str) -> str:
    """NFC. Composed and decomposed forms of the same string are visually identical
    and byte-different; without normalization they would hash differently."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # lone surrogate
        raise LoneSurrogate(f"string is not encodable as UTF-8: {exc}") from exc
    return unicodedata.normalize("NFC", text)


def _encode_string(text: str) -> str:
    out = ['"']
    for ch in text:
        cp = ord(ch)
        if cp in _SHORT_ESCAPES:
            out.append(_SHORT_ESCAPES[cp])
        elif cp < 0x20:
            out.append(f"\\u{cp:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


# --------------------------------------------------------------------------- encode


def _encode(value: Any) -> str:
    # bool before int: in Python `isinstance(True, int)` is true, so an unguarded
    # int branch would silently serialize True as 1 and collapse two distinct values.
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        if not INT64_MIN <= value <= INT64_MAX:
            raise IntOutOfRange(f"integer outside signed 64-bit range: {value}")
        return str(value)
    if isinstance(value, float):
        return _encode_string(encode_float(value))
    if isinstance(value, str):
        return _encode_string(_normalize(value))
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_encode(v) for v in value) + "]"
    if isinstance(value, dict):
        items: list[tuple[bytes, str, Any]] = []
        seen: set[bytes] = set()
        for raw_key, val in value.items():
            if not isinstance(raw_key, str):
                raise BadKeyType(f"object key is not a string: {raw_key!r}")
            key = _normalize(raw_key)
            kb = key.encode("utf-8")
            if kb in seen:
                # After normalization, because two keys differing only by composition
                # are the same key and must not both survive into the canonical form.
                raise DuplicateKey(f"duplicate object key after NFC: {key!r}")
            seen.add(kb)
            items.append((kb, key, val))
        items.sort(key=lambda it: it[0])
        body = ",".join(f"{_encode_string(k)}:{_encode(v)}" for _, k, v in items)
        return "{" + body + "}"
    raise UnsupportedType(f"type is not representable in ACS-1: {type(value).__name__}")


def canonicalize(value: Any) -> bytes:
    """The canonical UTF-8 bytes of `value`. No whitespace anywhere."""
    return _encode(value).encode("utf-8")


# ----------------------------------------------------------------------------- hash


def hash_input(record_type: str, value: Any) -> bytes:
    """Domain-separated preimage.

        ACS_VERSION 0x00 record_type 0x00 canonical_bytes

    The separators exist so a result stamp and an evidence row with coincidentally
    identical content cannot produce the same digest, and so the scheme version can
    change without silently reinterpreting existing digests.
    """
    if "\x00" in record_type:
        raise AcsError("record_type must not contain a NUL byte")
    return (
        ACS_VERSION.encode("utf-8")
        + b"\x00"
        + _normalize(record_type).encode("utf-8")
        + b"\x00"
        + canonicalize(value)
    )


def acs_sha256(record_type: str, value: Any) -> str:
    return hashlib.sha256(hash_input(record_type, value)).hexdigest()


# ---------------------------------------------------------------------------- parse


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [_normalize(k) for k, _ in pairs]
    if len(set(keys)) != len(keys):
        raise DuplicateKey(f"duplicate object key: {keys}")
    return dict(zip(keys, (v for _, v in pairs)))


def _reject_constant(token: str) -> Any:
    raise NotFinite(f"JSON constant not permitted in ACS-1: {token}")


def _reject_float(token: str) -> Any:
    # Canonical form carries floats as strings, so a JSON float literal cannot occur in
    # it. Accepting one here would let `parse_strict` succeed on input the encoder can
    # never produce.
    raise AcsError(f"ACS-1 numbers are integers; floats are carried as strings: {token}")


def _check_int(token: str) -> int:
    value = int(token)
    if not INT64_MIN <= value <= INT64_MAX:
        raise IntOutOfRange(f"integer outside signed 64-bit range: {token}")
    return value


def parse_strict(data: bytes) -> Any:
    """Parse ACS-1 bytes, refusing what the stock parser accepts silently: duplicate
    keys (which the default keeps last-wins with no error) and the non-standard
    `NaN` / `Infinity` literals.

    Floats come back as strings. Callers know from their schema which fields are
    floats; the canonical form deliberately does not carry that distinction, because
    a self-describing numeric type is what created the divergence in the first place.
    """
    return json.loads(
        data.decode("utf-8"),
        object_pairs_hook=_no_duplicates,
        parse_constant=_reject_constant,
        parse_float=_reject_float,
        parse_int=_check_int,
    )


def is_canonical(data: bytes) -> bool:
    """Whether `data` is already in canonical form — the check an auditor runs on a
    stored row before trusting its digest."""
    try:
        return canonicalize(parse_strict(data)) == data
    except (AcsError, ValueError, UnicodeDecodeError):
        return False
