"""Generate the ACS-1 test-vector suite (ADR-0003).

The vectors are the specification. ACS-1 is deliberately not a published standard, so
the thing that makes it implementable by a third party — and therefore auditable — is a
portable case file, not this prose.

Every input is described in a neutral tagged form that carries no host-language
formatting decisions: floats as their IEEE-754 bit pattern in hex, integers as decimal
strings, strings as UTF-8 hex — or, where UTF-8 cannot carry the case at all, as
UTF-16 code units under the `str16` tag. A file that described a float as `2.4` would
be asking the reader's JSON parser the very question ACS-1 exists to answer.

Seven sections, each a different question an implementation must answer the same way:
`encode` (canonical bytes and digest), `encode_errors` (what it must refuse), `hash`
and `hash_errors` (the record_type half of the preimage, which is hashed input too),
`parse` (what a reader must accept and reject), `canonical` and `non_canonical` (what
`is_canonical` must say about stored bytes).

How large each section needs to be is not a matter of taste: `harness/acs/mutate.py`
injects a deliberate defect for every rule here and requires the suite to fail at
least eight checks on each. Sections that look repetitive are sized by that control.

    python3 harness/acs/gen_vectors.py
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

from acs1 import ACS_VERSION, AcsError, acs_sha256, canonicalize, is_canonical

OUT = Path(__file__).resolve().parent / "vectors.json"


def f64(x: float) -> dict[str, str]:
    return {"t": "f64", "v": struct.pack(">d", x).hex()}


def bits(hexbits: str) -> dict[str, str]:
    return {"t": "f64", "v": hexbits}


def i64(x: int) -> dict[str, str]:
    return {"t": "i64", "v": str(x)}


def s(text: str) -> dict[str, str]:
    return {"t": "str", "v": text.encode("utf-8", "surrogatepass").hex()}


def s16(*units: int) -> dict[str, str]:
    """A string given as UTF-16 code units, big-endian hex.

    The `str` tag cannot carry a lone surrogate portably: its payload is UTF-8 hex,
    and a host that decodes those bytes strictly rejects the sequence while one that
    decodes leniently substitutes U+FFFD — so the vector would test the reader's
    decoder rather than ACS-1. Code units are unambiguous in every host, which is what
    lets the lone-surrogate refusal be a vector at all rather than a hand-written
    assertion in one implementation.
    """
    return {"t": "str16", "v": "".join(f"{u:04x}" for u in units)}


def arr(*items: Any) -> dict[str, Any]:
    return {"t": "arr", "v": list(items)}


def obj(*pairs: tuple[str, Any]) -> dict[str, Any]:
    return {"t": "obj", "v": [[k.encode("utf-8").hex(), v] for k, v in pairs]}


def dup_obj(key_a: str, key_b: str) -> dict[str, Any]:
    """An object literal with two keys that collide only after NFC. Written as raw
    node data rather than through `obj`, because the point of the case is that both
    keys reach the encoder — which no host container would allow if they were already
    equal."""
    return {"t": "obj", "v": [[key_a.encode("utf-8").hex(), {"t": "i64", "v": "1"}],
                              [key_b.encode("utf-8").hex(), {"t": "i64", "v": "2"}]]}


TRUE = {"t": "bool", "v": True}
FALSE = {"t": "bool", "v": False}
NULL = {"t": "null"}


def build(node: Any) -> Any:
    """Neutral node form -> Python value. An independent implementation reimplements
    this function against its own types; everything else in the file is data."""
    t = node["t"]
    if t == "null":
        return None
    if t == "bool":
        return node["v"]
    if t == "i64":
        return int(node["v"])
    if t == "f64":
        return struct.unpack(">d", bytes.fromhex(node["v"]))[0]
    if t == "str":
        return bytes.fromhex(node["v"]).decode("utf-8", "surrogatepass")
    if t == "str16":
        return bytes.fromhex(node["v"]).decode("utf-16-be", "surrogatepass")
    if t == "arr":
        return [build(v) for v in node["v"]]
    if t == "obj":
        return {bytes.fromhex(k).decode("utf-8"): build(v) for k, v in node["v"]}
    raise ValueError(f"unknown node tag: {t}")


# --------------------------------------------------------------------------- cases

NEG_ZERO = bits("8000000000000000")

# Every escape JSON gives a two-character form, in one string. A vector that carries
# all seven means a single wrong entry in an implementation's escape table shows up
# here as well as in the per-escape vectors below.
ALL_SHORT_ESCAPES = "\b\t\n\f\r\"\\"

# The control characters that have no two-character form and are therefore emitted as
# \u00xx with lowercase hex: everything below 0x20 except the five above.
CTRL_NO_SHORT_FORM = "".join(
    chr(c) for c in range(0x20) if c not in (0x08, 0x09, 0x0A, 0x0C, 0x0D)
)

INT64_MAX_N = 2**63 - 1
INT64_MIN_N = -(2**63)

CASES: list[tuple[str, str, str, Any]] = [
    # (id, note, record_type, node)
    # ---- float grammar: the presentation is pinned, not inherited from a host language
    ("f-one", "1.0 is 1.0e0, never \"1\"", "vector", f64(1.0)),
    ("f-neg-one", "sign precedes the mantissa", "vector", f64(-1.0)),
    ("f-zero", "positive zero", "vector", f64(0.0)),
    ("f-neg-zero", "-0.0 normalizes to 0.0e0; hash equals f-zero", "vector", bits("8000000000000000")),
    ("f-2p4", "the oracle's TTC value", "vector", f64(2.4)),
    ("f-hundred", "100.0 is 1.0e2, never \"100\"", "vector", f64(100.0)),
    ("f-1e16", "python renders 1e+16, JS renders 10000000000000000", "vector", f64(1e16)),
    ("f-1e21", "above the JS fixed/exponential threshold", "vector", f64(1e21)),
    ("f-1e-7", "python renders 1e-07, JS renders 1e-7", "vector", f64(1e-7)),
    ("f-point3", "0.1+0.2, the 17-digit case", "vector", f64(0.1 + 0.2)),
    ("f-min-subnormal", "smallest positive double", "vector", bits("0000000000000001")),
    ("f-neg-min-subnormal", "smallest negative double", "vector", bits("8000000000000001")),
    ("f-max", "largest finite double", "vector", bits("7fefffffffffffff")),
    ("f-min-normal", "smallest positive normal", "vector", bits("0010000000000000")),
    ("f-10p5", "mantissa longer than one digit", "vector", f64(10.5)),
    ("f-third", "1/3", "vector", f64(1 / 3)),
    # ---- integers
    ("i-zero", "", "vector", i64(0)),
    ("i-one", "", "vector", i64(1)),
    ("i-neg-one", "", "vector", i64(-1)),
    ("i-max", "int64 max, emitted as a JSON number", "vector", i64(2**63 - 1)),
    ("i-min", "int64 min", "vector", i64(-(2**63))),
    # ---- strings
    ("s-empty", "", "vector", s("")),
    ("s-ascii", "", "vector", s("hello")),
    ("s-nfc", "composed cafe", "vector", s("café")),
    ("s-nfd", "decomposed cafe; canonical output equals s-nfc", "vector", s("café")),
    ("s-astral", "outside the BMP", "vector", s("\U0001f600")),
    ("s-controls", "u0000, u0001, u001f as \\u00xx lowercase", "vector", s("\x00\x01\x1f")),
    ("s-short-escapes", "backspace tab newline formfeed return", "vector", s("\b\t\n\f\r")),
    ("s-quote-backslash", "the two mandatory escapes", "vector", s('"\\')),
    ("s-del", "0x7f is NOT escaped", "vector", s("\x7f")),
    ("s-slash", "forward slash is NOT escaped", "vector", s("a/b")),
    ("s-nonascii-raw", "emitted raw UTF-8, never \\uXXXX", "vector", s("é中")),
    # ---- containers and key ordering
    ("o-empty", "", "vector", obj()),
    ("a-empty", "", "vector", arr()),
    ("a-order", "arrays keep input order; they are never sorted", "vector", arr(i64(3), i64(1), i64(2))),
    ("o-sort-ascii", "keys sort by UTF-8 bytes: digits, uppercase, lowercase", "vector",
     obj(("b", i64(1)), ("a", i64(2)), ("A", i64(3)), ("0", i64(4)))),
    ("o-sort-utf16-divergence",
     "the case where UTF-8 byte order and UTF-16 code-unit order disagree: RFC 8785 "
     "would order the astral character before the fullwidth one",
     "vector", obj(("z", i64(1)), ("Ｚ", i64(2)), ("\U0001f600", i64(3)))),
    ("o-empty-key", "the empty string is a legal key and sorts first", "vector",
     obj(("", i64(1)), ("a", i64(2)))),
    ("o-key-nfd", "a decomposed KEY normalizes and sorts by its composed bytes", "vector",
     obj(("cafe\u0301", i64(1)), ("cafz", i64(2)))),
    ("o-key-nfd-equals-nfc", "canonical output equals o-key-nfd", "vector",
     obj(("café", i64(1)), ("cafz", i64(2)))),
    ("s-nfd-nested", "normalization applies at every depth, not only at the top", "vector",
     arr(obj(("k", s("cafe\u0301"))), s("A\u030a"))),
    ("s-nfd-nested-composed", "canonical output equals s-nfd-nested", "vector",
     arr(obj(("k", s("café"))), s("Å"))),
    ("o-sort-prefix", "a key that is a prefix of another sorts first", "vector",
     obj(("ab", i64(1)), ("a", i64(2)), ("abc", i64(3)))),
    ("o-sort-multibyte", "two-byte and three-byte UTF-8 keys against ASCII", "vector",
     obj(("é", i64(1)), ("z", i64(2)), ("中", i64(3)), ("~", i64(4)))),
    ("o-sort-case", "uppercase sorts before lowercase by byte value", "vector",
     obj(("b", i64(1)), ("B", i64(2)), ("a", i64(3)), ("A", i64(4)))),
    ("o-nested", "", "vector",
     obj(("outer", obj(("b", arr(f64(1.5), NULL)), ("a", TRUE))))),
    ("b-true", "", "vector", TRUE),
    ("b-false", "", "vector", FALSE),
    ("n-null", "", "vector", NULL),
    ("b-vs-int", "true is not 1; the encoder must test bool before int", "vector",
     obj(("t", TRUE), ("i", i64(1)))),
    # ---- the ADR-0001 tagged metric value, which is why any of this exists
    ("mv-defined", "MetricValue: defined", "result_stamp",
     obj(("kind", s("defined")), ("value", f64(2.4)))),
    ("mv-infinite-pos", "MetricValue: +inf, which cannot be a JSON number", "result_stamp",
     obj(("kind", s("infinite")), ("sign", s("+")))),
    ("mv-infinite-neg", "MetricValue: -inf", "result_stamp",
     obj(("kind", s("infinite")), ("sign", s("-")))),
    ("mv-undefined", "MetricValue: undefined carries the reason name, not the integer",
     "result_stamp", obj(("kind", s("undefined")), ("reason", s("NO_CONFLICT_AREA")))),
    # ---- domain separation: identical content, different record_type
    ("sep-evidence", "same content as sep-result; digests must differ", "evidence_row",
     obj(("v", i64(1)))),
    ("sep-result", "same content as sep-evidence; digests must differ", "result_stamp",
     obj(("v", i64(1)))),

    # ================================================================= widened set
    # Everything below was added to give the mutation control (harness/acs/mutate.py)
    # a margin: each deliberate defect must fail at least eight checks, and several
    # rules above were resting on one or two vectors. The grouping is by the rule
    # being pinned, not by type.

    # ---- -0.0 normalizes wherever it appears, not only at the top level
    ("f-neg-zero-in-array", "-0.0 inside an array", "vector", arr(NEG_ZERO, f64(1.0))),
    ("f-neg-zero-in-object", "-0.0 as an object value", "vector",
     obj(("z", NEG_ZERO), ("a", f64(-1.0)))),
    ("f-neg-zero-deep", "-0.0 three levels down", "vector",
     obj(("o", arr(obj(("n", NEG_ZERO)))))),

    # ---- more of the float grammar: exponent width, digit count, mantissa shape
    ("f-two", "2.0 is 2.0e0", "vector", f64(2.0)),
    ("f-hundredth", "0.01 is 1.0e-2", "vector", f64(0.01)),
    ("f-1e100", "a three-digit exponent", "vector", f64(1e100)),
    ("f-1e-300", "a three-digit negative exponent", "vector", f64(1e-300)),
    ("f-17-digits", "seventeen significant digits", "vector", f64(1.2345678901234567)),
    ("f-nested-mixed", "floats at three depths in one structure", "vector",
     obj(("a", arr(f64(1.0), f64(-1.0))), ("b", obj(("c", f64(1e16)))))),

    # ---- the seven short escapes, one vector each plus three that carry all of them
    ("s-esc-backspace", "0x08 is \\b, never \\u0008", "vector", s("\b")),
    ("s-esc-tab", "0x09 is \\t", "vector", s("\t")),
    ("s-esc-newline", "0x0a is \\n", "vector", s("\n")),
    ("s-esc-formfeed", "0x0c is \\f", "vector", s("\f")),
    ("s-esc-return", "0x0d is \\r", "vector", s("\r")),
    ("s-esc-all", "all seven two-character escapes in one string", "vector",
     s(ALL_SHORT_ESCAPES)),
    ("o-esc-in-key", "the escapes apply to keys exactly as to values", "vector",
     obj((ALL_SHORT_ESCAPES, i64(1)), ("a", i64(2)))),
    ("a-esc-nested", "escapes at depth", "vector",
     arr(obj(("k", s(ALL_SHORT_ESCAPES))), s(ALL_SHORT_ESCAPES))),

    # ---- control characters with no short form: \u00xx, lowercase hex
    ("s-control-vertical-tab", "0x0b has no two-character form", "vector", s("\x0b")),
    ("s-control-1e", "0x1e, a hex digit above 9 in the escape", "vector", s("\x1e")),
    ("s-control-all", "every control character that has no short form", "vector",
     s(CTRL_NO_SHORT_FORM)),
    ("o-control-in-key", "control escapes in a key", "vector",
     obj(("\x01\x1f", i64(1)), ("a", i64(2)))),
    ("a-control-nested", "control escapes at depth", "vector",
     arr(obj(("k", s("\x00"))), s("\x1f"))),

    # ---- characters an over-eager escaper would escape and ACS-1 does not
    ("o-del-in-key", "0x7f is not escaped in a key either", "vector",
     obj(("\x7f", i64(1)), ("a", i64(2)))),
    ("a-del-nested", "0x7f at depth", "vector", arr(obj(("k", s("\x7f"))), s("a\x7fb"))),
    ("s-del-mixed", "0x7f between printable characters", "vector", s("a\x7fb")),
    ("o-slash-in-key", "forward slash is not escaped in a key", "vector",
     obj(("a/b", i64(1)), ("a", i64(2)))),
    ("a-slash-nested", "forward slash at depth", "vector",
     arr(obj(("p/q", s("x/y"))), s("/"))),
    ("s-slash-only", "a string that is one solidus", "vector", s("/")),

    # ---- NFC is not NFKC: compatibility characters must survive unchanged
    ("s-nfkc-fullwidth", "fullwidth Z is NOT folded to Z; NFC is not NFKC", "vector",
     s("Ｚ")),
    ("s-nfkc-ligature", "the fi ligature is not decomposed under NFC", "vector", s("ﬁ")),
    ("s-nfkc-superscript", "superscript two is not folded to 2", "vector", s("²")),
    ("o-nfkc-key", "a compatibility character as a key", "vector",
     obj(("ﬁle", i64(1)), ("a", i64(2)))),
    ("a-nfkc-nested", "compatibility characters at depth", "vector",
     arr(obj(("k", s("Ｚ"))), s("²"))),

    # ---- keys that differ only past a common prefix
    ("o-sort-long-common-prefix",
     "keys identical for fifteen bytes; the comparison must not stop early", "vector",
     obj(("alpha/beta/gamma/y", i64(1)), ("alpha/beta/gamma", i64(2)),
         ("alpha/beta/gamma/x", i64(3)))),
    ("o-sort-prefix-multibyte", "a prefix boundary in the middle of a UTF-8 sequence",
     "vector", obj(("café", i64(1)), ("caf", i64(2)), ("café-x", i64(3)))),
    ("o-sort-last-byte", "keys differing only in their final byte", "vector",
     obj(("aaaz", i64(1)), ("aaab", i64(2)), ("aaaa", i64(3)))),
    ("o-sort-prefix-nested", "prefix keys at depth", "vector",
     obj(("outer", obj(("kk", i64(1)), ("k", i64(2)), ("kkk", i64(3)))))),

    # ---- int64 boundaries, at depth as well as at the top
    ("a-i64-bounds", "both boundary integers in an array", "vector",
     arr(i64(INT64_MAX_N), i64(INT64_MIN_N))),
    ("o-i64-bounds", "both boundary integers as object values", "vector",
     obj(("max", i64(INT64_MAX_N)), ("min", i64(INT64_MIN_N)))),
    ("o-i64-bounds-deep", "boundary integers three levels down", "vector",
     obj(("a", obj(("b", arr(i64(INT64_MAX_N), i64(INT64_MIN_N)))))),),
    ("i-max-minus-one", "one inside the upper boundary", "vector", i64(INT64_MAX_N - 1)),
    ("i-min-plus-one", "one inside the lower boundary", "vector", i64(INT64_MIN_N + 1)),

    # ---- booleans, which a host that tests int before bool collapses into 0 and 1
    ("a-bools", "booleans in an array are not 1 and 0", "vector",
     arr(TRUE, FALSE, i64(1), i64(0))),
    ("o-bools", "booleans as object values", "vector",
     obj(("t", TRUE), ("f", FALSE), ("one", i64(1)), ("zero", i64(0)))),
    ("o-bools-deep", "booleans at depth", "vector",
     obj(("a", arr(obj(("t", TRUE), ("i", i64(1))), FALSE)))),

    # ---- empty containers, alone and as members
    ("o-empty-nested", "an empty object as a value", "vector", obj(("a", obj()))),
    ("a-empty-nested", "an empty array as a value", "vector", obj(("a", arr()))),
    ("a-of-empties", "empty containers as array members", "vector", arr(arr(), obj())),
    ("o-empty-key-and-value", "the empty key with an empty-string value", "vector",
     obj(("", s("")), ("a", arr(obj())))),

    # ---- one deep structure that exercises every rule at once
    ("deep-mixed",
     "ten levels, each carrying a rule: ordering, escapes, NFC, floats, bounds",
     "evidence_row",
     obj(("z", i64(1)),
         ("a", obj(("k\tk", arr(
             f64(2.4),
             obj(("é", obj(("", arr(
                 NEG_ZERO,
                 obj(("café", arr(TRUE, NULL, i64(INT64_MIN_N),
                                        obj(("deepest", s("\x00/\x7f")))))),
             ))))),
             i64(INT64_MAX_N),
         )))))),

    # ---- UTF-8 byte order against UTF-16 code-unit order. Any BMP character at or
    # above U+E000 sorts after an astral character under UTF-16 (whose leading
    # surrogate is at most 0xdbff) and before it under UTF-8 (three bytes beginning
    # ee or ef, against four beginning f0). Every pair below is such a pair; RFC 8785
    # orders each of them the other way round.
    ("o-sort-astral-vs-private-use", "astral against U+E000", "vector",
     obj(("\U0001f600", i64(1)), ("\ue000", i64(2)))),
    ("o-sort-astral-vs-fullwidth-a", "astral against U+FF21", "vector",
     obj(("\U0001d400", i64(1)), ("\uff21", i64(2)))),
    ("o-sort-astral-vs-cjk-compat", "astral against a CJK compatibility ideograph",
     "vector", obj(("\U00020000", i64(1)), ("\ufa0e", i64(2)))),
    ("o-sort-astral-vs-arabic-form", "astral against an Arabic presentation form",
     "vector", obj(("\U0001f4a9", i64(1)), ("\ufb50", i64(2)))),
    ("o-sort-two-astrals-one-bmp", "two astral keys around one high BMP key", "vector",
     obj(("\U0001f600", i64(1)), ("\uffe0", i64(2)), ("\U00010000", i64(3)))),
    ("o-sort-astral-and-ascii", "astral, high BMP and ASCII keys together", "vector",
     obj(("\U0001f600", i64(1)), ("\uff3a", i64(2)), ("z", i64(3)), ("a", i64(4)))),
    ("o-sort-astral-shared-suffix", "the divergent keys share a trailing character",
     "vector", obj(("\U0001f600a", i64(1)), ("\uff3aa", i64(2)))),
    ("o-sort-astral-deep", "the divergence three levels down", "vector",
     obj(("outer", arr(obj(("\U0001f600", i64(1)), ("\ue001", i64(2))))))),

    # ---- keys that share a first byte and a length, so a comparison that stops
    # early or falls back to length ordering cannot get them right by accident
    ("o-sort-same-first-byte", "three keys beginning 'a', all the same length",
     "vector", obj(("azz", i64(1)), ("aay", i64(2)), ("abx", i64(3)))),
    ("o-sort-same-first-byte-b", "three keys beginning 'b', all the same length",
     "vector", obj(("bzz", i64(1)), ("byy", i64(2)), ("bxx", i64(3)))),
    ("o-sort-same-first-byte-multibyte",
     "three keys sharing a two-byte first character", "vector",
     obj(("\u00e9z", i64(1)), ("\u00e9a", i64(2)), ("\u00e9b", i64(3)))),
    ("o-sort-same-first-byte-long",
     "twenty-byte keys differing only in the last", "vector",
     obj(("x" * 19 + "c", i64(1)), ("x" * 19 + "a", i64(2)), ("x" * 19 + "b", i64(3)))),
    ("o-sort-same-first-byte-astral",
     "two astral keys sharing three of their four bytes", "vector",
     obj(("\U0001f601", i64(1)), ("\U0001f600", i64(2)))),
    ("o-sort-same-first-byte-deep", "the same, three levels down", "vector",
     obj(("outer", arr(obj(("azz", i64(1)), ("aay", i64(2)), ("aax", i64(3))))))),

    # ---- -0.0 wherever it can occur
    ("f-neg-zero-among-floats", "-0.0 between two other floats", "vector",
     arr(f64(1.0), NEG_ZERO, f64(2.0))),
    ("f-neg-zero-both-zeros", "both zeros in one array; they must become one form",
     "vector", arr(f64(0.0), NEG_ZERO)),
    ("f-neg-zero-nested-array", "-0.0 inside an array inside an array", "vector",
     arr(arr(NEG_ZERO))),
    ("f-neg-zero-object-of-floats", "-0.0 among other float values", "vector",
     obj(("a", f64(1.5)), ("b", NEG_ZERO), ("c", f64(-1.5)))),
    ("f-neg-zero-key-and-value", "-0.0 under a key that sorts last", "vector",
     obj(("a", i64(1)), ("zz", NEG_ZERO))),

    # ---- int64 boundaries in more positions
    ("o-i64-max-only", "int64 max as the only value", "vector",
     obj(("v", i64(INT64_MAX_N)))),
    ("o-i64-min-only", "int64 min as the only value", "vector",
     obj(("v", i64(INT64_MIN_N)))),
    ("a-i64-max-among-many", "int64 max among ordinary integers", "vector",
     arr(i64(0), i64(1), i64(INT64_MAX_N), i64(-1))),
    ("a-i64-min-among-many", "int64 min among ordinary integers", "vector",
     arr(i64(0), i64(1), i64(INT64_MIN_N), i64(-1))),
    ("o-i64-bounds-mixed", "boundary integers beside floats and strings", "vector",
     obj(("f", f64(1.0)), ("i", i64(INT64_MAX_N)), ("j", i64(INT64_MIN_N)),
         ("s", s("x")))),

    # ---- 0x7f, which is not a control character for JSON's purposes
    ("s-del-repeated", "several DEL characters", "vector", s("\x7f\x7f\x7f")),
    ("o-del-only-key", "a key that is one DEL", "vector",
     obj(("\x7f", i64(1)))),
    ("a-del-among-strings", "DEL beside ordinary strings", "vector",
     arr(s("a"), s("\x7f"), s("b"))),

    # ---- NFC is not NFKC: more compatibility characters that folding would destroy
    ("s-nfkc-roman-numeral", "U+216B is not folded to XII", "vector", s("\u216b")),
    ("s-nfkc-circled-digit", "U+2460 is not folded to 1", "vector", s("\u2460")),
    ("s-nfkc-nbsp", "a no-break space is not folded to a space", "vector", s("\u00a0")),
    ("s-nfkc-fraction", "U+00BD is not folded to 1/2", "vector", s("\u00bd")),
    ("o-nfkc-key-superscript", "a compatibility character as a key", "vector",
     obj(("\u00b2", i64(1)), ("a", i64(2)))),
    ("a-nfkc-deep", "compatibility characters three levels down", "vector",
     obj(("o", arr(obj(("k", s("\u216b\u2460"))))))),

    # ---- a little more slack on the escapes and control characters, so that a
    # future vector removed for looking redundant does not put a mutant back under
    # the threshold
    ("s-esc-tab-between-text", "tabs between printable characters", "vector",
     s("a\tb\tc")),
    ("o-esc-tab-key", "a tab inside a key", "vector",
     obj(("k\tk", i64(1)), ("a", i64(2)))),
    ("a-esc-newline-deep", "a newline three levels down", "vector",
     obj(("o", arr(obj(("k", s("line\nline"))))))),
    ("s-control-with-text", "control characters between printable ones", "vector",
     s("a\x01b\x1fc")),
    ("o-control-deep", "a control character in a key three levels down", "vector",
     obj(("o", arr(obj(("\x02", i64(1)), ("a", i64(2))))))),
    # ================================================ ADR-0006: the v1 result stamp
    # The ten-key shape, its three upstream arms, the configuration document the
    # `simulated` arm's digest commits to, and the record that wraps a value in one.
    #
    # Written out here in the neutral tagged form and importing nothing from `src`,
    # deliberately: this file is the published specification a third party audits
    # against (ADR-0004), and a specification generated from the implementation it
    # specifies states nothing. The coupling in the other direction — that
    # `ResultStampV1.to_acs()` really produces these bytes — is asserted by a bridge
    # test in `tests/`, which may import both trees.
    #
    # The record types here are the real domain-separation tags rather than the short
    # names used above, so a reader can recompute a live stamp digest from this file.
    ("stamp-v1-corpus", "the ten-key v1 stamp; upstream is the corpus arm",
     "alfred.result_stamp",
     obj(("acs_version", s("ACS-1")),
         ("assumption_set", obj(("entries", obj(("extrapolation", s("constant_velocity")),
                                                ("horizon_s", f64(10.0)))),
                                ("name", s("baseline")),
                                ("version", s("1.0.0")))),
         ("code_commit", s("0" * 39 + "a")),
         ("input_hash", s("1" * 64)),
         ("metric_id", s("ttc")),
         ("metric_version", s("1.0.0")),
         ("reason_codebook_version", i64(1)),
         ("stamp_schema_version", i64(1)),
         ("tolerance", obj(("atol", f64(1e-9)), ("rtol", f64(1e-6)))),
         ("upstream", obj(("corpus_digest", s("2" * 64)),
                          ("corpus_name", s("CommonRoad")),
                          ("corpus_version", s("2020a")),
                          ("kind", s("corpus")),
                          ("scenario_id", s("ZAM_Urban-7_1_S-2")))))),
    ("stamp-v1-simulated-minimal",
     "the simulated arm with both optional fields absent; absent is not null",
     "alfred.result_stamp",
     obj(("acs_version", s("ACS-1")),
         ("assumption_set", obj(("entries", obj()),
                                ("name", s("baseline")),
                                ("version", s("1.0.0")))),
         ("code_commit", s("0" * 39 + "a")),
         ("input_hash", s("1" * 64)),
         ("metric_id", s("ttc")),
         ("metric_version", s("1.0.0")),
         ("reason_codebook_version", i64(1)),
         ("stamp_schema_version", i64(1)),
         ("tolerance", obj(("atol", f64(1e-9)), ("rtol", f64(1e-6)))),
         ("upstream", obj(("config_digest", s("3" * 64)),
                          ("kind", s("simulated")),
                          ("tool_name", s("ExampleSim")),
                          ("tool_version", s("2024 R2")))))),
    ("stamp-v1-simulated-full",
     "the simulated arm with tool_build and config_ref present; a vendor version is "
     "free-form and is deliberately not semverish",
     "alfred.result_stamp",
     obj(("acs_version", s("ACS-1")),
         ("assumption_set", obj(("entries", obj()),
                                ("name", s("baseline")),
                                ("version", s("1.0.0")))),
         ("code_commit", s("0" * 39 + "a")),
         ("input_hash", s("1" * 64)),
         ("metric_id", s("ttc")),
         ("metric_version", s("1.0.0")),
         ("reason_codebook_version", i64(1)),
         ("stamp_schema_version", i64(1)),
         ("tolerance", obj(("atol", f64(1e-9)), ("rtol", f64(1e-6)))),
         ("upstream", obj(("config_digest", s("3" * 64)),
                          ("config_ref", s("s3://alfred-configs/run-41.yaml")),
                          ("kind", s("simulated")),
                          ("tool_build", s("7.3.0-hotfix4")),
                          ("tool_name", s("ExampleSim")),
                          ("tool_version", s("2024 R2")))))),
    ("stamp-v1-unknown",
     "the unknown arm carries a mandatory reason by NAME, never an ordinal; a stamp "
     "in this shape does not discharge the buyer's storage duty",
     "alfred.result_stamp",
     obj(("acs_version", s("ACS-1")),
         ("assumption_set", obj(("entries", obj()),
                                ("name", s("baseline")),
                                ("version", s("1.0.0")))),
         ("code_commit", s("0" * 39 + "a")),
         ("input_hash", s("1" * 64)),
         ("metric_id", s("ttc")),
         ("metric_version", s("1.0.0")),
         ("reason_codebook_version", i64(1)),
         ("stamp_schema_version", i64(1)),
         ("tolerance", obj(("atol", f64(1e-9)), ("rtol", f64(1e-6)))),
         ("upstream", obj(("kind", s("unknown")),
                          ("reason", s("UPSTREAM_NOT_RECORDED")))))),
    ("upstream-config-v1",
     "the configuration document the simulated arm's config_digest commits to, under "
     "its own record type: the digest commits, the config_ref retrieves",
     "alfred.upstream_config",
     obj(("scenario", s("urban-crossing")),
         ("seed", i64(4242)),
         ("solver", obj(("dt", f64(0.1)), ("name", s("rk4")))))),
    ("stamped-result-v1-defined",
     "a stamped result carries no version of its own: the nested stamp's "
     "stamp_schema_version is inside this preimage (ADR-0016)",
     "alfred.stamped_result",
     obj(("stamp", obj(("acs_version", s("ACS-1")),
                       ("assumption_set", obj(("entries", obj()),
                                              ("name", s("baseline")),
                                              ("version", s("1.0.0")))),
                       ("code_commit", s("0" * 39 + "a")),
                       ("input_hash", s("1" * 64)),
                       ("metric_id", s("ttc")),
                       ("metric_version", s("1.0.0")),
                       ("reason_codebook_version", i64(1)),
                       ("stamp_schema_version", i64(1)),
                       ("tolerance", obj(("atol", f64(1e-9)), ("rtol", f64(1e-6)))),
                       ("upstream", obj(("corpus_digest", s("2" * 64)),
                                        ("corpus_name", s("CommonRoad")),
                                        ("corpus_version", s("2020a")),
                                        ("kind", s("corpus")),
                                        ("scenario_id", s("ZAM_Urban-7_1_S-2")))))),
         ("value", obj(("kind", s("defined")), ("value", f64(2.4)))))),
    ("stamped-result-v1-undefined",
     "the same record wrapping an undefined value, which is why the tagged form exists",
     "alfred.stamped_result",
     obj(("stamp", obj(("acs_version", s("ACS-1")),
                       ("assumption_set", obj(("entries", obj()),
                                              ("name", s("baseline")),
                                              ("version", s("1.0.0")))),
                       ("code_commit", s("0" * 39 + "a")),
                       ("input_hash", s("1" * 64)),
                       ("metric_id", s("ttc")),
                       ("metric_version", s("1.0.0")),
                       ("reason_codebook_version", i64(1)),
                       ("stamp_schema_version", i64(1)),
                       ("tolerance", obj(("atol", f64(1e-9)), ("rtol", f64(1e-6)))),
                       ("upstream", obj(("corpus_digest", s("2" * 64)),
                                        ("corpus_name", s("CommonRoad")),
                                        ("corpus_version", s("2020a")),
                                        ("kind", s("corpus")),
                                        ("scenario_id", s("ZAM_Urban-7_1_S-2")))))),
         ("value", obj(("kind", s("undefined")), ("reason", s("NO_CONFLICT_AREA")))))),
]

ERROR_CASES: list[tuple[str, str, Any, str]] = [
    ("e-nan", "NaN is forbidden as an output anywhere", bits("7ff8000000000000"), "NOT_FINITE"),
    ("e-inf", "infinity must use the tagged form, never a raw float", bits("7ff0000000000000"), "NOT_FINITE"),
    ("e-neg-inf", "", bits("fff0000000000000"), "NOT_FINITE"),
    ("e-int-too-big", "int64 max + 1", i64(2**63), "INT_OUT_OF_RANGE"),
    ("e-int-too-small", "int64 min - 1", i64(-(2**63) - 1), "INT_OUT_OF_RANGE"),
    ("e-dup-key-nfc",
     "two keys identical after NFC are one key; both must not survive",
     {"t": "obj", "v": [["café".encode().hex(), {"t": "i64", "v": "1"}],
                        ["café".encode().hex(), {"t": "i64", "v": "2"}]]},
     "DUPLICATE_KEY"),
    ("e-dup-key-nfd-nested",
     "duplicate detection applies at every depth, not only at the top",
     {"t": "obj", "v": [["outer".encode().hex(),
                         {"t": "obj", "v": [["Å".encode().hex(), {"t": "i64", "v": "1"}],
                                            ["Å".encode().hex(), {"t": "i64", "v": "2"}]]}]]},
     "DUPLICATE_KEY"),
    ("e-dup-key-astral",
     "an astral key duplicated by composition-insensitive comparison",
     {"t": "obj", "v": [["\U0001f600Å".encode().hex(), {"t": "i64", "v": "1"}],
                        ["\U0001f600Å".encode().hex(), {"t": "i64", "v": "2"}]]},
     "DUPLICATE_KEY"),

    # ================================================================= widened set
    # ---- duplicate keys. Every case collides only *after* NFC, because a key
    # duplicated byte for byte cannot reach an encoder through a host container (see
    # the note below the list); those cases are parse-side.
    ("e-dup-key-nfd-first", "the decomposed form first; order must not matter",
     dup_obj("cafe\u0301", "caf\u00e9"), "DUPLICATE_KEY"),
    ("e-dup-key-angstrom-sign",
     "U+212B ANGSTROM SIGN and U+00C5 are one key after NFC",
     dup_obj("\u212b", "\u00c5"), "DUPLICATE_KEY"),
    ("e-dup-key-long-prefix",
     "the collision is sixteen bytes into two otherwise identical keys",
     dup_obj("alpha/beta/gamma/caf\u00e9", "alpha/beta/gamma/cafe\u0301"),
     "DUPLICATE_KEY"),
    ("e-dup-key-among-others",
     "a colliding pair surrounded by distinct keys",
     {"t": "obj", "v": [["a".encode().hex(), {"t": "i64", "v": "0"}],
                        ["\u00f4".encode().hex(), {"t": "i64", "v": "1"}],
                        ["m".encode().hex(), {"t": "i64", "v": "2"}],
                        ["o\u0302".encode().hex(), {"t": "i64", "v": "3"}],
                        ["z".encode().hex(), {"t": "i64", "v": "4"}]]},
     "DUPLICATE_KEY"),
    ("e-dup-key-in-array", "a duplicate inside an object inside an array",
     arr(i64(1), dup_obj("\u00f1", "n\u0303")), "DUPLICATE_KEY"),
    ("e-dup-key-deep",
     "a duplicate four levels down; detection is not a top-level pass",
     obj(("a", arr(obj(("b", dup_obj("\u00fc", "u\u0308")))))), "DUPLICATE_KEY"),
    ("e-dup-key-astral-prefix",
     "an astral character before the colliding portion",
     dup_obj("\U0001f4a9caf\u00e9", "\U0001f4a9cafe\u0301"), "DUPLICATE_KEY"),
    ("e-dup-key-two-collisions",
     "two independent colliding pairs in one object",
     {"t": "obj", "v": [["\u00e9".encode().hex(), {"t": "i64", "v": "1"}],
                        ["\u00f4".encode().hex(), {"t": "i64", "v": "2"}],
                        ["e\u0301".encode().hex(), {"t": "i64", "v": "3"}],
                        ["o\u0302".encode().hex(), {"t": "i64", "v": "4"}]]},
     "DUPLICATE_KEY"),

    # ---- lone surrogates, given as UTF-16 code units. UTF-8 hex cannot carry them
    # without asking the reader's decoder the question the vector exists to settle.
    ("e-surrogate-high-alone", "an unpaired high surrogate", s16(0xD800), "LONE_SURROGATE"),
    ("e-surrogate-low-alone", "an unpaired low surrogate", s16(0xDC00), "LONE_SURROGATE"),
    ("e-surrogate-high-max", "the last high surrogate, unpaired", s16(0xDBFF), "LONE_SURROGATE"),
    ("e-surrogate-low-max", "the last low surrogate, unpaired", s16(0xDFFF), "LONE_SURROGATE"),
    ("e-surrogate-reversed-pair",
     "low then high: a pair in the wrong order is two lone surrogates",
     s16(0xDC00, 0xD800), "LONE_SURROGATE"),
    ("e-surrogate-high-then-ascii", "a high surrogate followed by a non-surrogate",
     s16(0xD83D, 0x0041), "LONE_SURROGATE"),
    ("e-surrogate-trailing-high", "a high surrogate at the end of a string",
     s16(0x0041, 0x0042, 0xD83D), "LONE_SURROGATE"),
    ("e-surrogate-two-highs", "two high surrogates in a row",
     s16(0xD800, 0xD800), "LONE_SURROGATE"),
    ("e-surrogate-in-array", "a lone surrogate inside an array",
     arr(s("ok"), s16(0xD800)), "LONE_SURROGATE"),
    ("e-surrogate-deep", "a lone surrogate three levels down",
     obj(("a", arr(obj(("b", s16(0xDC00)))))), "LONE_SURROGATE"),
    ("e-surrogate-after-valid-pair",
     "a well-formed pair then an unpaired one; the check must scan the whole string",
     s16(0xD83D, 0xDE00, 0xD83D), "LONE_SURROGATE"),

    # ---- int64 boundaries, exactly one past the limit and at every depth. An encoder
    # whose bound is off by one accepts precisely these values and nothing wider.
    ("e-int-too-big-in-array", "int64 max + 1 in an array",
     arr(i64(1), i64(2**63)), "INT_OUT_OF_RANGE"),
    ("e-int-too-small-in-array", "int64 min - 1 in an array",
     arr(i64(1), i64(-(2**63) - 1)), "INT_OUT_OF_RANGE"),
    ("e-int-too-big-in-object", "int64 max + 1 as an object value",
     obj(("a", i64(2**63))), "INT_OUT_OF_RANGE"),
    ("e-int-too-small-in-object", "int64 min - 1 as an object value",
     obj(("a", i64(-(2**63) - 1))), "INT_OUT_OF_RANGE"),
    ("e-int-too-big-deep", "int64 max + 1 four levels down",
     obj(("a", arr(obj(("b", arr(i64(2**63))))))), "INT_OUT_OF_RANGE"),
    ("e-int-too-small-deep", "int64 min - 1 four levels down",
     obj(("a", arr(obj(("b", arr(i64(-(2**63) - 1))))))), "INT_OUT_OF_RANGE"),
    ("e-int-uint64-max", "2^64 - 1, the unsigned boundary a wider host might allow",
     i64(2**64 - 1), "INT_OUT_OF_RANGE"),
    ("e-int-huge", "far outside any machine word", i64(10**30), "INT_OUT_OF_RANGE"),
    ("e-int-too-big-among-values", "int64 max + 1 beside legal values",
     obj(("a", i64(1)), ("b", i64(2**63)), ("c", s("x"))), "INT_OUT_OF_RANGE"),
    ("e-int-too-small-among-values", "int64 min - 1 beside legal values",
     obj(("a", i64(1)), ("b", i64(-(2**63) - 1)), ("c", s("x"))), "INT_OUT_OF_RANGE"),
]
# A key duplicated *byte for byte* is unrepresentable through the encoder in either
# implementation — Python's dict and JavaScript's Map both collapse it before the
# encoder is reached. That case is therefore a parse-side vector, where raw bytes can
# carry what no host container can hold.

# ------------------------------------------------------------------ hash preimage
#
# The digest is over ACS_VERSION 0x00 record_type 0x00 canonical_bytes, so record_type
# is hashed input and needs vectors of its own. It is carried as a tagged node here,
# not as a plain JSON string, for the same reason every other input is: a record_type
# containing a NUL or a lone surrogate has no unambiguous plain-JSON spelling.

HASH_CASES: list[tuple[str, str, Any, Any, str]] = [
    # (id, note, record_type node, value node, "" | id of the case it must equal)
    ("h-plain", "the ordinary case, for comparison", s("evidence_row"), obj(("v", i64(1))), ""),
    ("h-empty-type", "an empty record_type is legal", s(""), obj(("v", i64(1))), ""),
    ("h-empty-type-empty-value", "empty on both sides of the second separator",
     s(""), obj(), ""),
    ("h-nonascii-type", "a record_type outside ASCII", s("r\u00e9sultat"), obj(("v", i64(1))), ""),
    ("h-astral-type", "a record_type outside the BMP", s("\U0001f600row"), obj(("v", i64(1))), ""),
    ("h-long-type", "a record_type longer than a SHA-256 block", s("x" * 100),
     obj(("v", i64(1))), ""),
    ("h-type-with-quote", "record_type is not JSON-escaped; it is raw UTF-8 in the preimage",
     s('a"b\\c'), obj(("v", i64(1))), ""),
    # ---- record_type is NFC-normalized before hashing, exactly like every other
    # string. Each decomposed case must produce the digest of its composed twin.
    ("h-nfc-cafe", "composed", s("caf\u00e9"), obj(("v", i64(1))), ""),
    ("h-nfd-cafe", "decomposed; digest equals h-nfc-cafe", s("cafe\u0301"),
     obj(("v", i64(1))), "h-nfc-cafe"),
    ("h-nfc-angstrom", "composed", s("\u00c5"), obj(("v", i64(1))), ""),
    ("h-nfd-angstrom", "decomposed; digest equals h-nfc-angstrom", s("A\u030a"),
     obj(("v", i64(1))), "h-nfc-angstrom"),
    ("h-nfc-ntilde", "composed", s("\u00f1"), obj(("v", i64(1))), ""),
    ("h-nfd-ntilde", "decomposed; digest equals h-nfc-ntilde", s("n\u0303"),
     obj(("v", i64(1))), "h-nfc-ntilde"),
    ("h-nfc-udiaeresis", "composed", s("\u00fc"), obj(("v", i64(1))), ""),
    ("h-nfd-udiaeresis", "decomposed; digest equals h-nfc-udiaeresis", s("u\u0308"),
     obj(("v", i64(1))), "h-nfc-udiaeresis"),
    ("h-nfc-ocircumflex", "composed", s("\u00f4"), obj(("v", i64(1))), ""),
    ("h-nfd-ocircumflex", "decomposed; digest equals h-nfc-ocircumflex", s("o\u0302"),
     obj(("v", i64(1))), "h-nfc-ocircumflex"),
    ("h-nfc-two-marks", "composed, two marks", s("\u00e9v\u00e9nement"),
     obj(("v", i64(1))), ""),
    ("h-nfd-two-marks", "decomposed, two marks; digest equals h-nfc-two-marks",
     s("e\u0301ve\u0301nement"), obj(("v", i64(1))), "h-nfc-two-marks"),
    ("h-nfc-angstrom-sign", "U+212B normalizes to U+00C5; digest equals h-nfc-angstrom",
     s("\u212b"), obj(("v", i64(1))), "h-nfc-angstrom"),
    ("h-nfc-astral-mark", "an astral character before a decomposable one",
     s("\U0001f600caf\u00e9"), obj(("v", i64(1))), ""),
    ("h-nfd-astral-mark", "digest equals h-nfc-astral-mark",
     s("\U0001f600cafe\u0301"), obj(("v", i64(1))), "h-nfc-astral-mark"),
    # ---- the separators are what stop a record_type/value boundary being forged
    ("h-boundary-a", "record_type 'ab', value {'':1}", s("ab"), obj(("", i64(1))), ""),
    ("h-boundary-b", "record_type 'a', value {'b':1}; must NOT equal h-boundary-a",
     s("a"), obj(("b", i64(1))), ""),
]

HASH_ERROR_CASES: list[tuple[str, str, Any, Any, str]] = [
    # (id, note, record_type node, value node, error code)
    ("h-e-nul-only", "a record_type that is one NUL", s16(0x0000), obj(("v", i64(1))),
     "ACS_ERROR"),
    ("h-e-nul-leading", "NUL at the start", s16(0x0000, 0x0061), obj(("v", i64(1))),
     "ACS_ERROR"),
    ("h-e-nul-trailing", "NUL at the end", s16(0x0061, 0x0000), obj(("v", i64(1))),
     "ACS_ERROR"),
    ("h-e-nul-middle", "NUL between two ordinary characters",
     s16(0x0061, 0x0000, 0x0062), obj(("v", i64(1))), "ACS_ERROR"),
    ("h-e-nul-twice", "two NULs", s16(0x0061, 0x0000, 0x0000, 0x0062),
     obj(("v", i64(1))), "ACS_ERROR"),
    ("h-e-nul-forged-boundary",
     "'evidence_row\\0result_stamp' would otherwise produce the preimage of a "
     "different (record_type, value) split",
     s16(*[ord(c) for c in "evidence_row"], 0x0000, *[ord(c) for c in "result_stamp"]),
     obj(("v", i64(1))), "ACS_ERROR"),
    ("h-e-nul-with-nonascii", "NUL beside a multi-byte character",
     s16(0x00e9, 0x0000), obj(("v", i64(1))), "ACS_ERROR"),
    ("h-e-nul-with-astral", "NUL beside a surrogate pair",
     s16(0xD83D, 0xDE00, 0x0000), obj(("v", i64(1))), "ACS_ERROR"),
    ("h-e-nul-both-ends", "NUL at each end",
     s16(0x0000, 0x0061, 0x0000), obj(("v", i64(1))), "ACS_ERROR"),
    ("h-e-nul-in-long-type", "NUL late in a long record_type",
     s16(*[ord("x")] * 64, 0x0000, *[ord("y")] * 8), obj(("v", i64(1))), "ACS_ERROR"),
    # ---- a record_type is a string, so the string rules apply to it too
    ("h-e-surrogate-type", "a lone surrogate in the record_type", s16(0xD800),
     obj(("v", i64(1))), "LONE_SURROGATE"),
    ("h-e-surrogate-type-trailing", "a lone surrogate at the end of the record_type",
     s16(0x0061, 0xDC00), obj(("v", i64(1))), "LONE_SURROGATE"),
    # ---- the value is still encoded, so its refusals still apply
    ("h-e-value-not-finite", "a NaN in the value", s("evidence_row"),
     obj(("v", bits("7ff8000000000000"))), "NOT_FINITE"),
    ("h-e-value-int-range", "an out-of-range integer in the value", s("evidence_row"),
     obj(("v", i64(2**63))), "INT_OUT_OF_RANGE"),
]


PARSE_CASES: list[tuple[str, str, str, str | None]] = [
    # (id, note, input bytes as utf-8 hex, expected error code or None)
    ("p-dup-key", "stock parsers keep the last silently",
     b'{"a":1,"a":2}'.hex(), "DUPLICATE_KEY"),
    ("p-nan-literal", "non-standard JSON constant", b'{"a":NaN}'.hex(), "NOT_FINITE"),
    ("p-infinity-literal", "non-standard JSON constant", b'{"a":Infinity}'.hex(), "NOT_FINITE"),
    ("p-dup-key-nested", "duplicate at depth", b'{"o":{"a":1,"a":2}}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-identical-bytes",
     "byte-identical duplicate keys, which no host container can hold and only a parser sees",
     b'{"\xc3\xa9":1,"\xc3\xa9":2}'.hex(), "DUPLICATE_KEY"),
    ("p-float-as-number", "ACS-1 numbers are integers; floats are carried as strings",
     b'{"a":1.5}'.hex(), "PARSE_ERROR"),
    ("p-int-too-big", "int64 max + 1", b'{"a":9223372036854775808}'.hex(), "INT_OUT_OF_RANGE"),
    ("p-canonical", "already canonical", b'{"a":1}'.hex(), None),

    # ================================================================= widened set
    # ---- duplicate keys, which the stock parser of at least two languages accepts
    # silently. These are byte-level duplicates: unlike the encode side, a parser
    # sees the bytes and no host container has collapsed them yet.
    ("p-dup-key-three", "three copies of one key", b'{"a":1,"a":2,"a":3}'.hex(),
     "DUPLICATE_KEY"),
    ("p-dup-key-separated", "the duplicate is not adjacent to its twin",
     b'{"a":1,"b":2,"a":3}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-deep", "a duplicate four levels down",
     b'{"a":{"b":{"c":{"d":1,"d":2}}}}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-in-array", "a duplicate inside an object inside an array",
     b'[{"a":1,"a":2}]'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-empty", "two empty-string keys", b'{"":1,"":2}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-astral",
     "two astral keys, identical byte for byte",
     b'{"\xf0\x9f\x98\x80":1,"\xf0\x9f\x98\x80":2}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-long-prefix", "keys identical for sixteen bytes and then to the end",
     b'{"alpha/beta/gamma/x":1,"alpha/beta/gamma/x":2}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-collision",
     "composed and decomposed keys are one key on the parse side too",
     b'{"caf\xc3\xa9":1,"cafe\xcc\x81":2}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-angstrom", "U+00C5 and A + U+030A",
     b'{"\xc3\x85":1,"A\xcc\x8a":2}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-angstrom-sign", "U+212B and U+00C5",
     b'{"\xe2\x84\xab":1,"\xc3\x85":2}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-ntilde", "U+00F1 and n + U+0303",
     b'{"\xc3\xb1":1,"n\xcc\x83":2}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-decomposed-first", "the decomposed form first",
     b'{"cafe\xcc\x81":1,"caf\xc3\xa9":2}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-deep", "an NFC collision four levels down",
     b'{"a":{"b":{"c":{"\xc3\xa9":1,"e\xcc\x81":2}}}}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-in-array", "an NFC collision inside an array",
     b'[{"\xc3\xb4":1,"o\xcc\x82":2}]'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-separated", "the colliding pair is not adjacent",
     b'{"\xc3\xbc":1,"m":2,"u\xcc\x88":3}'.hex(), "DUPLICATE_KEY"),
    ("p-dup-key-nfc-long-prefix", "the collision is sixteen bytes in",
     b'{"alpha/beta/gamma/caf\xc3\xa9":1,"alpha/beta/gamma/cafe\xcc\x81":2}'.hex(),
     "DUPLICATE_KEY"),
    ("p-dup-key-nfc-astral", "an astral character before the colliding portion",
     b'{"\xf0\x9f\x92\xa9caf\xc3\xa9":1,"\xf0\x9f\x92\xa9cafe\xcc\x81":2}'.hex(),
     "DUPLICATE_KEY"),
    ("p-dup-key-nfc-three", "three spellings of one key",
     b'{"\xc3\x85":1,"A\xcc\x8a":2,"\xe2\x84\xab":3}'.hex(), "DUPLICATE_KEY"),
    # ---- integer bounds. The parser has its own range check, separate from the
    # encoder's, and an off-by-one in either direction has to be visible.
    ("p-int-too-small", "int64 min - 1", b'{"a":-9223372036854775809}'.hex(),
     "INT_OUT_OF_RANGE"),
    ("p-int-too-big-nested", "int64 max + 1 at depth",
     b'{"a":{"b":9223372036854775808}}'.hex(), "INT_OUT_OF_RANGE"),
    ("p-int-too-small-nested", "int64 min - 1 at depth",
     b'{"a":{"b":-9223372036854775809}}'.hex(), "INT_OUT_OF_RANGE"),
    ("p-int-too-big-in-array", "int64 max + 1 in an array",
     b'[1,9223372036854775808]'.hex(), "INT_OUT_OF_RANGE"),
    ("p-int-too-small-in-array", "int64 min - 1 in an array",
     b'[1,-9223372036854775809]'.hex(), "INT_OUT_OF_RANGE"),
    ("p-int-too-big-second-value", "int64 max + 1 after a legal value",
     b'{"a":1,"b":9223372036854775808}'.hex(), "INT_OUT_OF_RANGE"),
    ("p-int-too-small-second-value", "int64 min - 1 after a legal value",
     b'{"a":1,"b":-9223372036854775809}'.hex(), "INT_OUT_OF_RANGE"),
    ("p-int-too-big-deep", "int64 max + 1 four levels down",
     b'{"a":{"b":{"c":9223372036854775808}}}'.hex(), "INT_OUT_OF_RANGE"),
    ("p-int-too-small-deep", "int64 min - 1 four levels down",
     b'{"a":{"b":{"c":-9223372036854775809}}}'.hex(), "INT_OUT_OF_RANGE"),
    ("p-int-uint64-max", "2^64 - 1", b'{"a":18446744073709551615}'.hex(),
     "INT_OUT_OF_RANGE"),
    ("p-int-huge", "far outside any machine word",
     (b'{"a":' + b"9" * 40 + b"}").hex(), "INT_OUT_OF_RANGE"),
    # ---- the boundary values themselves are legal and must be accepted
    ("p-int-max-ok", "int64 max is inside the range",
     b'{"a":9223372036854775807}'.hex(), None),
    ("p-int-min-ok", "int64 min is inside the range",
     b'{"a":-9223372036854775808}'.hex(), None),
    ("p-int-bounds-array", "both boundaries in an array",
     b'[9223372036854775807,-9223372036854775808]'.hex(), None),
    ("p-int-bounds-nested", "both boundaries at depth",
     b'{"a":{"b":9223372036854775807,"c":-9223372036854775808}}'.hex(), None),
    ("p-int-max-minus-one-ok", "one inside the upper boundary",
     b'{"a":9223372036854775806}'.hex(), None),
    ("p-int-min-plus-one-ok", "one inside the lower boundary",
     b'{"a":-9223372036854775807}'.hex(), None),
    ("p-int-max-deep", "int64 max four levels down",
     b'{"a":{"b":{"c":9223372036854775807}}}'.hex(), None),
    ("p-int-min-deep", "int64 min four levels down",
     b'{"a":{"b":{"c":-9223372036854775808}}}'.hex(), None),
    ("p-int-max-among-others", "int64 max beside ordinary integers",
     b'[0,1,9223372036854775807,-1]'.hex(), None),
    ("p-int-min-among-others", "int64 min beside ordinary integers",
     b'[0,1,-9223372036854775808,-1]'.hex(), None),
    ("p-int-bounds-and-strings", "boundaries beside string values",
     b'{"a":9223372036854775807,"b":"x","c":-9223372036854775808}'.hex(), None),
    # ---- other things a parser must accept, so that a stricter-than-ACS-1 reader is
    # caught as surely as a laxer one
    ("p-empty-containers", "empty object and array", b'{"a":{},"b":[]}'.hex(), None),
    ("p-escapes", "every escape ACS-1 emits",
     b'{"\\b\\t\\n\\f\\r\\"\\\\":"\\u0000\\u001f"}'.hex(), None),
    ("p-raw-utf8", "non-ASCII is raw in canonical form and must parse as such",
     b'{"caf\xc3\xa9":"\xe4\xb8\xad\xf0\x9f\x98\x80"}'.hex(), None),
    ("p-float-as-string", "floats are strings; the parser must not object to the value",
     b'{"a":"2.4e0"}'.hex(), None),
    # ---- and things it must reject
    ("p-float-exponent", "an exponent-form JSON number is still a JSON number",
     b'{"a":1e0}'.hex(), "PARSE_ERROR"),
    ("p-float-whole", "a float that looks like an integer with a point",
     b'{"a":1.0}'.hex(), "PARSE_ERROR"),
    ("p-float-negative", "a negative float", b'{"a":-1.5}'.hex(), "PARSE_ERROR"),
    ("p-float-zero", "0.0 is still a float literal", b'{"a":0.0}'.hex(), "PARSE_ERROR"),
    ("p-float-in-array", "a float literal in an array", b'[1,1.5]'.hex(), "PARSE_ERROR"),
    ("p-float-deep", "a float literal four levels down",
     b'{"a":{"b":{"c":1.5}}}'.hex(), "PARSE_ERROR"),
    ("p-float-capital-exponent", "capital E is legal JSON and still a float",
     b'{"a":1E5}'.hex(), "PARSE_ERROR"),
    ("p-float-both", "digits, point and exponent", b'{"a":1.5e-3}'.hex(), "PARSE_ERROR"),
    ("p-float-fraction-only", "a fraction below one", b'{"a":0.5}'.hex(), "PARSE_ERROR"),
    ("p-float-many-digits", "a float with a long fractional part",
     b'{"a":1234.5678}'.hex(), "PARSE_ERROR"),
    ("p-neg-infinity-literal", "non-standard JSON constant", b'{"a":-Infinity}'.hex(),
     "NOT_FINITE"),
    ("p-nan-in-array", "non-standard JSON constant at depth", b'[1,NaN]'.hex(),
     "NOT_FINITE"),
    ("p-trailing-content", "a second value after the first",
     b'{"a":1}{"b":2}'.hex(), "PARSE_ERROR"),
    ("p-unterminated-string", "truncated input", b'{"a":"x'.hex(), "PARSE_ERROR"),
    ("p-empty-input", "no value at all", b"".hex(), "PARSE_ERROR"),
]

CANONICAL: list[tuple[str, str, Any]] = [
    # (id, note, node). The expected bytes are generated, not written by hand: the
    # claim under test is that `is_canonical` ACCEPTS what the encoder emits. It runs
    # parse and re-encode together, so it catches defects on either side — a parser
    # that mangles what it reads fails here even when the encoder is intact.
    ("c-scalar-int", "", i64(1)),
    ("c-scalar-string", "", s("hello")),
    ("c-float-string", "a float is a string in canonical form", f64(2.4)),
    ("c-empty-object", "", obj()),
    ("c-empty-array", "", arr()),
    ("c-nested-empties", "", obj(("a", obj()), ("b", arr()))),
    ("c-sorted-keys", "already in byte order", obj(("a", i64(1)), ("b", i64(2)))),
    ("c-prefix-keys", "keys that differ only past a common prefix",
     obj(("a", i64(1)), ("ab", i64(2)), ("abc", i64(3)))),
    ("c-utf16-divergent-keys", "keys where UTF-8 and UTF-16 order disagree",
     obj(("z", i64(1)), ("Ｚ", i64(2)), ("\U0001f600", i64(3)))),
    ("c-escapes", "every escape ACS-1 emits, in a key and in a value",
     obj(("\b\t\n\f\r\"\\", s("\x00\x01\x1f")), ("a", s("\x0b\x7f/")))),
    ("c-raw-non-ascii", "non-ASCII stays raw", s("café中\U0001f600")),
    ("c-int-bounds", "both int64 boundaries",
     obj(("max", i64(2**63 - 1)), ("min", i64(-(2**63))))),
    ("c-bools-and-null", "", arr(TRUE, FALSE, NULL, i64(1), i64(0))),
    ("c-deep", "ten levels", obj(("a", arr(obj(("b", arr(obj(("c", arr(
        obj(("d", arr(i64(1), s("x")))),
    )))))))))),
    ("c-metric-value", "the ADR-0001 tagged form, which is what actually gets hashed",
     obj(("kind", s("defined")), ("value", f64(2.4)))),
    ("c-int-max-deep", "int64 max at depth", obj(("a", obj(("b", i64(2**63 - 1)))))),
    ("c-int-min-deep", "int64 min at depth", obj(("a", obj(("b", i64(-(2**63))))))),
    ("c-int-bounds-array", "both boundaries in an array",
     arr(i64(2**63 - 1), i64(-(2**63)))),
    ("c-astral-keys", "keys where UTF-8 and UTF-16 order disagree, at depth",
     obj(("o", obj(("\U0001f600", i64(1)), ("\ue000", i64(2)))))),
]

NON_CANONICAL: list[tuple[str, str, str]] = [
    ("nc-whitespace", "whitespace is never present in canonical form", b'{"a": 1}'.hex()),
    ("nc-key-order", "keys out of byte order", b'{"b":1,"a":2}'.hex()),
    ("nc-escaped-nonascii", "non-ASCII must be raw, not escaped", b'"\\u00e9"'.hex()),
    ("nc-uppercase-escape", "control escapes use lowercase hex", b'"\\u001F"'.hex()),

    # ================================================================= widened set
    # `is_canonical` is parse-then-re-encode-then-compare, so every rule ACS-1 has
    # shows up here from the other side: these are the forms a stored evidence row
    # must NOT be accepted in.
    ("nc-whitespace-newline", "a newline between tokens", b'{\n"a":1\n}'.hex()),
    ("nc-whitespace-tab", "a tab after a colon", b'{"a":\t1}'.hex()),
    ("nc-whitespace-in-array", "spaces between array members", b'[1, 2]'.hex()),
    ("nc-key-order-multibyte", "a two-byte key before an ASCII one",
     b'{"\xc3\xa9":1,"a":2}'.hex()),
    ("nc-key-order-utf16",
     "keys in UTF-16 code-unit order: the astral key's leading unit is 0xd83d, below "
     "the fullwidth character's 0xff3a, so UTF-16 puts it first while its UTF-8 "
     "bytes (f0 ...) put it last. This is the ordering RFC 8785 specifies and the "
     "reason ADR-0003 does not adopt it",
     b'{"z":1,"\xf0\x9f\x98\x80":3,"\xef\xbc\xba":2}'.hex()),
    ("nc-key-order-utf16-two-astrals",
     "the same divergence with two astral keys",
     b'{"\xf0\x90\x80\x80":1,"\xf0\x9f\x98\x80":2,"\xef\xbf\xa0":3}'.hex()),
    ("nc-key-order-prefix", "a longer key before the one that prefixes it",
     b'{"ab":1,"a":2}'.hex()),
    ("nc-key-order-last-byte", "keys differing only in their final byte, reversed",
     b'{"aaab":1,"aaaa":2}'.hex()),
    ("nc-escaped-slash", "the solidus is not escaped", b'"a\\/b"'.hex()),
    ("nc-escaped-del", "0x7f is not escaped", b'"\\u007f"'.hex()),
    ("nc-escaped-ascii", "a printable ASCII character escaped", b'"\\u0041"'.hex()),
    ("nc-long-escape-for-short-form", "0x09 has a two-character form and must use it",
     b'"\\u0009"'.hex()),
    ("nc-long-escape-newline", "0x0a has a two-character form and must use it",
     b'"\\u000a"'.hex()),
    ("nc-uppercase-escape-in-key", "lowercase hex applies to keys too",
     b'{"\\u001F":1}'.hex()),
    ("nc-nfd-string", "a decomposed string value", b'"cafe\xcc\x81"'.hex()),
    ("nc-nfd-key", "a decomposed key", b'{"cafe\xcc\x81":1}'.hex()),
    ("nc-nfkc-neighbours",
     "a fullwidth key beside its NFKC folding: out of byte order, and a duplicate as "
     "well for any implementation that normalizes with NFKC instead of NFC",
     b'{"\xef\xbc\xba":1,"Z":2}'.hex()),
    ("nc-dup-key", "a duplicate key is not a canonical row", b'{"a":1,"a":2}'.hex()),
    ("nc-dup-key-nfc", "keys colliding after NFC",
     b'{"caf\xc3\xa9":1,"cafe\xcc\x81":2}'.hex()),
    ("nc-dup-key-deep", "a duplicate at depth", b'{"o":{"a":1,"a":2}}'.hex()),
    ("nc-int-too-big", "an out-of-range integer", b'{"a":9223372036854775808}'.hex()),
    ("nc-int-too-small", "an out-of-range integer",
     b'{"a":-9223372036854775809}'.hex()),
    ("nc-int-leading-zero", "leading zeros are not canonical", b'{"a":01}'.hex()),
    ("nc-int-plus-sign", "a leading plus is not JSON", b'{"a":+1}'.hex()),
    ("nc-int-negative-zero", "-0 is not a canonical integer", b'{"a":-0}'.hex()),
    ("nc-float-literal", "a float as a JSON number", b'{"a":1.5}'.hex()),
    ("nc-float-exponent-literal", "a float in exponent form", b'{"a":1e0}'.hex()),
    ("nc-nan-literal", "a non-standard constant", b'{"a":NaN}'.hex()),
    ("nc-lone-surrogate-escape", "a lone surrogate written as a \\u escape",
     b'"\\ud800"'.hex()),
    ("nc-lone-surrogate-in-key", "a lone surrogate in a key",
     b'{"\\ud800":1}'.hex()),
    ("nc-trailing-comma", "not JSON at all", b'{"a":1,}'.hex()),
    ("nc-trailing-content", "a second value after the first", b'{"a":1}{}'.hex()),
    ("nc-empty-input", "no value at all", b"".hex()),
    ("nc-invalid-utf8", "bytes that are not UTF-8", bytes([0x22, 0xC3, 0x28, 0x22]).hex()),
]


def main() -> None:
    vectors: dict[str, Any] = {
        "acs_version": ACS_VERSION,
        "note": (
            "Inputs are given in a neutral tagged form so that no host language's "
            "JSON parser or number formatter can influence them. Floats are IEEE-754 "
            "bit patterns, big-endian hex. Integers are decimal strings. Strings are "
            "UTF-8 hex, or UTF-16 code units in big-endian hex under the str16 tag "
            "for the cases UTF-8 cannot carry. Expected output is the canonical UTF-8 "
            "bytes as hex, and the SHA-256 of "
            "ACS_VERSION 0x00 record_type 0x00 canonical_bytes."
        ),
        "coverage_note": (
            "Every section here is sized by the mutation control in "
            "harness/acs/mutate.py, not by taste: each deliberate defect that script "
            "injects must fail at least eight checks. Sections that look repetitive "
            "are repetitive on purpose — a rule pinned by one vector is a rule an "
            "implementation can get wrong and still pass."
        ),
        "encode": [],
        "encode_errors": [],
        "hash": [],
        "hash_errors": [],
        "parse_note": (
            "Parse cases are normative in WHETHER they reject, not in the code they "
            "reject with. A host that rejects a non-standard JSON constant in its own "
            "tokenizer legitimately reports a syntax error where this implementation "
            "reports NOT_FINITE. Encode-error codes ARE normative: those are ACS-1's "
            "own semantics rather than a host parser's. The error field distinguishes "
            "the two: PARSE_ERROR means the input is malformed JSON and any refusal "
            "counts, while DUPLICATE_KEY, INT_OUT_OF_RANGE and NOT_FINITE mark inputs "
            "that are well-formed JSON and can only be refused by an ACS-1 rule."
        ),
        "parse": [],
        "canonical": [],
        "non_canonical": [],
    }

    for case_id, note, record_type, node in CASES:
        if not record_type.isascii():
            raise SystemExit(
                f"{case_id}: record_type is a plain JSON string in this section and "
                f"must stay ASCII; non-ASCII record types belong in HASH_CASES"
            )
        value = build(node)
        canon = canonicalize(value)
        vectors["encode"].append({
            "id": case_id,
            "note": note,
            "record_type": record_type,
            "input": node,
            "canonical_hex": canon.hex(),
            "canonical_utf8": canon.decode("utf-8"),
            "sha256": acs_sha256(record_type, value),
        })

    for case_id, note, node, code in ERROR_CASES:
        try:
            canonicalize(build(node))
        except AcsError as exc:
            actual = exc.code
        else:
            raise SystemExit(f"{case_id}: expected {code}, encoder accepted the input")
        if actual != code:
            raise SystemExit(f"{case_id}: expected {code}, got {actual}")
        vectors["encode_errors"].append(
            {"id": case_id, "note": note, "input": node, "error": code}
        )

    digests: dict[str, str] = {}
    for case_id, note, type_node, node, equals in HASH_CASES:
        digest = acs_sha256(build(type_node), build(node))
        digests[case_id] = digest
        if equals and digests[equals] != digest:
            raise SystemExit(f"{case_id}: digest differs from {equals}")
        vectors["hash"].append({
            "id": case_id,
            "note": note,
            "record_type": type_node,
            "input": node,
            "sha256": digest,
            "equals": equals or None,
        })
    if digests["h-boundary-a"] == digests["h-boundary-b"]:
        raise SystemExit("h-boundary-a and h-boundary-b collided: separators are broken")

    for case_id, note, type_node, node, code in HASH_ERROR_CASES:
        try:
            acs_sha256(build(type_node), build(node))
        except AcsError as exc:
            actual = exc.code
        else:
            raise SystemExit(f"{case_id}: expected {code}, hashing accepted the input")
        if actual != code:
            raise SystemExit(f"{case_id}: expected {code}, got {actual}")
        vectors["hash_errors"].append({
            "id": case_id,
            "note": note,
            "record_type": type_node,
            "input": node,
            "error": code,
        })

    for case_id, note, data_hex, code in PARSE_CASES:
        vectors["parse"].append(
            {"id": case_id, "note": note, "input_hex": data_hex, "error": code}
        )

    for case_id, note, node in CANONICAL:
        # Generated rather than written by hand: the claim under test is that
        # is_canonical accepts what the encoder emits, so the encoder produces the
        # bytes and the check is that the round trip through the parser survives.
        data = canonicalize(build(node))
        if not is_canonical(data):
            raise SystemExit(f"{case_id}: encoder output failed its own is_canonical")
        vectors["canonical"].append({
            "id": case_id,
            "note": note,
            "input_hex": data.hex(),
            "input_utf8": data.decode("utf-8"),
        })

    for case_id, note, data_hex in NON_CANONICAL:
        if is_canonical(bytes.fromhex(data_hex)):
            raise SystemExit(f"{case_id}: is_canonical accepted a non-canonical form")
        vectors["non_canonical"].append(
            {"id": case_id, "note": note, "input_hex": data_hex}
        )

    ids = [v["id"] for section in ("encode", "encode_errors", "hash", "hash_errors",
                                   "parse", "canonical", "non_canonical")
           for v in vectors[section]]
    if len(set(ids)) != len(ids):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise SystemExit(f"duplicate vector ids: {dupes}")

    OUT.write_text(json.dumps(vectors, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.name}: {len(ids)} vectors "
          f"({len(vectors['encode'])} encode, {len(vectors['encode_errors'])} encode-error, "
          f"{len(vectors['hash'])} hash, {len(vectors['hash_errors'])} hash-error, "
          f"{len(vectors['parse'])} parse, {len(vectors['canonical'])} canonical, "
          f"{len(vectors['non_canonical'])} non-canonical)")


if __name__ == "__main__":
    main()
