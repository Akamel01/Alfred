// ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).
//
// Written from the specification and the vector file, not translated from acs1.py.
// Its purpose is to test the claim the whole scheme rests on: that a third party can
// recompute Alfred's evidence-chain digests without running Alfred's code.
//
// An auditor needs the parser more than the encoder. They receive stored rows they did
// not produce, so `isCanonical` — parse, re-encode, compare — is the operation that
// actually answers "is this row what its digest says it is".
//
// No dependencies beyond node: built-ins.

import { createHash } from "node:crypto";

export const ACS_VERSION = "ACS-1";

export const INT64_MIN = -(2n ** 63n);
export const INT64_MAX = 2n ** 63n - 1n;

export class AcsError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

// JavaScript cannot tell 1 from 1.0 — both are Number — so the int/float distinction
// that ACS-1 needs on the way *in* cannot be recovered from the value. Floats are
// therefore wrapped explicitly and integers must be BigInt. A bare Number is refused
// rather than guessed at.
export class F64 {
  constructor(value) {
    this.value = value;
  }
}
export const f64 = (value) => new F64(value);

const SHORT_ESCAPES = new Map([
  [0x08, "\\b"],
  [0x09, "\\t"],
  [0x0a, "\\n"],
  [0x0c, "\\f"],
  [0x0d, "\\r"],
  [0x22, '\\"'],
  [0x5c, "\\\\"],
]);

// ------------------------------------------------------------------------- floats

export function encodeFloat(x) {
  if (typeof x !== "number") throw new AcsError("UNSUPPORTED_TYPE", `not a number: ${x}`);
  if (!Number.isFinite(x)) throw new AcsError("NOT_FINITE", `float is not finite: ${x}`);
  if (x === 0) return "0.0e0"; // also normalizes -0

  // toExponential() with no argument is specified to emit as many significand digits
  // as are needed to uniquely identify the value — the same shortest-digit sequence
  // every correct implementation produces. Only the presentation differs, and
  // ADR-0004 pins that.
  const [mantissa, exponent] = x.toExponential().split("e");
  const dot = mantissa.indexOf(".");
  const head = dot === -1 ? mantissa : mantissa.slice(0, dot);
  const tail = dot === -1 ? "0" : mantissa.slice(dot + 1);
  return `${head}.${tail}e${parseInt(exponent, 10)}`;
}

export const decodeFloat = (text) => Number(text);

// ------------------------------------------------------------------------ strings

function checkSurrogates(text) {
  // TextEncoder replaces a lone surrogate with U+FFFD and reports nothing, so the
  // corruption is silent unless it is checked for explicitly. Python raises here.
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    if (c >= 0xd800 && c <= 0xdbff) {
      const next = text.charCodeAt(i + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) {
        throw new AcsError("LONE_SURROGATE", `unpaired high surrogate at ${i}`);
      }
      i++;
    } else if (c >= 0xdc00 && c <= 0xdfff) {
      throw new AcsError("LONE_SURROGATE", `unpaired low surrogate at ${i}`);
    }
  }
}

function normalize(text) {
  checkSurrogates(text);
  return text.normalize("NFC");
}

function encodeString(text) {
  let out = '"';
  for (const ch of text) {
    const cp = ch.codePointAt(0);
    if (SHORT_ESCAPES.has(cp)) out += SHORT_ESCAPES.get(cp);
    else if (cp < 0x20) out += "\\u" + cp.toString(16).padStart(4, "0");
    else out += ch;
  }
  return out + '"';
}

// ------------------------------------------------------------------------- encode

const UTF8 = new TextEncoder();

function compareBytes(a, b) {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) if (a[i] !== b[i]) return a[i] - b[i];
  return a.length - b.length;
}

function encode(value) {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "bigint") {
    if (value < INT64_MIN || value > INT64_MAX) {
      throw new AcsError("INT_OUT_OF_RANGE", `outside signed 64-bit range: ${value}`);
    }
    return value.toString();
  }
  if (value instanceof F64) return encodeString(encodeFloat(value.value));
  if (typeof value === "number") {
    throw new AcsError(
      "UNSUPPORTED_TYPE",
      "bare Number is ambiguous in ACS-1: use BigInt for integers, f64() for floats",
    );
  }
  if (typeof value === "string") return encodeString(normalize(value));
  if (Array.isArray(value)) return "[" + value.map(encode).join(",") + "]";

  const entries = value instanceof Map ? [...value.entries()] : null;
  if (entries === null) {
    throw new AcsError("UNSUPPORTED_TYPE", `not representable: ${Object.prototype.toString.call(value)}`);
  }

  const items = [];
  const seen = new Set();
  for (const [rawKey, val] of entries) {
    if (typeof rawKey !== "string") {
      throw new AcsError("BAD_KEY_TYPE", `object key is not a string: ${rawKey}`);
    }
    const key = normalize(rawKey);
    const bytes = UTF8.encode(key);
    const marker = bytes.join(",");
    if (seen.has(marker)) {
      throw new AcsError("DUPLICATE_KEY", `duplicate object key after NFC: ${key}`);
    }
    seen.add(marker);
    items.push([bytes, key, val]);
  }
  items.sort((a, b) => compareBytes(a[0], b[0]));
  return "{" + items.map(([, k, v]) => `${encodeString(k)}:${encode(v)}`).join(",") + "}";
}

