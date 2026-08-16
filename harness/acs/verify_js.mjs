// Verify the JavaScript implementation against the published ACS-1 vector suite.
//
// This is the experiment the vector file exists for. Passing means an implementation
// written in another language, from the spec and the vectors alone, produces the same
// canonical bytes and the same digests — which is the claim Alfred makes to an auditor
// and has, until now, only asserted.
//
//     node harness/acs/verify_js.mjs

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { AcsError, F64, acsSha256, canonicalize, f64, isCanonical, parseStrict } from "./acs1.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const vectors = JSON.parse(readFileSync(join(here, "vectors.json"), "utf8"));

const hex = (bytes) => Buffer.from(bytes).toString("hex");

// The neutral node form -> JavaScript values. The only part of the vector file an
// independent implementation has to reimplement; everything else is data.
function build(node) {
  switch (node.t) {
    case "null":
      return null;
    case "bool":
      return node.v;
    case "i64":
      return BigInt(node.v);
    case "f64":
      return f64(Buffer.from(node.v, "hex").readDoubleBE(0));
    case "str":
      return Buffer.from(node.v, "hex").toString("utf8");
    case "str16": {
      // UTF-16 code units, big-endian hex. The str tag cannot carry a lone
      // surrogate: Buffer.toString("utf8") substitutes U+FFFD for one silently, so
      // a surrogate vector read through it would test this decoder rather than the
      // encoder's refusal.
      const raw = Buffer.from(node.v, "hex");
      let out = "";
      for (let i = 0; i < raw.length; i += 2) out += String.fromCharCode(raw.readUInt16BE(i));
      return out;
    }
    case "arr":
      return node.v.map(build);
    case "obj": {
      // A Map, not an object literal: two keys that differ only by Unicode
      // composition are distinct JavaScript strings and must both reach the encoder
      // so that it can reject them as one key.
      const m = new Map();
      for (const [k, v] of node.v) m.set(Buffer.from(k, "hex").toString("utf8"), build(v));
      return m;
    }
    default:
      throw new Error(`unknown node tag: ${node.t}`);
  }
}

let pass = 0;
const failures = [];
const check = (id, ok, detail) => (ok ? pass++ : failures.push(`${id}: ${detail}`));

for (const c of vectors.encode) {
  let actual;
  try {
    actual = hex(canonicalize(build(c.input)));
  } catch (e) {
    check(c.id, false, `threw ${e.code ?? e.message}`);
    continue;
  }
  check(c.id + " (bytes)", actual === c.canonical_hex,
    `expected ${c.canonical_utf8}, got ${Buffer.from(actual, "hex").toString("utf8")}`);

  const digest = acsSha256(c.record_type, build(c.input));
  check(c.id + " (sha256)", digest === c.sha256, `expected ${c.sha256}, got ${digest}`);
}

for (const c of vectors.encode_errors) {
  try {
    canonicalize(build(c.input));
    check(c.id, false, `expected ${c.error}, encoder accepted the input`);
  } catch (e) {
    check(c.id, e instanceof AcsError && e.code === c.error,
      `expected ${c.error}, got ${e.code ?? e.message}`);
  }
}

// The record_type is hashed input too: NFC applies to it, and the NUL separators are
// what stop its boundary with the payload being forged.
for (const c of vectors.hash) {
  try {
    const digest = acsSha256(build(c.record_type), build(c.input));
    check(c.id, digest === c.sha256, `expected ${c.sha256}, got ${digest}`);
  } catch (e) {
    check(c.id, false, `threw ${e.code ?? e.message}`);
  }
}

for (const c of vectors.hash_errors) {
  try {
    acsSha256(build(c.record_type), build(c.input));
    check(c.id, false, `expected ${c.error}, hashing accepted the input`);
  } catch (e) {
    check(c.id, e instanceof AcsError && e.code === c.error,
      `expected ${c.error}, got ${e.code ?? e.message}`);
  }
}

for (const c of vectors.parse) {
  const bytes = Buffer.from(c.input_hex, "hex");
  if (c.error === null) {
    try {
      parseStrict(bytes);
      check(c.id, true);
    } catch (e) {
      check(c.id, false, `expected acceptance, got ${e.code ?? e.message}`);
    }
  } else {
    try {
      parseStrict(bytes);
      check(c.id, false, "expected rejection, parser accepted");
    } catch (e) {
      // The error *code* is deliberately not compared — see `parse_note` in the
      // vector file. For PARSE_ERROR the input is malformed JSON and any refusal
      // counts, including one from a host tokenizer that never reaches ACS-1's
      // rules; for the ACS codes the input is well-formed JSON, so only an ACS-1
      // rule can be what rejected it.
      check(c.id, c.error === "PARSE_ERROR" || e instanceof AcsError,
        `rejected with a non-ACS error: ${e.message}`);
    }
  }
}

// The mirror of the non-canonical section: bytes a correct encoder emitted, which the
// parser must read back unchanged. An encoder-only suite cannot catch a parser that
// mangles what it reads.
for (const c of vectors.canonical) {
  check(c.id, isCanonical(Buffer.from(c.input_hex, "hex")),
    `rejected canonical bytes: ${c.input_utf8}`);
}

for (const c of vectors.non_canonical) {
  check(c.id, !isCanonical(Buffer.from(c.input_hex, "hex")), "accepted a non-canonical form");
}

// Host-language traps this implementation has that Python does not.
try {
  canonicalize(1);
  check("js-bare-number", false, "a bare Number was accepted");
} catch (e) {
  check("js-bare-number", e.code === "UNSUPPORTED_TYPE", `got ${e.code}`);
}
check("js-int64-max-needs-bigint",
  Number("9223372036854775807") !== 9223372036854775807n && String(Number("9223372036854775807")) === "9223372036854776000",
  "Number no longer loses int64 precision — revisit the BigInt requirement");
try {
  canonicalize("\ud800");
  check("js-lone-surrogate", false, "a lone surrogate was accepted");
} catch (e) {
  check("js-lone-surrogate", e.code === "LONE_SURROGATE", `got ${e.code}`);
}
check("js-textencoder-is-silent",
  hex(new TextEncoder().encode("\ud800")) === "efbfbd",
  "TextEncoder no longer substitutes silently — the explicit check may be removable");

console.log(`${pass} checks passed, ${failures.length} failed`);
for (const f of failures) console.log("  FAIL " + f);
process.exit(failures.length === 0 ? 0 : 1);