export const canonicalize = (value) => UTF8.encode(encode(value));

// --------------------------------------------------------------------------- hash

export function hashInput(recordType, value) {
  if (recordType.includes("\u0000")) {
    throw new AcsError("ACS_ERROR", "record_type must not contain a NUL byte");
  }
  return Buffer.concat([
    Buffer.from(ACS_VERSION, "utf8"),
    Buffer.from([0]),
    Buffer.from(normalize(recordType), "utf8"),
    Buffer.from([0]),
    Buffer.from(canonicalize(value)),
  ]);
}

export const acsSha256 = (recordType, value) =>
  createHash("sha256").update(hashInput(recordType, value)).digest("hex");

// -------------------------------------------------------------------------- parse

// A hand-written parser rather than JSON.parse, for the same reason Python needs
// object_pairs_hook: the built-in silently keeps the last of a duplicate key pair, so
// the tampering it would hide is invisible to a reviver.
export function parseStrict(bytes) {
  const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  let i = 0;

  const fail = (code, msg) => {
    throw new AcsError(code, `${msg} at offset ${i}`);
  };
  const expect = (ch) => {
    if (text[i] !== ch) fail("PARSE_ERROR", `expected '${ch}'`);
    i++;
  };

  function parseValue() {
    const ch = text[i];
    if (ch === "{") return parseObject();
    if (ch === "[") return parseArray();
    if (ch === '"') return parseString();
    if (text.startsWith("true", i)) return (i += 4), true;
    if (text.startsWith("false", i)) return (i += 5), false;
    if (text.startsWith("null", i)) return (i += 4), null;
    if (text.startsWith("NaN", i) || text.startsWith("Infinity", i) || text.startsWith("-Infinity", i)) {
      fail("NOT_FINITE", "JSON constant not permitted in ACS-1");
    }
    return parseNumber();
  }

  function parseObject() {
    expect("{");
    const map = new Map();
    if (text[i] === "}") return i++, map;
    for (;;) {
      // Normalized before the duplicate check, and stored normalized, because two
      // keys differing only by composition are one key — the same rule the encoder
      // applies. Without this the parser accepts a row the encoder could never have
      // produced, which is exactly the tampering `parseStrict` exists to catch.
      const key = normalize(parseString());
      if (map.has(key)) fail("DUPLICATE_KEY", `duplicate object key '${key}'`);
      expect(":");
      map.set(key, parseValue());
      if (text[i] === ",") { i++; continue; }
      expect("}");
      return map;
    }
  }

  function parseArray() {
    expect("[");
    const out = [];
    if (text[i] === "]") return i++, out;
    for (;;) {
      out.push(parseValue());
      if (text[i] === ",") { i++; continue; }
      expect("]");
      return out;
    }
  }

  function parseString() {
    expect('"');
    let out = "";
    for (;;) {
      const ch = text[i];
      if (ch === undefined) fail("PARSE_ERROR", "unterminated string");
      if (ch === '"') return i++, out;
      if (ch === "\\") {
        i++;
        const esc = text[i++];
        const simple = { '"': '"', "\\": "\\", "/": "/", b: "\b", f: "\f", n: "\n", r: "\r", t: "\t" };
        if (esc in simple) out += simple[esc];
        else if (esc === "u") {
          out += String.fromCharCode(parseInt(text.slice(i, i + 4), 16));
          i += 4;
        } else fail("PARSE_ERROR", `bad escape '\\${esc}'`);
      } else {
        out += ch;
        i++;
      }
    }
  }

  function parseNumber() {
    const start = i;
    if (text[i] === "-") i++;
    while (i < text.length && text[i] >= "0" && text[i] <= "9") i++;
    if (i === start || (text[start] === "-" && i === start + 1)) fail("PARSE_ERROR", "expected a value");
    const raw = text.slice(start, i);
    if (text[i] === "." || text[i] === "e" || text[i] === "E") {
      fail("PARSE_ERROR", "ACS-1 numbers are integers; floats are carried as strings");
    }
    const n = BigInt(raw);
    if (n < INT64_MIN || n > INT64_MAX) fail("INT_OUT_OF_RANGE", `outside signed 64-bit range: ${raw}`);
    return n;
  }

  const value = parseValue();
  if (i !== text.length) fail("PARSE_ERROR", "trailing content");
  return value;
}

export function isCanonical(bytes) {
  try {
    return Buffer.from(canonicalize(parseStrict(bytes))).equals(Buffer.from(bytes));
  } catch {
    return false;
  }
}
