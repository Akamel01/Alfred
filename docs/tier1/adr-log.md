---
status:        frozen
owner:         human
enforcement:   none
evidence:      One published ADR, whose decisive inputs were measured on this machine rather than argued: Pydantic v2's default serialization of infinity, and the cost of per-timestep objects against vectorized evaluation.
falsifies_if:  An ADR is edited after publication rather than superseded.
review_after:  Phase 4
---

# ADR Log

Immutable, dated architecture decision records, including every stage-gate waiver.
Historical claims are never revised, only superseded. An ADR that turns out to be wrong
gets a successor and a `Superseded by` line; its text stays as written.

Numbering is sequential and never reused.

---

## ADR-0001 — Representation of undefined and infinite metric values

**Date:** 2026-08-12 · **Status:** Accepted · **Supersedes:** none · **Amended by:** ADR-0002 (encoding clause) · **See also:** ADR-0006 (the tagged-union pattern gains a third use, for upstream toolchain provenance)

### Context

The Edge Case and Degeneracy Specification requires every metric to be total over its
declared input domain, forbids NaN as an output, forbids a finite number where the
quantity is undefined, and distinguishes three claims that all read informally as "no
collision": a defined finite value, `+inf` (the event provably never occurs), and
`Undefined(reason)` (the quantity is not defined for this input).

That specification says what must be represented. It did not say how, and the choice
propagates into every metric signature, the API schema, the criterion comparison and the
content-addressed result hash — so it is a first-hour Phase 0 decision, not a later
refactor.

### Options considered

| | Option | Outcome |
|---|---|---|
| A | `float`, NaN for undefined | Rejected by the specification already. NaN propagates silently and `NaN != NaN` defeats equality-based detection. |
| B | `MetricResult(value: float, defined: bool, reason: Reason)` | **Rejected.** The type checker cannot see the trap — `.value` is always a `float` and reads fine when meaningless. Carries a plausible number in an ignorable field, which is the exact failure the specification exists to prevent. |
| C | `value: float \| None`, `None` meaning undefined | **Rejected on measurement — see below.** |
| D | `np.ma.MaskedArray` | **Rejected.** A mask is one bit and carries no reason, so `NO_CONFLICT_AREA`, `SINGLE_OCCUPANCY` and `INSUFFICIENT_SAMPLES` collapse into one another. Mask propagation through numpy operations is also inconsistent. |
| E | Tagged discriminated union at the boundary; numpy value + reason-code arrays inside | **Accepted.** |

### The two measurements that decided it

**1. Pydantic v2 serializes infinity to `null` by default.** Measured on
pydantic 2.13.4:

```
default:                        {"v": inf}  ->  {"v":null}
ser_json_inf_nan="constants":   {"v": inf}  ->  {"v":Infinity}
```

Under option C, `None` on the wire means undefined. So the default serializer silently
converts `+inf` — a *defined* value asserting that no collision occurs — into the
encoding for undefined. E1 and E7 become indistinguishable to any consumer, produced by
the serializer rather than by the metric, with no error anywhere.

The apparent fix is worse for this product. `Infinity` is not valid JSON: RFC 8259 has
no infinity literal, and a strict parser rejects it. Alfred sells re-derivability to
customers who may parse results with a strict decoder, so emitting a non-standard literal
trades a silent bug for an interoperability failure.

Conclusion: **infinity cannot cross a JSON boundary as a float at all.** Some tagged
encoding is required regardless of the in-memory type, which removes option C's only real
advantage — that it was the simplest thing that could work.

**2. Per-timestep objects cost ~60× against vectorized evaluation.** Same TTC-shaped
formula, 200,000 values, this machine:

```
vectorized numpy:     0.5 ms
object per timestep:  29.5 ms
```

Metrics here are evaluated per timestep across a scenario, so a scalar-first
representation forces one Python object per timestep. Recorded because the first version
of this benchmark reported 1.3× — it compared object construction against array
allocation-plus-sum, doing no arithmetic on the object path. The favourable number was
measuring the wrong thing, the same way an unsalted prompt turned a prefill measurement
into a cache-hit measurement during Phase −1.

### Decision

**Two representations with exactly one declared conversion point: the metric's return.**

**Inside computation — `MetricSeries`:**

- `values: NDArray[float64]` — `+inf` is a legal value here
- `reasons: NDArray[uint8]` — `0` means defined; any non-zero code means the value at
  that index is undefined and must not be read
- `t: NDArray[float64]` — the timebase

The reason array *is* the mask, so definedness costs one extra byte per sample and, unlike
a boolean mask, keeps the reason per timestep. NaN never appears in `values`; a degenerate
timestep carries a reason code instead.

**On every boundary — `MetricValue`, a tagged discriminated union:**

```json
{"kind": "defined",   "value": 2.4}
{"kind": "infinite",  "sign": "+"}
{"kind": "undefined", "reason": "NO_CONFLICT_AREA"}
```

Verified RFC-valid and lossless on round trip for all three arms. The tag is the
discriminator, so validation is exhaustive and `pyright --strict` forces every consumer
to narrow before it can do arithmetic.

This crosses the API surface, the evidence store, and criterion comparison. Comparison is
total: match on `kind` first, then compare within the arm — which is what lets the
criterion runner distinguish `Undefined(NO_CONFLICT_AREA)` from
`Undefined(SINGLE_OCCUPANCY)` at verdict time, a distinction option C loses precisely
where it matters most.

### Consequences

**Composition never absorbs.** A composed metric receiving an undefined input returns
`Undefined(UPSTREAM_UNDEFINED)` carrying the originating code as a cause, so the reason
chain survives. Silent absorption is NaN with extra steps and is forbidden.

**Reason codes are a global `IntEnum` with stable integers, never renumbered**, because
they enter both the wire format and the content-addressed hash. Each metric declares the
subset it can emit; CI asserts the metric emits nothing outside its subset and that the
subset covers every catalog row for its domain.

**Canonical float encoding**, since results are content-addressed: shortest
round-tripping `repr`, and `-0.0` normalized to `0.0` before hashing.

**The agent's surface stays numpy-shaped.** Phase 1 tasks have the agent implement the
series function; the harness owns the boundary conversion. This matters because a complex
required return type is a documented source of false-negative rejection of valid
solutions, and the mitigation is that the interface signature is supplied to the agent as
part of the criterion rather than invented by it.

**Cost accepted:** two types instead of one, and a conversion that must be applied
consistently. The conversion point is single and named, and CI asserts no metric returns
a bare `float`.

---

## ADR-0002 — Reason-code width, and what the integer is allowed to be

**Date:** 2026-08-12 · **Status:** Accepted · **Amends:** ADR-0001 (encoding clause only)

### Context

ADR-0001 specified `reasons: NDArray[uint8]` and stated that reason codes are "stable
integers, never renumbered, because they enter both the wire format and the
content-addressed hash."

That clause is wrong, and it is the reason the width looked irreversible. It also
contradicts the same ADR's own wire example, which carries the reason as a **name**
(`{"kind": "undefined", "reason": "NO_CONFLICT_AREA"}`), not as an integer.

### What the measurement showed, and what it did not

Memory is not a deciding input:

```
one scenario, 20 pairs:   values f64 0.5 MB | reasons u8 0.06 MB | u16 0.12 MB
500-scenario sweep:       values f64 240 MB | reasons u8 30 MB   | u16 60 MB
```

Either width is negligible beside the `float64` values array it accompanies. The decision
therefore rests on population growth and on reversibility, not on cost.

**Population.** The enum is global, so codes enumerate *kinds of degeneracy*, not
metrics × kinds — one `NO_CONFLICT_AREA` serves every conflict-point measure. The Edge
Case catalog's 30 rows produce **7** distinct reason codes today, because most rows
resolve to defined values (`+inf`, `0.0`) or are contract violations that raise rather
than encode. Growth is sublinear in the number of metrics.

The one design that would exhaust `uint8` is **namespaced integer ranges** (geometry
1–99, sampling 100–199, and so on), which needs 400 slots for four namespaces. Rejected
independently: the per-metric declared subset already constrains which codes a metric may
emit, explicitly and checkably, and does not consume encoding space to do it.

### Decision

**`uint8`.** More importantly: **the integer is a private in-memory encoding and nothing
else.**

- **The wire format carries the name**, never the integer. A name is self-describing to a
  customer decoding a result, and carries no renumbering hazard across versions.
- **The content-addressed hash covers the canonical JSON**, therefore the name. Integers
  never enter a hash.
- `0` means **defined**, permanently and in every codebook version.
- `255` is reserved as `UNKNOWN_CODE`. A reader encountering a code it does not know maps
  it to 255 — **never to 0**. Silently decoding an unrecognized reason as "defined" would
  reintroduce the plausible-wrong failure through the deserializer.
- That leaves **254 usable codes against 7 in use**.
- **Names are stable and never reused.** Integers are stable within a codebook version.
- Any persisted `MetricSeries` artifact carries `reason_codebook_version`, so the array
  dtype lives inside a versioned envelope.

Consequence, and the point of the ADR: **widening to `uint16` becomes a pure code change**
— no wire change, no hash change, no re-derivation of stored results. The width stops
being an irreversible decision and becomes a reversible one, which is why it can be
settled now at the cheaper option rather than hedged at the more expensive one.

### Enforcement

CI asserts the name↔integer mapping is bijective, that no name is ever reused for a
different meaning, that every metric emits only codes in its declared subset, and that
`0` and `255` are never allocated.

**The build fails at 200 allocated codes**, not at 254. A ceiling discovered at exhaustion
is an emergency; a ceiling discovered at 80% is a scheduled decision with an ADR attached.
This also covers the mechanical hazard that numpy wraps `uint8` arithmetic silently —
`254 + 3` evaluates to `1` with no error — so a naive allocator could otherwise collide
with a live code rather than fail.

---

## ADR-0003 — Canonical serialization for hashed structures (ACS-1)

**Date:** 2026-08-12 · **Status:** Accepted · **Supersedes:** none · **Amended by:** ADR-0004 (float grammar) · **See also:** ADR-0006 (the `alfred.result_stamp` field set becomes versioned; record type `alfred.upstream_config` allocated; SSP-LS-Traceability evaluated against §"the split that decides the shape" and declined)

### Context

ADR-0002 made the content-addressed hash cover the canonical JSON of a result rather than
an integer encoding. That made canonical JSON load-bearing, and nothing specified it. Two
implementations can both emit valid JSON for the same value and hash differently.

Measured divergences between Python's `json` and ES6/JCS number formatting, each of which
silently changes the hash of an identical value:

```
1.0    ->  python "1.0"    | ES6/JCS "1"
-0.0   ->  python "-0.0"   | ES6/JCS "0"
1e16   ->  python "1e+16"  | ES6/JCS "10000000000000000"
1e-7   ->  python "1e-07"  | ES6/JCS "1e-7"
```

Two input-side hazards in the same standard library: `json.loads('{"a":1,"a":2}')`
returns `{'a': 2}` with no error, and `json.dumps(float('nan'))` emits a bare `NaN`.

### The split that decides the shape

There are two hashes here with different requirements, and conflating them was making the
problem harder than it is.

**Artifact content addressing** — arrays, scenario files, diffs, traces, logs. These are
stored as bytes, so the hash is over the bytes as stored. No canonicalization question
arises, and this is the majority of the volume.

**Evidence-chain rows and result stamps** — structured records that a **third party must
be able to recompute**. An external auditor re-deriving the hash chain is the use case
that justifies chaining at all, and that auditor is not guaranteed to be running Python.
Only this second class needs a canonical form.

### Options considered

| | Option | Outcome |
|---|---|---|
| A | `json.dumps(sort_keys=True, separators=(',',':'))` | **Rejected.** A specification only a Python implementation can follow. Every divergence above is inherited, and it leaves the duplicate-key and NaN hazards live. |
| B | RFC 8785 (JCS) | **Rejected, with reservations.** A real standard with multi-language implementations — the strongest argument for it. But its two hardest requirements are exactly the two this design does not need: ES6 number formatting, which is the source of all four divergences, and UTF-16 code-unit key ordering, which is surrogate-dependent and measurably disagrees with byte ordering on astral characters. |
| C | Canonical CBOR / dag-cbor | **Rejected.** Solves the problem, but makes evidence rows unreadable without a decoder. An audit record whose integrity a human cannot inspect with `cat` trades the wrong thing for the right one. |
| D | ACS-1 — JSON with floats carried as strings | **Accepted.** |

### The observation that collapses the problem

Canonicalization here is almost entirely a *number formatting* problem. Encode floats as
strings and it disappears — the bytes are string content, identical in every language,
and no implementation has to reproduce ES6's shortest-round-trip algorithm.

The encoding is lossless: `float(repr(f)) == f` held for **all 200,000** random doubles
tested, with zero failures.

### Decision — ACS-1

1. **UTF-8**, no BOM.
2. **Object keys sorted by UTF-8 byte sequence.** Unambiguous and surrogate-independent,
   unlike JCS's UTF-16 rule.
3. **No whitespace.** Separators are `,` and `:`.
4. **Strings NFC-normalized**, emitted as raw UTF-8 with only the escapes JSON requires —
   never `\uXXXX` for printable characters. NFC matters because `café` composed and
   decomposed are visually identical and produce different bytes.
5. **Floats are JSON strings**, shortest round-tripping decimal, with `-0.0` normalized to
   `"0.0"`.
6. **Integers are JSON numbers**, restricted to signed 64-bit. Anything wider is a string.
7. **NaN and infinity never appear as numbers.** Infinity uses the ADR-0001 tagged form;
   NaN is forbidden as an output everywhere.
8. **Duplicate keys are rejected on parse** — via `object_pairs_hook`, since the default
   parser silently keeps the last — and are unrepresentable on emit.
9. **Domain separation:** the hash is computed over
   `acs_version || 0x00 || record_type || 0x00 || canonical_bytes`, so a result stamp and
   an evidence row with coincidentally identical content cannot collide.
10. **`acs_version` is part of the hashed bytes**, so the scheme is replaceable without
    invalidating the meaning of existing hashes.

### Consequences

**The honest cost:** ACS-1 is not a standard, so a third party implements from this spec
rather than importing a library. This is the one real advantage JCS had, and it is given
up deliberately, because the rules above are roughly twenty lines in any language while a
correct ES6 number formatter is not.

**The mitigation is the deliverable:** a published **test-vector suite** ships with the
spec — floats at the boundaries, astral-plane keys, NFC/NFD pairs, empty containers,
int64 limits, the tagged infinity form. For rules this simple the vectors are a complete
specification, and they are what makes a non-standard defensible to an auditor.

**Phase 0 obligations:** the encoder lives in `harness/`, is protected, and is covered by
a round-trip property test over generated documents. A CI check asserts no code path
hashes a structure through any encoder but this one.

---

## ADR-0004 — The ACS-1 float presentation grammar

**Date:** 2026-08-12 · **Status:** Accepted · **Amends:** ADR-0003 (float rule only)

### Context

ADR-0003 specified floats as "shortest round-tripping decimal, with `-0.0` normalized",
and rested the whole scheme on the claim that carrying floats as strings removes
cross-language number-formatting divergence.

Building the test-vector suite showed that rule is not a specification. Correct
implementations of shortest-round-trip agree on the **digits** and disagree on the
**presentation**:

```
1.0    python "1.0"     JS "1"
100.0  python "100.0"   JS "100"
1e16   python "1e+16"   JS "10000000000000000"
1e-7   python "1e-07"   JS "1e-7"
```

A JavaScript implementer reading ADR-0003 would reasonably use `String(x)` and produce
different bytes for these values — reintroducing precisely the divergence the string
encoding exists to remove, now hidden inside a rule that reads as though it had settled
it.

### Decision

Pin the presentation as **normalized scientific**, always:

```
sign? digit "." digit+ "e" "-"? exponent
```

Exactly one digit before the point, at least one after, no `+` on the exponent, no
leading zeros in it.

```
1.0    -> "1.0e0"        0.1+0.2 -> "3.0000000000000004e-1"
100.0  -> "1.0e2"        5e-324  -> "5.0e-324"
2.4    -> "2.4e0"        -0.0    -> "0.0e0"
10.5   -> "1.05e1"       1e-7    -> "1.0e-7"
```

One rule, no thresholds, no host-language defaults. An implementation needs only the
shortest-digit sequence — which every correct implementation already agrees on — plus a
fixed way to lay it out. Verified bit-exact on 50,000 random doubles, and the grammar
shape is asserted separately on 20,000 more.

Human readability is preserved well enough to keep ADR-0003's argument against canonical
CBOR intact: `"2.4e0"` is still a number an auditor can read in a stored row.

### Consequence

The vectors caught this within an hour of ADR-0003 being written, which is the argument
for the vectors being the specification rather than the prose. It also makes the
published suite non-negotiable rather than a nicety: two of the four divergences ADR-0003
cites as its motivation would have survived into a conforming implementation without it.

### Confirmed by an independent implementation

A JavaScript implementation written against the spec and the vector file
(`harness/acs/acs1.mjs`) reproduces every canonical byte string and every digest:
**136 checks, 0 failures**. `toExponential()` with no argument yields the same
shortest-digit sequence as Python's `repr`, so ADR-0004's grammar needs only the
presentation rules on top of it — which is the property that makes it portable.

Two host-language hazards found that Python does not have, both now guarded in the JS
implementation and recorded here for any future implementer:

- **`Number` cannot represent int64.** `Number("9223372036854775807")` is
  `9223372036854776000`. ACS-1 integers must be `BigInt`.
- **`TextEncoder` silently substitutes U+FFFD for a lone surrogate** where Python raises,
  so the corruption is invisible unless checked for explicitly.

A third is structural rather than a hazard: **JavaScript cannot distinguish `1` from
`1.0`**, both being `Number`, so the int/float split ACS-1 needs on the way *in* is not
recoverable from the value. Floats must be wrapped and integers must be `BigInt`; a bare
`Number` is refused rather than guessed at. The canonical form itself is unaffected —
the distinction is recoverable when *reading* it, since floats are strings there.

**The second implementation found a defect in the first.** Python's `parse_strict`
accepted `{"a":1.5}` and an out-of-range integer, neither of which can occur in canonical
form, because `json.loads` was left to its defaults. Fixed with `parse_float` and
`parse_int` hooks. This is the return on writing a second implementation at all: the
divergence was invisible from inside either one.

One spec point the exercise settled: **parse cases are normative in whether they reject,
not in the code they reject with.** A host that rejects a non-standard JSON constant in
its own tokenizer legitimately reports a syntax error where this implementation reports
`NOT_FINITE`. Encode-error codes remain normative, being ACS-1's own semantics rather
than a host parser's.

**The suite is mutation-checked, because 136/136 on the first run is also what a vacuous
verifier reports.** Deliberate defects injected into the JS encoder — `+` on the
exponent, NFC dropped, UTF-16 key ordering, duplicate detection removed, surrogate check
removed — fail 32, 9, 12, 3 and 1 checks respectively. The thin margins are the honest
part: duplicate detection and the surrogate check rest on very few vectors, and the
suite should be widened there before it is relied on as a conformance gate.


## ADR-0005 — The Tier 0 authorship boundary is split by population, and enforced by an append-only log

**Date:** 2026-08-17 · **Status:** accepted

**Context.** `autonomy-boundaries.md` placed "Tier 0 documentation" permanently outside the
agent boundary. The project had nonetheless produced agent-drafted Tier 0 text twice, so
either the rule or the practice was wrong. A proposed amendment (2026-08-15) would have
permitted drafting under three conditions, the first being that the operator commits the
change — *"a signature an agent can forge is not one."*

**That condition was verified self-refuting.** `git log --format='%G?'` over `docs/tier0/`
returns `N` on every commit: signing is off. Every commit carries the identity
`Akamel01 <taahmedbayoumi@gmail.com>`. Enabling signing does not repair it, because an
assistant with shell access on this account can sign with the operator's key. Of the three
proposed conditions, one was forgeable and one ("the decision precedes the draft") was
unrecorded and therefore unverifiable, leaving one honour-system rule guarding the
constitution.

**The deeper defect is that the rule addressed one population while the exposure lived in
another.** Factory agents run in a container whose read paths the harness fixes at dispatch,
and `docs/tier0/` is not in the mount set — for them the boundary is structural and the rule
redundant. Development-time assistants run on the operator's account with write access to
every file, and for them no control existed at all. The rule was enforced where it was
unnecessary and silent where it mattered.

**Decision.** The boundary row splits into two, one per population, each stating its actual
enforcement. Authorship stays permanently outside for both. Drafting is permitted for
development-time assistants into scratchpad artifacts outside `docs/`, never by editing a
Tier 0 file. The honour-system conditions are replaced by one mechanical check: **a commit
touching `docs/tier0/` must append an entry to this log in the same commit**, enforced by
`scripts/lint_tier0_adr.py`.

**What this does not do.** It does not prevent an assistant from writing the constitution;
nothing on a single-user machine with shell access can. It raises the cost from a silent edit
to two forged artifacts, one of which is append-only and designed to be read. Recorded as a
detection control, not a prevention control, so that no future reader mistakes it for one.

**Consequences.** `scripts/lint_tier0_adr.py` joins the inspector set under D20 and may not
be agent-edited. This ADR is itself the first entry that gate requires. The anchoring hazard
— that a drafted amendment is easier to accept than to rewrite — is stated in the boundary
document and deliberately not mitigated.

**Forward pointer:** none supersedes this yet.

## ADR-0006 — The result stamp field set, its own version, and upstream toolchain provenance

**Date:** 2026-08-16 · **Status:** Accepted · **Supersedes:** none · **Forward pointers:** ADR-0001 (the tagged-union pattern gains a third use), ADR-0003 (the record type `alfred.result_stamp` gains a versioned field set; a second record type `alfred.upstream_config` is allocated)

### Context

`ResultStamp.to_acs()` emitted exactly eight keys — `acs_version`, `assumption_set`,
`code_commit`, `input_hash`, `metric_id`, `metric_version`, `reason_codebook_version`,
`tolerance`. It carried a version for ACS-1 and a version for the reason codebook, and
**no version for its own field set**. It also carried no upstream toolchain provenance:
the stamp names *Alfred's* `metric_version` and `code_commit`, while D48's buyer's
mandated duty under EU 2022/1426 Annex III Part 4 is storage of the **upstream**
toolchain version and traceability from M&S output back to setup. An artifact digest of a
trajectory file is neither.

Adding a field later changes the digest of every re-derived stamp with **no marker
distinguishing old-shape records from new**, so a legitimate schema change becomes
indistinguishable from tampering — in the product whose thesis is tamper-evident
re-derivability. This is the exact class D27 exists to prevent, occurring inside D27's own
implementation.

**The window is open and about to close. Verified rather than assumed:** all four
`migrations/*/versions/` directories contain only `.gitkeep`, no Alembic revision exists
anywhere in the tree, no table holds a stamp, and the only `ResultStamp` constructions in
the repository are two test fixtures. **Zero stamps have ever been persisted, so the
migration cost of this change is zero. It is zero exactly once.**

### The prior decision: SSP Layered Standard Traceability 1.0.0

The field set could not be settled before deciding whether to emit records in an existing
standard's shape. Modelica/prostep ivip **SSP Layered Standard Traceability 1.0.0**
(`https://ssp-standard.org/ssp-ls-traceability/1.0.0/`, 253,204 bytes, re-fetched and
re-read 2026-08-16) specifies much of what a result stamp specifies.

| | Option | Outcome |
|---|---|---|
| A | Adopt SSP wholesale as the stamp record format | **Rejected.** |
| B | Adopt selectively — map Alfred's fields onto SSP names where they correspond | **Rejected.** |
| C | Emit both — ACS-1 for the chain, SRMD at the boundary | **Rejected now; specified as a deferred, trigger-gated export adapter.** |
| D | Decline; stay ACS-1-native; take SSP's mandatory-format-version idea | **Accepted.** |

**The decisive fact: SSP defines no canonical form for its own record.** Its SHA3-256 is
specified over *"the raw data of the data item"* — an opaque blob behind the `data` URI —
and the three occurrences of "canonical" in the entire 253 KB document all refer to a
*"canonical master source"* URI for a resource, never to serialization. Two conforming
implementations serializing the same SRMD produce different bytes: attribute order,
namespace prefix choice, whitespace, empty-element form. That is the exact divergence class
ADR-0003 exists to eliminate, and the XML remedy — Canonical XML 1.1 or Exclusive C14N — is
an order of magnitude larger than ACS-1's twenty lines and carries its own namespace-
inheritance traps.

ADR-0003 split two hashes: **artifact bytes** (hash as stored) and **structured records a
third party must recompute** (needs a canonical form). SSP's checksum is wholly the first;
Alfred's stamp digest is wholly the second. Adopting SSP as the record format would not add
a hash function to the chain — **it would remove the thing the chain is computed over.**

**The second fact, and it decides option B independently: SSP has no field for a tool
version or a tool configuration.** `generatingTool` is defined as *"the name of the tool
that generated this file"*. A name. `fileversion` versions the file's content, not the
tool. So on the one duty this ADR's second half exists to discharge, the standard specifies
nothing — adopting it would supply a tool name and leave the version and the configuration
with nowhere to live but a vendor annotation.

**Why option C is worse than either pure option.** Exactly one Alfred field has a true
correspondence: `stamp_schema_version` → SSP's Mandatory `version`. `input_hash` →
`checksum` is a **semantic mismatch** — SSP's checksum is over a data item's raw bytes,
`input_hash` is an ACS-1 digest of a *structured description* of the declared inputs, and
`checksumType` has no value expressing that. The remaining eight fields — `code_commit`,
`metric_id`, `metric_version`, `assumption_set`, `tolerance`, `reason_codebook_version`,
`acs_version`, `upstream` — have no slot at all and would land in
`Annotation type="org.alfred.stamp"` with `##any` content. **A consumer that does not
implement that annotation sees a name, a format version, a mis-typed checksum and a tool
name: the SSP-shaped part of the export transmits none of the information the product
exists to carry.** Interoperability that transmits nothing is a cost with a marketing
benefit, and the reviewer who asks "what is `org.alfred.stamp`?" is in exactly the
conversation the wrapper was bought to avoid, one indirection later.

**The tension that did not decide it, recorded because it was expected to.** ACS-1 fixes
SHA-256 and ADR-0003 argues at length for it; SSP fixes SHA3-256, FIPS 202. Two hash
functions in one system is a real cost — but under any selective adoption the two never
compete, because they hash different things: SHA3-256 over artifact bytes at an export
boundary, SHA-256/ACS-1 over structured records inside the chain. The residual cost is not
cryptographic; it is that every future reviewer and every third-party implementer acquires
a permanent "which digest is this?" question whose answer lives in prose. Genuine, modest,
and **not decisive in either direction.** The canonical-form argument decides; the hash-
function argument merely fails to rescue.

**What adopting would have bought, weighed honestly.** It blunts "you invented your own
format" in an assessment conversation — a real objection, made more live by the pivot,
which cost the ACS-1 vector suite most of its positioning value. But an XML envelope whose
payload is an opaque vendor annotation does not blunt it either, and ADR-0003 already chose
this trade deliberately with a named mitigation. ADR-0004 proved the mitigation works: an
independent JavaScript implementation reproduced every canonical byte string and every
digest (136 checks, 0 failures) and then found a real defect in the Python one. **A third
party who can recompute your digests from a published vector file is in a stronger position
than one who can parse your XML and learn nothing from it.**

**What is adopted: the idea, not the wire.** SSP makes its record's own format `version`
**Mandatory** while every provenance field — `checksum`, `checksumType`, `generatingTool`,
`generationDateAndTime` — is **Optional**. That is independent confirmation, from a
standards body, that a provenance record must version its own field set. Alfred takes the
version and inverts the optionality: its provenance fields are mandatory by design, which
is the whole difference between the two documents.

**What would reopen this.** If ≥2 of 3 Phase 0.75 demand-gate conversations name a tool in
the buyer's own toolchain that reads or writes SRMD, the option-C export adapter is
scheduled. Today that is a **could-not-check, not a verified absence**: dSPACE SIMPHERA's
Result Containers chapter is login-gated, Ansys AVxcelerate returned 403, and Applied
Intuition has no reachable documentation subdomain. Also relevant to the risk direction:
SRMD's own format version reads *"0.x for this pre-release"* inside a document published as
Layered Standard 1.0.0.

### Decision — the ten-key stamp

Two fields are added. `ResultStamp.to_acs()` freezes at ten keys, sorted by UTF-8 byte
sequence per ACS-1 rule 2:

```
acs_version · assumption_set · code_commit · input_hash · metric_id · metric_version
reason_codebook_version · stamp_schema_version · tolerance · upstream
```

**1. `stamp_schema_version: int`, starting at 1.**

An integer, not a semver: a stamp shape has no minor or patch axis, because any change to
the key set, to a key's type, or to how a value canonicalizes changes the digest input and
is major by construction. Consistent with `reason_codebook_version`, already an integer.

Distinct from `acs_version`, which versions the **encoder** while this versions the
**document**. Bumping one must not imply the other; ADR-0003 §10 put `acs_version` in the
hashed bytes for exactly that separation, and this is its sibling.

**It is inside `to_acs()` and therefore inside the preimage.** A schema version outside the
digest is a claim anyone can rewrite.

**Version 1 is the new ten-key shape.** The eight-key shape receives no number and is
declared never-emitted, because it never was.

> **Hard invariant, CI-asserted.** `stamp_schema_version` is a top-level integer key with
> exactly that name in every stamp schema version that will ever exist. Never renamed,
> never nested, never retyped, never optional. Every future version's readability depends
> on this one field being unconditionally locatable.

**Corollary: reading a stamp is two-stage.** Parse as ACS-1, read
`stamp_schema_version`, *then* dispatch to that version's validator. **A single model
validating every version is forbidden** — it would have to make version-specific fields
optional, reintroducing precisely the optionality this ADR rejects SSP for. Each schema
version gets its own frozen model, and old models are never edited: the same discipline as
this log.

**2. `upstream: UpstreamToolchain` — a tagged discriminated union with no null arm.**

```json
{"kind": "simulated", "tool_name": "...", "tool_version": "...", "config_digest": "...",
                      "tool_build": "...", "config_ref": "..."}
{"kind": "corpus",    "corpus_name": "...", "corpus_version": "...", "scenario_id": "...",
                      "corpus_digest": "..."}
{"kind": "unknown",   "reason": "UPSTREAM_NOT_RECORDED"}
```

The third use of this pattern, after three-valued verdicts and `MetricValue`. Three claims
that read informally as "no simulator" are held apart:

- **Absent / `null` is forbidden.** No default, no `| None`. Absence is the ambiguity the
  design removes, and an optional provenance field is the specific weakness this ADR
  rejects SSP for inheriting.
- **`unknown` is an arm with a mandatory reason.** It means there *was* an upstream
  toolchain and Alfred could not determine it. That is a defect-grade state — the stamp
  does not discharge the buyer's storage duty — and it must be visible, never silent.
- **"Not applicable" is expressed as the *positive* `corpus` arm, never as a negative tag.**
  A bare `{"kind":"not_applicable"}` is indistinguishable from laziness: a reviewer asking
  "not applicable because what?" gets nothing back. The arm names what *is* there — corpus,
  release, scenario id — so the claim is checkable. This is ADR-0001's reason for rejecting
  a bare mask: the reason travels with the state.

| `simulated` field | Use | Why |
|---|---|---|
| `tool_name` | Required | The simulator's identity. |
| `tool_version` | Required | Free-form string, **deliberately not** validated as `MAJOR.MINOR.PATCH`. `metric_version` is semverish because Alfred controls it; a vendor ships `2024 R2` or `7.3.0-hotfix4`, and forcing a grammar here would force a lie into the one field the regulation names. **The asymmetry is deliberate — do not unify them.** |
| `config_digest` | Required | ACS-1 digest under the new record type `alfred.upstream_config`, over the canonicalized configuration document. |
| `tool_build` | Optional | Commit or build id where the vendor publishes one; most do not. |
| `config_ref` | Optional in schema, required by policy where re-derivation is claimed | Locator for the stored configuration. **The digest commits; the ref retrieves.** A digest with no retrievable preimage proves nothing was altered and lets nobody reproduce anything. |

**Why a digest and not the configuration inline.** A real run's configuration is large and
vendor-shaped — scenario, weather, sensor models, solver settings, seeds. Inlining it puts
an unbounded, un-normalizable vendor document inside every stamp's preimage. Digest-and-
store is the split ADR-0003 already makes.

**Why this is the right unit, and a trajectory digest is not.** A trajectory digest
identifies the **output**. `tool_name` + `tool_version` + `config_digest` + a retrievable
`config_ref` identifies the **producer and its setup**, which is what Annex III Part 4
names: storage of every toolchain version used, and traceability from M&S output back to
setup. The trajectory digest keeps its existing place inside `input_hash`'s payload. It is
the other half, not a substitute.

**The `unknown` reason codebook** is a small closed set of names —
`UPSTREAM_NOT_RECORDED`, `UPSTREAM_TOOL_UNDECLARED`, `UPSTREAM_CONFIG_UNAVAILABLE` — under
ADR-0002's discipline: **names on the wire, never integers, never reused, never
repurposed.** It needs no version field of its own and no schema bump to grow, because
adding an allowed value changes no existing stamp's digest. Only removing or repurposing a
name would, and both are forbidden. A verifier meeting a name it does not know applies
ADR-0002's `255 UNKNOWN_CODE` rule: the digest still verifies, because it is over the name
string — but the verifier **must not** report "upstream known".

**No fourth arm.** Recorded real-world sensor data gets none, because Phase 0/1 is
CommonRoad plus the CriMe oracle, and inventing an arm for a case with no implementation is
the error of writing a document before its evidence exists. Adding a fourth arm later is a
`stamp_schema_version` bump — cheap, and the entire point of settling this now.

### The honest limit, stated so it is not overclaimed

**Alfred's container never observes the simulator.** `tool_name`, `tool_version` and the
configuration are **declared by whoever ran the run**. The stamp commits to a declaration,
not to a fact — the same shape as the defect this project already identified in Ansys
Minerva, where *"solver version is a user-declared job field rather than an attested
fact"*.

What Alfred adds is real and worth exactly its actual size: the declaration is inside the
digest, so it cannot be changed afterwards without breaking the chain, and it is bound to
**a specific number** rather than to a file. Minerva's unit of provenance is a file;
Alfred's is a metric value.

**Alfred makes the declaration tamper-evident. It does not make it true.** No customer
document, demand-gate conversation or assessment conversation may say otherwise. D30's
phrase "upstream toolchain identity" is amended to read "as declared".

### Versioning mechanics

**A version bump does not preserve a digest, and is not meant to.** A v1 stamp's digest is
computed over v1's key set including `"stamp_schema_version":1`; a v2 stamp has a different
key set and a different digest. They are different documents, possibly about the same
computation.

**What is preserved is the ability to recompute a v1 digest, forever. That is this
mechanism's real and permanent cost:**

> Every superseded stamp schema version's encoder remains implemented and test-vectored for
> as long as any stamp under it exists. `harness/acs/` gains per-schema-version stamp
> vectors; when v2 lands, v1's vectors are frozen and never regenerated, and CI asserts they
> still pass. This is ADR-0004's "the vectors are the specification", applied to the stamp
> shape rather than to the float grammar.
>
> **No stamp schema version is ever retired while any stamp under it exists.**

**The property obtained — the reason this ADR exists.** Given a stored stamp and its
digest, a verifier reads `stamp_schema_version`, selects **that version's** encoder, and
recomputes. Match → authentic, old shape. Mismatch → tampering. **The encoder is chosen by
the document, not by the verifier's build, so a legitimate schema change can no longer
present as tampering.**

**Cross-version collision is structurally impossible, and the record type therefore stays
constant at `alfred.result_stamp`.** The preimage is
`ACS_VERSION 0x00 record_type 0x00 canonical_bytes`. Any v1 document carries
`"stamp_schema_version":1` and any v2 carries `"stamp_schema_version":2` at the same key;
ACS-1 canonical form is injective on documents; the canonical bytes differ, so the
preimages differ. Versioning the record type to `alfred.result_stamp.v2` would duplicate a
guarantee already complete from the content and create a second place to bump — which is a
second place to drift. Recorded here so it is not added later as a courtesy.

### What a verifier does with a schema version it does not recognise

**Not "ignore the unknown fields."** Two reasons, the second sharper than the first.

**It does not fail cleanly.** The unknown fields are *inside the digest*. A verifier that
strips them and re-encodes cannot reproduce the preimage, computes a mismatch, and a naive
implementation reports that mismatch as **tampering** — the exact incident this ADR exists
to prevent, relocated from the writer into the reader.

**Where it can verify, it verifies without reading.** A verifier hashing the raw stored
bytes will report VERIFIED while silently discarding every field it did not understand.
Suppose a future v3 adds `upstream_attested: false`: an ignore-unknowns verifier returns
"verified" for a stamp whose single most important qualifier it never read. **That is
ADR-0001's plausible-wrong failure relocated into the verifier**, and it is worse than
ADR-0001's case because it wears the word "verified".

| Condition | Verdict | Maps to (Failure Semantics) |
|---|---|---|
| Version known and implemented, digest matches | `VERIFIED` | `pass` |
| Version known and implemented, digest differs | `MISMATCH` | `fail` |
| `stamp_schema_version` above the verifier's highest known | `UNVERIFIABLE(SCHEMA_TOO_NEW)` | `indeterminate` |
| At or below the highest known but not implemented | `UNVERIFIABLE(SCHEMA_RETIRED)` | `indeterminate` |
| `stamp_schema_version` missing, non-integer, or below 1 | `INVALID` | `fail` |

- **`UNVERIFIABLE` is never `MISMATCH`.** "I cannot check this" and "this failed the check"
  are different findings, and here the difference is between *upgrade your verifier* and
  *you have been tampered with* — an incident-grade misreport, and the default behaviour of
  every naive hash comparison.
- **`UNVERIFIABLE` is never `VERIFIED`, and is fail-closed at the product boundary.** A
  result whose stamp cannot be verified does not ship as verified.
- **`SCHEMA_RETIRED` should be unreachable**, since retirement is forbidden while stamps
  exist. It is specified so that reaching it is loud.
- **A missing `stamp_schema_version` is `INVALID`, not `UNVERIFIABLE`.** A document without
  the pinned field is not a stamp; treating it as an old one would resurrect the
  unversioned eight-key shape as a permanent implicit version zero — which zero persisted
  stamps lets us refuse outright.
- **Every `UNVERIFIABLE` carries the verifier's own highest known version**, or the
  operator cannot act on it.

### Migration

**None.** Verified, not assumed: four `migrations/*/versions/` directories containing only
`.gitkeep`, no Alembic revision in the tree, no stamp table, two test fixtures. **Zero
stamps have ever been persisted**, so no record exists under the eight-key shape and none
ever will. This is the entire reason the decision had to land before any Phase 0 code.

### Consequences and enforcement

- `ResultStamp` freezes at ten keys; the published ACS-1 vector suite is extended to cover
  the v1 shape, all three `upstream` arms, and the two-stage read.
- A new domain-separation record type, `alfred.upstream_config`, is allocated.
- CI asserts: `stamp_schema_version` is present, top-level and integer in every emitted
  stamp; no stamp model makes an `upstream` arm's required field optional; every superseded
  schema version's vectors still pass; the record type is not versioned.
- `failure-semantics` gains the `UNVERIFIABLE` rows; `audit-and-retention-policy` gains the
  obligation that a `config_ref` remains retrievable for as long as the stamp it belongs to
  is live, and the restore drill gains a case for it.
- **Cost accepted:** one encoder per schema version, kept forever, with frozen vectors. That
  is the price of making a schema change distinguishable from tampering, and it is paid in
  maintenance rather than in trust.
```

## ADR-0007 — Executor-premise assertions may pass vacuously, and that is a third outcome

**Date:** TBD · **Status:** Accepted · **Supersedes:** none

C1–C3, C5 and C10 of the Sandbox Specification are written to pass harmlessly if the feature
they disable does not exist. That argument holds for an absent feature and fails for a misnamed
one. C2's two conjuncts (configuration disabled; zero condensation-class events) and C3's three
are not independent: each rests on the executor's own vocabulary for keys and event classes,
which is unverified first-hand. A single wrong name defeats every conjunct at once and the
assertion reports `passed` while the hazard occurs.

Failure Semantics distinguishes a check that failed from a check that did not run. This is a
third state: **executed, passed, possibly vacuous.** Until the executor source is read at the
pinned SHA, C2 and C3 are recorded as `passed (unverified vocabulary)` rather than `passed`, and
a run under that state is admissible for build work and **not** admissible as a measurement
under I16 or T10.

**Discharged by:** reading the executor at the pinned commit SHA and recording the exact
configuration keys and event class names, after which this ADR is superseded.

## ADR-0008 — The operator's browser talks to one origin, and read-model output is untrusted

**Date:** 2026-08-15 · **Status:** Accepted · **Supersedes:** none

### Context

Mission control is split (D51): the command surface is inspector, the read model is
factory and agents may build it. The split's operative rule is that the read model may
not be the source of any fact an action depends on. That rule is usually read as being
about which query supplies which field. It is not sufficient at that reading, because the
two halves must compose into one page that a human decides on.

Three compositions were available. Two separate origins the operator navigates between
puts the decision on whichever page they are looking at — the exact failure the split
exists to prevent. A client-side fetch or iframe requires JavaScript, which D51 refuses,
and gives an agent-built page a frame inside the approval screen.

### Decision

**The browser loads pages from the command surface only.** The command surface
server-side fetches HTML fragments from the read model over loopback and splices them
into a page whose decision-critical zones it rendered itself. The read model is a
subordinate service, never a peer the browser trusts.

**Read-model output is untrusted content, on the same footing as a commit message or
agent prose.** It passes the A10 scan and is re-serialized through an element and
attribute allowlist admitting no `style` attribute, no `<script>`, `<style>` or
`<foreignObject>`, no event-handler attribute, and no `id`/`class` outside a reserved
prefix. Decision-critical zones render first in DOM order and contain no read-model
content. A strict CSP applies.

**The named attack is an overlay:** an agent-authored fragment that positions itself over
the verdict and renders a `fail` as a `pass`, defeating every control beneath it while
leaving all of them intact.

### Consequence, and what makes this checkable

**The dark-read-model test.** With the read model stopped, every review page must still
render its decision-critical zones and permit `approve` on a `pass`. Zones 4 and 5 render
as unavailable; the decision remains possible. If it does not, a fact an action depends
on came from the read model and the split has been violated.

This is the only executable assertion that the boundary is real rather than declared, and
it doubles as a test of D22's own claim — that the criterion and evidence bundle, not the
diff, are what a decision rests on. If a review cannot be completed with the diff summary
unavailable, D22 is wrong, and that is worth discovering.

### Rejected

An iframe with `sandbox=""` on a distinct loopback origin closes the overlay attack too,
but needs JavaScript for layout and adds a cross-origin surface for no gain over
sanitization. Rendering the whole page from the read model and having the command surface
supply only the forms was rejected outright: the verdict would then be agent-rendered.

---

## ADR-0009 — The grant matrix is asserted by set equality, and converging by REVOKE strips ownership

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

Recorded under major-fix #8: `harness/db/assert_grants.py`, `harness/db/grants_declared.py`
and the two `migrations/roles/` files are inspector, agent-drafted, and therefore
admitted only under line-by-line human review with a mandatory ADR. This is that ADR.

### Context

`data-architecture.md` specifies the matrix and required the assertion to compare by
**set equality, never subset**, because a subset check passes on every extra grant and an
extra grant is the only kind of grant defect that fails in the safe-looking direction.
The document has said so since it was written; nothing enforced it, because the first
migration did not exist and a table-driven grant script over zero tables grants nothing.

Two implementation questions had no answer in the document, and one defect was found by
running the thing rather than reading it.

### Decision

**Equality, not predicates.** N1, N2, N3, N4, N5, N7 and N8 are not checked individually.
A grant that must not exist is a grant that is not declared, and an undeclared grant is
reported as `EXTRA`. Ten predicates catch the ten things somebody thought of; an equality
catches the eleventh. N6, N9 and N10 are not grants and are checked by name.

**Owner self-grants are excluded, on both sides.** Postgres materialises an owner's own
privileges into an object's ACL as soon as anything is granted, so an owner is its own
grantee everywhere it owns. That is ownership, and ownership is compared separately.
Excluding it on the observed side alone produced twelve `MISSING` tuples that were not
missing — the four migrators' declared grants on the version tables they own — so the
rule is applied to the declaration too. **What this gives up is stated rather than
implied:** the assertion no longer checks that a migrator can write the version table it
owns. Alembic's first upgrade checks that, loudly.

**No YAML library.** `grants.yaml` is read by a parser for exactly the constructs it
uses, which raises on any line and any top-level key it does not recognise. Same reason
`lint_docs.py` parses frontmatter by hand: the parser guarding the grant matrix should
not depend on the supply chain the grant matrix exists to bound. The cost is real — that
parser is now a thing that can be wrong — and it is paid down by the parser failing
closed rather than skipping.

**`grants.yaml` goes to version 3** with a `default_privileges` section. `002_grants.sql`
has issued `ALTER DEFAULT PRIVILEGES` since 2026-08-16 and the declaration named none, so
under equality every one of them read as `EXTRA`. N8's rule — no default privilege to
`PUBLIC` or to an unnamed role — is weaker than declaring them and comparing.

### The third omission, and it is the same one twice more

`002_grants.sql` converges by revoking everything from every named role before granting
anything, which is correct and is what makes re-application idempotent. **A schema owner
holds `USAGE` and `CREATE` implicitly only while the schema's ACL is null.** The revoke
makes it explicit and the implicit privileges go with it. So the owner of `product` could
not create a table in `product`:

```
permission denied for schema product
LINE 2: CREATE TABLE product.scenario (
```

`migration_meta` was already granted explicitly, on 2026-08-16, for precisely this
reason — and that fix was written as a special case about Alembic's version table rather
than as the general fact. The general fact is that converging by `REVOKE` removes
ownership's implicit grants, so every owner's schema privileges must be re-issued
explicitly. All five are now issued explicitly, which is also the better end state: an
implicit privilege is one no assertion can read.

This is the third omission of the same class in two days, all three of the same shape —
a privilege the matrix never mentioned, failing **loud** rather than silent. The document
already draws the moral and it is now carried by three instances: *a matrix reviewed only
for what it grants too much cannot catch a matrix that grants too little.*

### Consequence

Excluding owner self-grants means the assertion cannot see the defect above, so it is
asked directly: `has_schema_privilege(owner, schema, 'CREATE')` for every named schema,
reported as an `OWNER` violation. `has_schema_privilege` is version-independent, which
spelling out an owner's materialised ACL bitmask is not — `MAINTAIN` exists from
Postgres 17, and hardcoding `arwdDxtm` would pin the assertion to a major version.

The suite carries two mutation controls, committed beside it: an extra grant to
`alfred_agent` must be reported `EXTRA`, and a withdrawn grant to `alfred_harness` must
be reported `MISSING`, each issued and reversed inside `try/finally` with the cluster
re-checked afterwards. Every denial asserts `SQLSTATE 42501` and is paired with the
identical statement by the role that should hold the privilege — a denial with no
matching permission is a denial that proves the object exists nowhere.

### Rejected

**Declaring owner self-grants and comparing them.** It would have made the `OWNER` check
unnecessary, at the cost of encoding Postgres's per-version owner privilege set into the
expansion. A control that has to be updated on a server upgrade is a control that reports
a false failure on the day nobody has time for it.

**Adding PyYAML.** One dependency, in the closure of the module whose job is to bound
what the cluster trusts, to read a 200-line file with eight top-level keys.

---

## ADR-0010 — The evidence chain, and the fork the constraint did not close

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

### Context

`EvidenceStore` is the first inspector port to exist. D43 requires evidence rows
hash-chained with each row carrying its predecessor's digest; D5 requires the store be
written by the harness and never by the agent; S7's restore drill requires the walk be
asserted **total** — one head, no forks — because a check that verifies each link but
never checks they form a single path passes on a forked audit log.

Three things the specification left to implementation, and one it got wrong.

### Decision

**The link digest is a module-level function, not a method.** `link_digest(chain_id,
record_type, prev_sha256, body_sha256)` over ACS-1 with its own domain separator
`alfred.evidence.chain_link.v1`, distinct from every body separator. An external auditor
recomputes the chain from the stored columns without instantiating anything, which is the
only reason the chain is worth having. A separator distinct from the body's is what stops
a link and a body of coincidentally identical content colliding.

**The head is derived from the links, never from a timestamp.** The head is the row whose
digest no other row in the chain points back to. Ordering by `created_at` would pick
arbitrarily between two rows written in the same microsecond and fork the chain; and the
query returning more than one row *is* the fork, raised on every append rather than
discovered at audit time.

**`verify_chain` asserts three separate things**, and the third is the one usually
skipped: every link recomputes, there is exactly one genesis, and the walk visited every
row that exists. The third is reachability rather than link integrity — an island whose
predecessor was deleted has perfect links.

**Autocommit is refused at construction.** The chain is serialized by a
transaction-scoped advisory lock, which under autocommit is released the instant it is
taken. Every append would look correct and two writers would race for the same
predecessor; the unique constraint would still refuse the fork, but as an integrity error
at some unrelated call site.

**Who may write what is not re-checked here.** The store takes whatever connection it is
handed and the grant decides. A second copy of a control the database already enforces is
the copy that drifts.

### The fork the constraint did not close

`0001_evidence_base` declared `UNIQUE (chain_id, prev_sha256)` and the migration's own
comment claimed the chain "physically cannot fork". It cannot, except at row one.
**Postgres treats NULLs as distinct in a unique index**, so the constraint refuses a
second row on an existing predecessor and accepts a **second genesis** — two rows with
`prev_sha256 IS NULL`, a fork at the one position where both individual links still
recompute perfectly. Found by writing the test that expected the constraint to refuse it
and watching the insert succeed.

Corrected to `UNIQUE NULLS NOT DISTINCT`, which Postgres has since 15 and the pinned
image is 17.6. The walk's totality check already caught this case, but **catching is not
preventing**, and the reason the constraint is in the cluster at all is that a writer
which never runs the Python check cannot produce one.

This is the same class as the three grant omissions in ADR-0009: a rule stated for the
general case with the boundary case unexamined, and in each instance the boundary case is
where the NULL, the owner, or the empty set lives. Worth naming as a pattern rather than
as a fourth coincidence — **the constraint reviewer's habit of reading the general row
and not the degenerate one is now four for four.**

### Consequence

The mutation control is committed beside the test: remove `postgresql_nulls_not_distinct`
from the migration and `test_second_genesis_is_refused_by_the_cluster` is the only thing
in the repository that fails. Verified by applying and reverting the mutation.

**What the Python re-walk does not prove, stated so no drill quotes it as more than it
is.** `verify_chain` recomputes every link with the same encoder that wrote the rows, so
it is checked against itself. It detects a row mutated after the fact and it detects a
fork. It does not validate the encoder. The independent check remains the JavaScript
re-walk in the restore drill (S7), and this method is not a substitute for it.

### Rejected

**A Python-side fork check in place of the constraint.** A check in the writer is a check
a second writer does not run, and the second writer is the case the property exists for.

**`hashtext()` for the advisory-lock key.** An undocumented internal whose output has
changed across major versions — a lock key that changes on upgrade serializes nothing on
the day of the upgrade. The key is the chain id's SHA-256, truncated to a signed int64.

**Re-declaring the verdict vocabulary in Python.** It is a check constraint on the table.
A value this code rejected but the database accepted would mean the two disagreed, and
the database is the one still true after a code change.

---

## ADR-0011 — The criterion subprocess computes; the runner compares

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

### Context

A8 requires ground truth the agent did not author **and cannot retrieve**. The register
says held-out reference values are "injected by `CriterionRunner` at verdict time", and
the obvious implementation is to write them into the criterion environment so the
criterion can assert against them.

That implementation is wrong, and it is wrong in the way the architecture exists to
prevent. **Agent-authored code executes in the criterion environment.** A held-out value
placed there is a value the code under test can read and return, and a stub doing exactly
that passes every held-out point — every P3 resample, every P4 invariance, every P5
degeneracy — with a clean transcript and no dishonesty anywhere in the loop. It is D50's
delegation failure moved one layer in, past the oracle-absence probe, which asserts a
module is unimportable and says nothing about a JSON file sitting in the working
directory.

### Decision

**The subprocess computes; the runner compares.** The held-out command is a *harvest*: it
produces the candidate's outputs and asserts nothing. The comparison against reference
values happens in the runner process, which holds `alfred_criterion` and sits outside the
environment (A1). Nothing that knows an expected value ever runs beside the code being
measured.

The visible criterion is the opposite and may assert inside the subprocess. Visible values
are legitimately in agent context — that is the entire distinction D49 and D33 rest on.

**Four supporting decisions, each closing a way the composition lies:**

**The exit code is corroboration, never the verdict.** An exit code cannot distinguish
"every check passed" from "no check ran", and the second is what a vacuous criterion looks
like from outside. The command writes a mandatory report; zero checks run is
`did_not_run`. An exit code disagreeing with its own report is also `did_not_run` — two
readings of one run that contradict each other, where picking the convenient one is how a
harness reports on its own health.

**F4 is `indeterminate` and never a pass on visible criteria alone.** Reachability is
passed in explicitly rather than inferred from an empty point list: "no points were
configured" and "the points could not be read" are different facts and only one is a
harness fault.

**Both grading arms are tagged.** A `0.0` against an `Undefined` reference is a mismatch,
not a near miss — the E1/E7 collapse a float-coercing comparison would score as a small
error.

**The provenance tier recorded is the weakest present, not the strongest.** *Taken here,
not read from D49, which says "the held-out point's tier" in the singular.* A task graded
by one P1 and one P4 point is recorded P4: an invariance point fixes a result's shape and
never its level, so quoting the stronger tier would overstate what the verdict rests on to
a gate that stratifies by it.

**There is no `patch is None` branch.** A do-nothing run takes the same path as every
other run and fails on the merits at score zero. Short-circuiting would make the
null-agent floor a code path rather than a measurement, and F3 — the floor run plus a
collection-forcing `conftest.py` — must traverse identical code to test A1's claim at all.

### Materialization

A1 is implemented as **allowlist-then-copy**, never copy-then-delete. The direction is the
property: copy-then-delete materializes the attack and then tries to remove it, which
depends on the remover's list being complete and leaves a window. Symlinks are refused
rather than resolved, on every path component and not only the leaf; escapes, absences and
double-declared paths are refused; the manifest of what crossed is path-to-digest and is
recomputable from the destination tree.

One layer **is** enumeration and is labelled as such in the code: import-hook filenames are
refused from the candidate side even where a declaration would admit them. It is not the
boundary. It exists because the allowlist's strength is its granularity — a task declaring
one file admits no `conftest.py`, one declaring a directory might — and it is defence in
depth over a structural control, which is the only position enumeration is safe in.

### Consequence

The suites assert absence rather than blocking. `test_undeclared_sibling_does_not_cross`
uses an ordinary filename deliberately: a suite testing only the `conftest.py` case would
be satisfied by a filename ban and would go green on the day the enumeration stopped being
complete.

`test_held_out_values_never_enter_the_environment` runs a probe that reads every file in
the materialized tree and reports whether the reference value appears. **Its first version
scanned everything, found the sentinel in the comparison literal it was itself compiled
from, and reported a leak.** The probe now skips its own source. Recorded because it is the
same failure as the unsalted prefill measurement and the double-encoded report helper found
in this same session: the instrument measured itself.

### Rejected

**Injecting held-out values as environment variables or a data file.** The whole subject of
this ADR.

**Special-casing `patch is None`.** Above.

**Trusted-wins on a materialization collision.** It would let a candidate name a criterion
file and have the overwrite read as success. Candidate-wins is the attack. Refusing is the
only answer that reports what happened.

---

## ADR-0012 — The verdict boundary is a lint, and the lint fails when it has nothing to check

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

### Context

D16 says agent nodes are schema-forbidden from writing verdict fields. The verify pass
established that **LangGraph raises only on *concurrent* unreducered writes** — a
sequential write to a verdict field raises nothing — so D16 is a convention unless
something checks it. D39 draws the conclusion: the boundary is physical, and the security
property comes from port separation rather than from inspecting field names at runtime.

Two thirds of that are enforced elsewhere. The separate process is a process; the separate
role is a grant, asserted by `assert_grants.py`. The **import path** was enforced nowhere.

### Decision

`scripts/lint_verdict_boundary.py`, three checks in three directions:

**V — vocabulary.** No module in the agent-writable tree declares `verdict`,
`held_out_result` or `indeterminate_reason`, or returns a type naming one. A return
annotation enumerating `pass`/`fail`/`indeterminate` is a verdict type whatever it is
called, so the literal set is checked too — a name check alone misses `-> Literal["pass",
"fail", "indeterminate"]` on a function called `classify`.

`score` is deliberately **not** in the vocabulary. It is an ordinary word a metric module
may legitimately use, and a lint that fires on ordinary words gets disabled rather than
obeyed.

**I — the agent tree must not reach a verdict module, transitively.** The transitive part
is the whole check: a one-hop version passes on `agent_node -> helpers ->
evidence.store`. Violations print the full import trail.

**R — a verdict module must not reach the agent tree.** The reverse direction, and the one
that gets forgotten. `CriterionRunner` executes candidate code as a subprocess and must
never import it — an import puts agent-authored code inside the process holding the
`heldout` credential.

**`harness/acs` is not a verdict module, deliberately.** `src/provenance/encoding.py`
imports the ACS-1 encoder and that edge is correct: there must be exactly one canonical
form, and a second encoder in the product tree would be a second canonical form. A rule
banning all of `harness/` would forbid the one import the architecture requires.

### The vacuity guard, which is the reason this ADR exists

**A check that scanned zero files fails rather than passes.** Today the V check has no
agent-invoking node to look at, because no graph exists. Without the guard the lint would
report green for a reason that has nothing to do with the property — and would keep
reporting green on the day the first agent node lands in a directory the globs do not
cover. The summary line prints the file and module counts for exactly this reason: `V=12,
I=12, R=10` is a claim someone can check; `OK` is not.

This is D57 applied to a lint rather than to a suite, and it is the fifth instance in this
project of the same underlying failure — an instrument trusted before it was checked.

### Consequence

`--self-test` is a committed mode of the lint itself rather than a separate test file, so
it travels with the thing it controls: a negative control in another directory is a
control someone deletes without noticing what it was for. It plants three violations, and
its clean control is a function called `score_of` returning `float` — deliberately
adjacent to the vocabulary, because a control using an obviously unrelated function would
not notice a check that fired on any annotated return at all.

Both import checks were verified by mutation against the live tree, not only against
fixtures: an import of `harness.evidence.store` added to `harness/acs/acs1.py` produced
`provenance.stamp -> provenance.encoding -> harness.acs.acs1 -> harness.evidence.store`, a
four-hop trail no one-hop check would have seen; an import of `metrics.value` added to
`harness/criterion/runner.py` fired R. Both reverted.

Wired into CI as two steps, the lint and its self-test, because a lint whose control is
not itself run is a lint that reports the same thing whether it works or not.

### Rejected

**Enforcing this inside the graph engine.** It is the thing that was measured not to work,
and it is why D39 exists.

**Banning `harness/` wholesale from the agent tree.** Above — it forbids the ACS-1 import
that keeps one canonical form.

**Including `score` in the vocabulary.** A lint that fires on ordinary words is a lint
that gets suppressed, and a suppressed lint enforces nothing while looking like it does.

---

## ADR-0013 — Containment probes, and the control that stops each one reading green

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

### Context

S6 builds two of the fifteen boot assertions: C6, the egress canary (A7), and C7, oracle
absence (D50/D54). Both are assertions about the *absence* of something, and an
absence-assertion is the easiest kind to satisfy vacuously — a probe that cannot run, a
target list that is empty, an enumeration that found nothing because it looked nowhere.

### Decision

**`not_executed` is a first-class outcome and `require_all_passed` treats it exactly as
`failed`** (F25). An absent assertion is also a failure, not a skip: an assertion nobody
ran and one nobody wrote are indistinguishable from the dispatch side, and both mean the
control was not applied.

ADR-0007's fourth outcome — executed, passed, and **vacuous** — is deliberately not
representable in the enum, because an assertion cannot know from inside that its own
premise is misnamed. It travels instead as `premise_verified=False`, and
`AssertionReport.unverified_premises` is what a reader consults before quoting a green
report as evidence.

**The canary runs a loopback control first.** A probe reporting "the target was
unreachable" reports the same thing when egress is blocked and when its own socket layer
is broken. Control failure yields `not_executed`, never `passed`.

**The canary policy must declare at least one IP-literal target.** A canary whose every
target is a DNS name reports identical green on a firewalled container and on one with an
empty resolver and every port open. The loader refuses a policy without one, and refuses a
policy with no targets at all — a canary with nothing to try passes unconditionally.

**The oracle probe uses `find_spec` and only on top-level names.** Importing a module to
learn whether it is importable executes its module-level code inside the sandbox.
`find_spec("a.b")` imports `a`; `find_spec("a")` imports nothing, so the top-level
restriction is load-bearing rather than incidental.

**Zero interpreters and zero scanned paths are both `not_executed`.** A probe with nothing
to probe reports what a clean probe reports.

**The denylist records a reason per entry, as data, inside the digest.** D54 calls the
classification a recorded human judgement. Reasons as comments would sit outside the hash,
so a silent reclassification would not invalidate a single autonomy grant measured under
the old one. `permitted_substrate` is loaded too: a package in neither set is
**unclassified**, and the closure check reports that separately from denied, because "we
have not looked at this one" and "we looked and it carries no measure" are different facts
and only the second is a decision.

### What these probes do not close

Named here because a green report will be quoted. The canary proves the named targets are
unreachable; it does **not** prove a policy is the reason, since a container with no
network interface passes identically. Distinguishing them needs a reachable allowlisted
host, and the Phase 1 allowlist is empty by design.

The oracle probe closes acquisition, declaration, presence and naming. It does not close
**meaning**: a renamed, reformatted vendored copy passes it, as do a shared object reached
through `ctypes`, a subprocess binary, a data file of constants, and reconstruction from
model weights. These are D50's already-recorded open holes and none is closed here.

### Two findings from running it

**`python*` is not an interpreter glob.** On the first real machine, discovery matched
`python3.14-config` — a shell script that exits 1 on an unrecognised flag — and the probe
correctly refused to read "could not run" as "nothing found", reporting `not_executed` for
an entire clean container. Fail-closed working perfectly on a set that should never have
contained the member. Deciding what is *in* the interpreter set is a different question
from failing closed on a member that cannot be probed, and collapsing them makes the probe
unusable. Membership is now an explicit name rule with its own test.

**Three suites were not in CI.** `harness/evidence`, `harness/criterion`,
`harness/containment` and `harness/lane` were all absent from `gates.yml` — built,
passing locally, and gating nothing. Added. Worth recording as a class: every new suite in
this project has needed a separate, easily-forgotten act to become a gate, and nothing
checks that a test directory is reachable from CI.

### Consequence

Each claim is mutation-controlled, verified by applying and reverting: reading
`not_executed` as passed fails exactly `test_not_executed_is_treated_as_failed`; replacing
`find_spec` with `__import__` fails exactly
`test_a_denied_module_on_the_import_path_fails`, because the planted module raises at
module level and the probe's fail-closed path converts it to `not_executed`; removing the
loopback control fails exactly `test_canary_is_not_executed_when_its_control_fails`.

The canary suite owns its own listener rather than using the machine's network, because a
canary suite depending on connectivity passes on an unplugged laptop — the one condition
under which a canary proves nothing. Run against the real policy on the development host,
the canary correctly reports **FAILED**: `1.1.1.1:443` and `pypi.org:443` are both
reachable there, which is the same finding Anthropic recorded in their own harness.

### Rejected

**Filtering non-interpreters by swallowing their probe failure.** It would make every
genuinely unprobeable interpreter invisible, which is the failure the fail-closed rule
exists for.

**Treating any `.pth` as a failure unconditionally.** A developer virtualenv legitimately
carries them, and a probe that cannot be run outside the container is a probe nobody runs
until it matters. `strict_import_hooks` is the parameter, True inside the container, and
both branches are tested.

---

## ADR-0014 — The chain is re-walked by the implementation that did not write it

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

### Context

D43 requires evidence rows hash-chained with the head anchored off-machine daily, and a
restore drill as an executable check. §6 of the harness self-test specification adds the
constraint that decides the design: **a drill using the Python encoder to check a chain
the Python encoder wrote is checking nothing.**

### Decision

**The re-walk is `harness/evidence/verify_chain.mjs`, stock Node, no dependencies.** Same
argument as `acs1.mjs` and the same reader: the claim Alfred sells is that a third party
recomputes the digests without running Alfred's code, and a claim only ever checked by its
own author is an assertion.

**The exporter computes nothing.** `export.py` selects stored columns and writes them out.
Any digest or derivation there would be a Python claim the independent implementation then
re-checks against itself. It is allowed to know which columns exist; not what they contain.

**The walker holds its own table-to-separator map, duplicated deliberately.** `verdict` and
`operator_action` carry no `record_type` column — their record type is the table. Putting
it in the export would mean Node recomputing digests from a separator Python chose. Two
maps that disagree make every digest mismatch, which is the loud failure and the right one.

**The anchor's head is derived by the walker, not by Python.** If Python derived it, an
encoder defect would produce a wrong anchor and a later restore would agree with it
perfectly. The anchor's *authority* comes from being written before any compromise and
living where the live machine cannot reach; its *content* comes from the non-Python
reading.

**The drill restores into a second cluster and refuses to restore into its source.** A
drill whose failure mode is the incident is not a drill.

**Data-only, into a cluster whose schema came from the migrations.** This separates "the
schema is what the migrations say" from "the rows are what the backup holds". A restore
bringing its own schema can bring back a *different* schema — an evidence table with a
dropped column, a missing check constraint — and every row lands in it without complaint.

**Comparison three is done by JavaScript.** The specification lists four: row counts,
primary-key set equality, per-row content hash against the stored digest, and the full
re-walk. The third recomputes a digest, so a Python version would check the encoder
against itself. Python does the two that are not digest claims; Node does both that are.

### What the second implementation caught, immediately

Writing the walker against a plain JavaScript object failed at the first row:
`acs1.mjs` refuses object literals outright, because JavaScript cannot distinguish `1`
from `1.0` and the encoder demands a representation that carries the distinction. The
digest input is a `Map`. Every value in it is a string or `null`, so nothing here needed
`f64()` or `BigInt` — **and the refusal still earned its place**, because the alternative
was a walker that produced digests which happened to agree with Python today.

### Two findings recorded rather than skipped

**No Tier 0 recovery objective exists.** `grep` over Tier 0, Tier 1 and Tier 6 returns
nothing for RPO, RTO or "recovery objective". The specification's instruction is to record
the number and treat the absence as a finding, never a skip — so the drill emits the
measured restore wall-clock alongside `no Tier 0 recovery objective exists to compare it
against`, and the test asserts that finding is present. It becomes an operator item.

**Artifact resolution is unexercised.** No artifact store exists, so no `evidence.artifact`
rows are restored and the resolution check has nothing to resolve. Reported as a finding
rather than passing: an unexercised check reports what a clean check reports.

The drill test asserts the finding set **exactly** — `len(findings) == 2` — so a third
finding fails the gate and either of these two disappearing does too. A drill that
accumulates tolerated findings is a drill that stops being read.

### Consequence

Verified by mutation, applied and reverted. Changing Python's `LINK_RECORD_TYPE` to `.v2`
fails every walker test, which is what proves the two implementations agree because they
compute the same thing rather than because one was derived from the other. Removing
`chain_id` from the digest input fails the store's own suite as well.

`test_node_is_available` fails loudly when Node is missing, and Node is now a required step
in the database CI job. A drill that silently degrades to a Python re-walk when Node is
absent is a drill that checks the encoder against itself on exactly the machines nobody
looked at.

### What remains, and it is most of S7

This is **D-synthetic only**. A green CI run is not "restore verified" for Phase 0 exit —
that criterion means a recorded **D-production** run against the actual off-machine backup.
Also outstanding, and none of it is code in this repository: continuous WAL archiving, an
off-machine target, the daily anchor job, and **point-in-time recovery**. PITR matters more
than the omission looks: a drill restoring only to latest cannot distinguish a working WAL
archive from a working base backup with a broken archive, and PITR is the capability that
matters after the bad migration D43 names.

### Rejected

**A Python re-walk, with the JavaScript one as a later addition.** It is the thing the
specification forbids, and the version that exists first is the version that gets trusted.

**Marking the drill `slow` so it can be deselected.** A marker there is a switch for
turning off the only end-to-end restore check, against a gate whose absence is
unrecoverable data loss. It costs one extra throwaway cluster.

## ADR-0015 — A missing candidate file is the candidate's failure, not the harness's fault

**Date:** 2026-08-18 · **Status:** accepted · **Supersedes:** nothing · **Amends:** ADR-0011

### Context

S4's null-agent floor suite is specified to assert that a run taking no actions scores
**zero and verdict `fail`, never `indeterminate`** — because `indeterminate` is excluded
from the merge rate on both sides, so a do-nothing run recorded that way leaves the
denominator instead of landing in it at the floor.

On its first execution the floor suite did not produce a verdict at all. `materialize`
raised `MaterializationError: candidate path 'solution.py' does not exist`. A caller
receiving an exception from the materializer has been handed a harness fault, and a
harness fault is exactly what maps to `indeterminate`. So the null agent — the cheapest
and most likely degenerate case in the whole system — would have been scored as harness
flakiness and dropped from the measurement, silently, in the direction that flatters the
merge rate.

The original refusal was not wrong for no reason. Its test carried one: *"a declaration
naming a path that is not there would otherwise materialize nothing, and the criterion
would fail for a reason unrelated to the work — or pass vacuously."* That reasoning is
sound for the **trusted** half and does not transfer to the **candidate** half, and the
single check conflated them.

### Decision

The two halves of a declaration have different owners and now fail differently.

A missing **trusted** path still raises. The harness declared its own criterion and the
criterion is not there; that is a broken inspector and it must stop.

A missing **candidate** path is recorded in `Materialization.missing_candidate_paths` and
materialization continues. The criterion then fails on its own, because the file genuinely
is not present — what changes is that the failure is attributed to the candidate rather
than to the harness.

Absence is reported **only after every other refusal has run**. The absolute-path and
symlink-traversal checks execute first, so `allow_absent` cannot become a way to smuggle a
declaration past them by naming something that does not exist yet. That has its own test.

### Consequences

The floor suite now returns `fail` with score `0.0` and no indeterminate reason, which is
what it was specified to assert.

`Materialization` gains a field, so the manifest an auditor recomputes is unchanged while
the record of what the candidate did not produce becomes available to the evidence row.
Nothing downstream reads it yet; it is recorded because "the candidate declared a file and
wrote none" is not reconstructible afterwards from a tree that does not contain it.

The vacuous-pass hazard the original test named is not reintroduced: a candidate that
produces nothing materializes nothing, and the visible criterion fails at import. It was
never the raise that prevented the vacuous pass — it was the criterion.

### Why this is an inspector patch

`harness/criterion/materialize.py` is inspector machinery under D20. Major-fix #8 permits
an agent-drafted inspector patch only under line-by-line human review with a mandatory
ADR. This is that ADR; the review is O9 and has not happened. Until it does, the change is
landed but unreviewed, and that is the honest state to record.

### What found it

The floor suite, on its first run, before it had ever passed. Recorded because the value of
S4 is not that the two suites pass — it is that they fail against a runner that should
fail, and the first thing this one did was fail against a real defect in the code it
measures.

---

## ADR-0016 — `StampedResult` takes its schema version from the stamp it contains

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** ADR-0006 (which versions the stamp and is silent on the record that wraps it) · **See also:** ADR-0001 (the tagged `MetricValue` encoding is inside this record's preimage), ADR-0003 (`alfred.stamped_result` is the third domain-separation record type)

### Context

ADR-0006 gives `ResultStamp` a version for its own field set, and the argument it makes is
general: a provenance record whose key set can change without a marker turns a legitimate
schema change into something indistinguishable from tampering. It then versions exactly one
record.

`StampedResult` is a second structured record. It has its own domain-separation tag
(`alfred.stamped_result`), its own digest (`content_hash()`), and its own key set —
`{stamp, value}`. `value` is `MetricValue` in the ADR-0001 tagged form, and ADR-0001's whole
design permits a fourth arm. **The document ADR-0006 calls "the only shape in which a number
leaves the system" carried no version of its own**, so a new `MetricValue` arm, or any change
to how an existing arm canonicalizes, would move every stored `StampedResult` digest with no
marker distinguishing the old shape from the new. That is ADR-0006's defect, one level up,
found while implementing ADR-0006.

The window is the same window and it is still open. Re-verified 2026-08-18: four
`migrations/*/versions/` directories containing only `.gitkeep`, no Alembic revision anywhere
in the tree, no table holding a stamp or a stamped result. **Zero records of either kind have
ever been persisted.**

### Decision

`StampedResult` gains **no version key of its own.** Its schema version is the
`stamp_schema_version` of the stamp it contains, which is already inside its preimage, so a
reader two-stage-reads straight through: parse as ACS-1, read `stamp.stamp_schema_version`,
dispatch to that version's encoder for the whole record.

| | Option | Outcome |
|---|---|---|
| A | Give `StampedResult` an independent `record_schema_version` | **Rejected.** |
| B | Derive the version from the contained stamp | **Accepted.** |
| C | Leave it unversioned and record the gap for later | **Rejected.** |

**Why B rather than A.** The record has no independent shape axis. It is a stamp plus a
value, and both of its two keys are things ADR-0006 already governs: the stamp by its own
version, the value by an ADR-0001 arm set that cannot change without a hash-affecting
change. An independent version would be a second number to bump for every change that
already bumps the first — and ADR-0006 rejects versioning the *record type* on precisely
this ground: a second place to bump is a second place to drift. Applying that argument here
and not there would be inconsistent in the direction of more machinery.

**What option A would have bought, weighed honestly.** Genuine independence: a future change
confined to `MetricValue` could bump the wrapper without disturbing the stamp shape, and
`ResultStampV1`'s frozen encoder would not need reissuing for a change that does not touch
a stamp key. That is a real saving in one scenario. It is outweighed because the scenario is
rare — `MetricValue` has had three arms since ADR-0001 and a fourth is speculative — and
because the cost of A is permanent and paid on every change, while the cost of B is paid
only in that one scenario.

**The consequence accepted, stated rather than discovered later.** The two records' lifecycles
are now coupled: **a change to `MetricValue`'s tagged encoding is a `stamp_schema_version`
bump**, even though no stamp key changed. The bump is cheap by ADR-0006's own accounting —
one new frozen encoder module and one new frozen vector set — and it is loud, which is the
property being bought. Anyone tempted to avoid the bump by arguing "the stamp did not change"
is reading this paragraph.

**Why C was rejected.** Deferring spends the one free window. The migration cost of this
decision is zero exactly once, and it is zero for the wrapper at the same moment it is zero
for the stamp. A gap recorded in `## Open items` for later resolution would be resolved after
the first persisted record, when the cost is a migration plus an advisory naming affected
rows — the exact bill ADR-0006 exists to avoid.

### Consequences and enforcement

- `StampedResult.to_acs()` freezes at two keys, `{stamp, value}`. No version key is added.
- The record type `alfred.stamped_result` stays unversioned, for ADR-0006's reason.
- The vector suite gains `stamped-result-v1-defined` and `stamped-result-v1-undefined`, whose
  notes state that the nested `stamp_schema_version` is inside this record's preimage.
- CI asserts, via `tests/test_stamp_v1_vectors.py`, that the model reproduces both vectors
  byte-for-byte and digest-for-digest.
- A future `MetricValue` arm is a `stamp_schema_version` bump. Recorded here so that it is not
  argued away at the time.

### Why this is not an inspector patch

`src/provenance/stamp.py` is product code. The accompanying vector extension in
`harness/acs/gen_vectors.py` and the new `harness/stamp/verdict_map.py` **are** inspector
machinery under D20, and are landed citing ADR-0006's own Consequences list as the authorizing
record rather than a fresh ADR each: major-fix #8 exists to stop an agent changing the
inspector on its own judgment, and there the judgment is already recorded and human. The
line-by-line review is still owed. It is O9, it has not happened, and this ADR has not been
reviewed either.

### What found it

Implementing ADR-0006. The ten-key stamp was written, and the record wrapping it still had
eight characters of key set and no version. Recorded because the general argument was already
in the log and had been applied once rather than exhaustively — which is the failure mode
`## Open items` describes as the register discovering its own conditions unrunnable at their
deadline rather than before it.

---

## ADR-0017 — A containment assertion with an unread premise is a hole, and a hole never passes

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** ADR-0007 (which names the third outcome and does not say how it is represented or acted on) · **See also:** the Sandbox Specification's containment table, whose C1–C3 paragraph this contradicts and which is amended by this record

### Context

ADR-0007 established that C1–C3, C5 and C10 can be **executed, passed and vacuous**: each
rests on the selected executor's own vocabulary — configuration keys, event class names,
configuration search paths — none of which is in this repository and none of which has been
read first-hand. It recorded the state and prescribed a label: such assertions are recorded
as `passed (unverified vocabulary)` and a run under them is admissible for build work and
not as a measurement.

Two things were missing, and both were found while implementing the assertions.

**First, the state could not reach the thing that acts on it.** `premise_verified` existed on
`harness/containment/assertions.py`'s `Assertion`. The shape that travels on `SandboxHandle`
and that `Worker.check_handle` reads — `harness/worker/port.py`'s `AssertionResult` — had no
such field, and no converter between the two vocabularies existed at all. So ADR-0007's third
state was recorded on a report nobody consulted and invisible at the only gate that refuses a
dispatch. A distinction that cannot reach a decision is a comment.

**Second, ADR-0007 says nothing about an assertion that has no key name at all.** It presumes
a name exists and is unverified — taken from a research note. An assertion written before
anybody reads the executor has something weaker: a *hole*. The Sandbox Specification's own
answer to that case is at `sandbox-specification.md:125` and is the position this ADR
rejects: *"an assertion that harmlessly passes on a feature that does not exist costs
nothing."* True for an absent feature. False for a misnamed one, and false in the direction
that matters, because fifteen green assertions that mean nothing are worse than fifteen
absent ones — the green ones stop anybody looking.

### Decision

**1. A hole is a first-class object, and an assertion with an unread hole reports
`not_executed`.**

`harness/containment/shells.py` carries a register of `PremiseShell`s. Each names its claim,
its holes, and the check that runs once the holes are filled. `evaluate` refuses to call the
check while any hole is unread and returns `NOT_EXECUTED` with `premise_verified=False`.

`NOT_EXECUTED` rather than `FAILED`: nothing was checked, and reporting a failure would claim
the control ran and found a problem. F25 already makes `not_executed` a failure at every gate,
so the refusal is inherited rather than reimplemented — `check_handle` needed no change to
refuse a shell.

**Never `PASSED`, under any observation.** The suite asserts this against the *most
favourable* observation available — empty configuration, empty stream, empty everything,
which is precisely what a check would read as "nothing enabled, nothing emitted" and pass on.

**2. `UNREAD` is a sentinel and is not `None`, and an empty answer is an answer.**

A hole holding `()` means *the executor was read and has no such event class*. A hole holding
`UNREAD` means *nobody looked*. These are different findings and the first is a legitimate,
useful result. `None` was rejected because some executor configuration could legitimately hold
it, and a hole whose unread state collides with a legal value can be filled by accident. The
sentinel is falsy so that `if hole.value:` cannot misread it as present, and `.read` is the
only correct test.

This is the same distinction ADR-0006 draws between an absent optional field and a declared
blank, arriving independently in a different subsystem. Recorded as such because the pattern
recurring twice in one week is evidence it will recur again.

**3. `premise_verified` crosses to the handle, and `check_handle` gains an admissibility
argument.**

`AssertionResult` gains `premise_verified: bool = True`. `harness/containment/handle.py` is
the single crossing from probe vocabulary to handle vocabulary, one-way by design: there is no
`from_result`, because reconstructing a probe result from adaptor-supplied data is the shape
of every control that ends up checking a copy of its own input.

`check_handle` takes `admissibility: Admissibility`, and **the default is `MEASUREMENT`** —
the strict end. Under `MEASUREMENT` a required assertion with `premise_verified=False` refuses
the dispatch; under `BUILD` it is admitted. A default of `BUILD` would mean every caller that
forgot the argument admitted a vacuous control into the merge rate, and the whole point of the
flag is that the permissive case is the one somebody has to ask for.

**4. The outcome mapping between the two vocabularies is written out, not derived.**

The two enums have identical members and values today. A mapping that relied on that would
misroute silently the first time either grew a member — which is how `not_executed` ends up
collapsed into a neighbour, the single defect this whole layer exists to prevent.

### What this changes about the Sandbox Specification

`sandbox-specification.md:125` and its `evidence:` header both argue C1–C3 are written to pass
harmlessly. **That paragraph is superseded by this record.** The assertions are written; they
do not pass; they name what has to be read. The specification's table is unchanged — every
claim in it still stands — and only the argument for writing them as harmless passes is
withdrawn.

### Consequences and enforcement

- Five shells are registered: C1, C2, C3, C5, C10. `open_holes()` is O5's worklist and its
  count reaching zero is what discharges O5.
- CI asserts the worklist is **non-empty** while the executor is unread. Deleting a hole is
  the cheapest way to make O5 look finished, and it is the one thing this check catches.
- C8, C9, C12, C13 are implemented for real, since none rests on executor vocabulary. C14
  folds the end-of-run re-assertion; C15 checks the patch. Each carries a control that fails
  on an empty scan.
- C4 and C11 are **not** written: both compare against a run fingerprint record that does not
  exist in this repository. They are blocked on that, not on O5, and saying so is more useful
  than a shell whose hole is "the fingerprint".
- `Admissibility` is a two-member enum with no third member and no default of convenience.

### Why this is an inspector patch

All of it is `harness/`, which is inspector machinery under D20. Major-fix #8 permits an
agent-drafted inspector patch only under line-by-line human review with a mandatory ADR. This
is that ADR. The review is O9 and has not happened, so the change is landed and unreviewed,
and that is the honest state to record.

### What found it

Implementing the shells. `premise_verified` was already written, already tested, and already
unable to affect anything — the flag existed, the converter did not, and nothing had ever
carried a probe result to a handle because no adaptor exists yet. A field that is correct and
unreachable reads exactly like a field that works.

---

## ADR-0018 — The executor moved, and eleven of thirteen premises were wrong

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** D38's selection target; the Sandbox Specification's C1, C2, C3, C5 and C10 rows · **Discharges:** O5 · **See also:** ADR-0007 (the vacuity this prevented), ADR-0017 (the shells that held the holes)

### Context

O5 was "read OpenHands at the pinned SHA". Two things were wrong with that sentence.

**There was no pinned SHA.** "Pinned by commit SHA" appears as an instruction in five places
— plan:114, plan:878, `execution-order.md:302`, the C5 row, D53 — and nowhere as a value. The
pin was an intention that had been restated often enough to read as a decision.

**And the repository named by D38 no longer contains an executor.** Read 2026-08-18:
`github.com/OpenHands/OpenHands` at `1916c9046c4e6a1e081be1ba06e278d182a40133` is **Agent
Canvas**, a TypeScript/React/Electron "developer control center". It holds eight Python
files: five CI scripts and three test mocks. The agent moved to
`github.com/OpenHands/software-agent-sdk`, whose `openhands-agent-server` is the REST API
Agent Canvas itself connects to.

### Decision

**1. The executor is `OpenHands/software-agent-sdk`, pinned at
`d460d1a0b6bd35e054ad146c6078205df4686387`** (default-branch HEAD at read time, 2026-08-18).
`OpenHands/OpenHands` at `1916c904…` is recorded as **checked and not adopted**, so a future
reader meeting that URL in D38 can see it was rejected rather than overlooked.

Both pins are constants in `harness/containment/shells.py` and C5 asserts against them.

**2. D38's selection rationale must be re-verified, not inherited.** It selected OpenHands
for "a real Docker sandbox (ActionExecutor inside the container, action/observation event
stream over REST)" and "documented durable per-event persistence". Those properties were
asserted of a repository that no longer holds the code. The persistence property **is**
confirmed against the SDK below; the sandbox property is not re-checked here and is recorded
as outstanding.

**3. Two corrections to recorded facts about the repository itself.** The canonical-path
redirect is real and worse than one hop: `OpenDevin/OpenDevin` and `All-Hands-AI/OpenHands`
both 301 to `OpenHands/OpenHands`, which is not the executor — so following the redirect
faithfully still lands somewhere wrong. And the C5 row's "a repository with no tags to pin
to" is false: `v1.14.0` was the most recent tag at read time. HEAD was pinned deliberately,
so that the vocabulary read is the vocabulary pinned; not because nothing else existed.

### What the read found — eleven corrections in thirteen answers

| # | Premise as recorded | What the source says |
|---|---|---|
| C1 | Persistence is **opt-in**; assert enabled at startup | `persistence_dir: str \| None` **defaults to `"workspace/conversations"`** — on unless explicitly `None`. The assertion is *not disabled*, not *enabled*, and the two differ on every default configuration. A path, not a flag. |
| C2 | `CondensationSummaryEvent` is the compaction event | **Three** classes: `Condensation`, `CondensationRequest`, `CondensationSummaryEvent`. The note named the third. |
| C2 | Assert the condenser disabled | `Agent.condenser: CondenserBase \| None = None`. **Two** ways to be off — `None`, or the explicit `NoOpCondenser` — and `PipelineCondenser` composes others, so a non-null value is never safe from the field name. |
| C3 | A confirmation/approval **mode** key | `confirmation_policy: ConfirmationPolicyBase = NeverConfirm()`, a polymorphic object with arms `AlwaysConfirm` / `NeverConfirm` / `ConfirmRisky`. Not a boolean. |
| C3 | Assert **zero approval-class events** in the stream | **No such event exists.** Rejection emits `UserRejectObservation` (`rejection_source` `"user"` or `"hook"`); acceptance is *implicit* — `run()`'s second call executes the pending actions and emits nothing. |
| C3 | The executor's own **frontend** is the surface to close | `enable_vscode: bool = True`. **A full VS Code server runs inside the agent container by default**, on port 8001. `enable_vnc` exists too, defaulting False. |
| C5 | The repository has no tags | It has tags; `v1.14.0` was latest at read time. |
| C5 | The canonical path is a redirect — pin by SHA | True, and insufficient: the redirect target is the frontend, not the executor. |
| C10 | Configuration hoists through **files** at search paths | `load_config` reads one file — `OPENHANDS_AGENT_SERVER_CONFIG_PATH`, else `workspace/openhands_agent_server_config.json` — and then **merges `OH_*` environment variables over it**. |

Two answers needed no correction: the `persistence_dir` and `confirmation_policy` key names
themselves, which is to say the research notes got the two easiest facts right and were
wrong or incomplete about everything that mattered.

### The one that could not be implemented as specified

C3's third conjunct — "zero approval-class events appear in the stream" — **is not
implementable, and would have passed over the exact hazard it names.** Approval leaves no
trace in the event stream, so a human could confirm every action in a run and the stream
would carry zero approval-class events. This is worse than ADR-0007's misnamed key: no name
would have made it work.

It is replaced by three observables, which together are stronger than what was asked:

- `confirmation_policy` is `NeverConfirm` on the loaded configuration;
- the conversation never entered `WAITING_FOR_CONFIRMATION`, which is **persisted** in
  conversation state and is the only durable trace that a human was asked;
- no `UserRejectObservation` carries `rejection_source="user"` — a human *rejecting* proves a
  human was being asked, whatever the configuration claims. `"hook"` is Alfred's own
  PreToolUse block and is deliberately not a finding.

A fourth clause is added that the specification never contemplated: `enable_vscode` and
`enable_vnc` false, and nothing listening on the surface ports. C3 was written against a chat
frontend with an approval button. A VS Code server is an arbitrary file-edit and
code-execution surface for a human, it is **on by default**, and anything done through it
lands in no event stream at any layer — not Alfred's, and not the executor's either.

### Consequences and enforcement

- All thirteen holes are answered and each cites a `path:line` in the pinned tree. **A hole
  cannot be filled without a source**: after O5 the failure mode is no longer an unread hole
  but an answered one nobody can re-verify. `unsourced_holes()` is CI-asserted empty.
- `open_holes()` is empty and CI asserts it. Any hole reset to `UNREAD` by a future executor
  change reopens O5 and returns that assertion to `not_executed`; the suite tests the refusal
  by blinding one hole per shell rather than by trusting that it still works.
- Corrections travel *with* the values, in `Hole.correction`. A research note that quietly
  becomes a constant is how a premise stops being rechecked.
- **Outstanding, and not closed by this ADR:** D38's sandbox rationale against the SDK; C4 and
  C11, still blocked on a run fingerprint record that does not exist; and whether Agent Canvas
  being the project's headline product changes the executor's trajectory for Alfred's purposes.

### Why this vindicates writing the shells first

Eleven corrections in thirteen answers. Every one would have been a green assertion: a
`persistence_dir` check asserting `True` against a path, two unnamed condensation event
classes, a boolean test against a policy object, an event count that can never be non-zero, a
VS Code server nobody looked for, and a configuration channel nobody enumerated. That is what
`sandbox-specification.md:125`'s "an assertion that harmlessly passes on a feature that does
not exist costs nothing" would have bought.

### Why this is an inspector patch

`harness/containment/` is inspector machinery under D20. This is the mandatory ADR under
major-fix #8; the line-by-line review is O9 and has not happened.

---

## ADR-0019 — D38's sandbox rationale, verified: true of one configuration, false of the default

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** D38's sandbox rationale; ADR-0018's outstanding list · **See also:** ADR-0018 (which recorded this as unverified), ADR-0017 (the shells), ADR-0007 (the vacuity being avoided)

### Context

D38 selected OpenHands for two properties. ADR-0018 confirmed the second — durable
per-event persistence — against `OpenHands/software-agent-sdk` at
`d460d1a0b6bd35e054ad146c6078205df4686387`, and recorded the first as **not re-checked**:

> a real Docker sandbox (ActionExecutor inside the container, action/observation event
> stream over REST)

That sentence was written about a repository that no longer holds the code. This ADR checks
it against the pinned tree. Every citation below is a `path:line` in that tree.

### Decision

**The rationale is upheld in substance, wrong in every proper noun, and — decisively — it
describes one configuration of the SDK rather than the SDK.** D38 stays as the selection;
what changes is that the sandbox is now a thing Alfred must *configure and assert*, not a
property it inherits by choosing this dependency.

### Clause by clause

| D38's words | Verdict | What the pinned tree says |
|---|---|---|
| "a real Docker sandbox" | **True, and opt-in** | `DockerWorkspace(RemoteWorkspace)` runs `docker run -d` on `ghcr.io/openhands/agent-server:latest-python` and health-checks it (`openhands-workspace/openhands/workspace/docker/workspace.py:53,171`). It is one of five workspace kinds; `docker`, `apptainer`, `remote_api` and `cloud` all exist. |
| "ActionExecutor" | **False as a name** | Zero occurrences repository-wide. The executor is the `agent-server` FastAPI app; the loop is `EventService` / `LocalConversation`. |
| "inside the container" | **True** | The server constructs its own `LocalWorkspace` for tool execution (`openhands-agent-server/openhands/agent_server/conversation_service.py:244`, `event_service.py:972`), so under `DockerWorkspace` the tools run in the container and the client holds only an HTTP handle. |
| "action/observation event stream" | **True** | `ActionEvent` (`openhands-sdk/openhands/sdk/event/llm_convertible/action.py:24`) and `ObservationEvent` (`observation.py:32`). |
| "over REST" | **True, and incomplete** | REST at `/conversations/{id}/events` (`event_router.py:30,195,206`), but the live stream the client actually consumes is a **WebSocket**, `/sockets/events/{conversation_id}` (`openhands-sdk/openhands/sdk/conversation/impl/remote_conversation.py:217`). A containment control written against REST alone would watch the wrong socket. |

### The finding that matters more than any of those

**The sandbox is not the default, and the type system does not say so.**
`Workspace(working_dir=...)` with no `host` returns a `LocalWorkspace`
(`openhands-sdk/openhands/sdk/workspace/workspace.py:36-49`), which "operates on the host
filesystem" and is "suitable for development and testing" (`local.py:17-29`). Meanwhile
`BaseWorkspace`'s own docstring says workspaces "provide a **sandboxed** environment"
(`base.py:27-33`) — a claim that is false of the class the factory returns by default.

The consequence for Alfred is precise: **no C-assertion in the specification currently
checks which workspace kind is in use.** Every containment control is written as though the
container is a given. An adaptor constructed against the default would run the agent on the
host, and C1, C2, C3 and C10 would all still pass, because each reads configuration and
event streams that exist identically in the local case. That is ADR-0007's third outcome
again — executed, passed, vacuous — at a layer above the one the shells were built to guard.

### Four properties the rationale asserted by implication and the tree does not provide

None of these is a defect in the SDK; each is a default that "a real Docker sandbox" was
read as excluding, and does not.

1. **The agent server is unauthenticated by default.** `session_api_keys` defaults empty and
   "empty list implies the server will be unsecured" (`config.py:223-232`, `33-44`);
   `DockerWorkspace` then sets `api_key = None` outright (`docker/workspace.py:278`). The
   server is told to bind `0.0.0.0` (`workspace.py:255-257`) and published with
   `-p {host_port}:8000` (`:222`), which Docker binds on **all host interfaces**. An
   unauthenticated remote-code-execution endpoint is reachable off-box unless the operator
   sets `SESSION_API_KEY` or firewalls the port.
2. **The container is unhardened.** The `docker run` argument list (`:238-260`) carries no
   `--cap-drop`, no `--read-only`, no `--security-opt`, no user namespace and no
   `--network none`; egress is the default bridge, i.e. open. Inside, the agent user has
   `NOPASSWD:ALL` sudo (`openhands-agent-server/openhands/agent_server/docker/Dockerfile:149`),
   so any assertion about in-container privilege is defeated by one command.
3. **Two egress channels exist that the specification never enumerated:** `webhooks`
   (`config.py:300`) POSTs events out of the container, and `telemetry` (`:396`) ships to
   PostHog or an arbitrary HTTP endpoint. C6's deny-by-default network policy is what stops
   them; nothing in the executor's own configuration does.
4. **The evidence is deleted by default at the end of the run.** `Conversation(...)` defaults
   `delete_on_close=True` (`openhands-sdk/openhands/sdk/conversation/conversation.py:84,113,142`);
   on close the client issues `DELETE /conversations/{id}`
   (`impl/remote_conversation.py:1729-1739`), and the server `safe_rmtree`s the conversation
   directory (`conversation_service.py:1725-1731`). The workspace survives; the event log does
   not.

Point 4 falsifies **C1 as written**. C1 claims "every event the adaptor observed is present
on disk at end of run", and its check reads the persisted directory — a directory the default
configuration removes before that read. C1 needs `delete_on_close` as a hole and a fourth
clause; that amendment is **required and is not made here**, because `harness/containment/`
is inspector machinery whose current patch is still unreviewed on O9.

### One confusable pair, recorded so it is not collapsed

`persistence_dir` exists at two layers with **opposite** requirements. Client-side, passing it
with a `RemoteWorkspace` raises `ValueError`
(`openhands-sdk/openhands/sdk/conversation/conversation.py:155-160`). Server-side it is
`StartConversationRequest.persistence_dir`, defaulting to `"workspace/conversations"`
(`openhands-agent-server/openhands/agent_server/models.py:134`). C1 cites the server-side
field and is therefore at the correct layer. A future reader unifying the two names would
break C1 in the direction that still reads green.

### Consequences

- D38's sandbox rationale is **verified, with the qualification that it describes
  `DockerWorkspace` and not the SDK's default**. ADR-0018's outstanding item is discharged.
- **Opened, and not closed here:** a C-assertion that the workspace kind in use is the
  container one — the missing control that makes the other four vacuous when it is absent;
  C1's `delete_on_close` clause; and whether points 1 and 2 are Alfred's to assert
  (`--cap-drop`, `--network`, sudo) or S6's host-level `nftables` work already covering them.
- **Still outstanding from ADR-0018:** C4 and C11, blocked on a run fingerprint record that
  does not exist; and whether Agent Canvas being the headline product changes the executor's
  trajectory.

---

## ADR-0020 — The run fingerprint record, and the two assertions that were waiting on it

**Date:** 2026-08-19 · **Status:** Accepted · **Supersedes:** none · **Amends:** the Sandbox Specification's C4 and C11 rows; the `Worker` port's fingerprint obligations · **See also:** ADR-0018 and ADR-0019 (which both recorded C4 and C11 as blocked on this), ADR-0017 (shells and why a green assertion can be worse than an absent one), ADR-0007 (the vacuity class), D19 and D40 (the field set)

### Context

C4 and C11 have never been written. Both compare a live reading against a declared value —
the runtime image digest, and the serving lane's configuration — and there was no declared
value anywhere in the repository to compare against. `runtime_image_digest` appeared in no
Python file at all: not in a column, not in a constant, not in a type. `control.fingerprint`
stored D19's and D40's components in the clear but had no column for the image digest, the
model id, the quantization, the denylist version, or the executor's identity.

ADR-0018 recorded the block and declined to write shells for the two rows, on the grounds
that a shell whose only hole is "the fingerprint" belongs on no worklist. ADR-0019 restated
it as still outstanding. Neither closed it, and the handoff that followed listed it as the
one piece of unblocked agent work that unblocks something else.

### Decision

**One typed, frozen record — `harness/fingerprint/record.py` — carrying the full field set,
whose digest is computed from the fields rather than supplied beside them.**

Four properties, each answering a way a fingerprint stops being one:

1. **The hash is a function of the fields, not a claim about them.** `fingerprint_sha256` is
   a property computed through ACS-1 (`harness/acs/acs1.py`) with record type
   `run_fingerprint`. ACS-1 is already the one encoder — the result stamp and the evidence
   chain use it, it has a published vector suite and a JavaScript cross-check — so a second
   canonicalization would be a second thing to keep in agreement. A test perturbs **every
   field in turn** and requires the digest to move; a digest over a subset passes every
   other test in the file while leaving the omitted fields free to change under a
   measurement.
2. **A missing field is a construction error.** No defaults, no `None` for "not known yet".
   A record that cannot state a field cannot assert on it, and a defaulted field is one that
   silently stops discriminating. This generalizes `lane_fingerprint.FingerprintIncomplete`,
   which has enforced the same rule for the lane since it was written.
3. **Comparison runs in both directions.** A declared field the observation omits, and an
   observed field the record never declared, are both differences — the second because an
   executor reporting a field nobody declared is an executor whose configuration surface grew
   under the measurement, which the `Worker` port contract already requires raising on.
4. **The record reads nothing.** It holds the declared value and compares. Reading the live
   world is C4's and C11's job, which is what lets every branch of the comparison be tested
   without a container or a serving layer.

**`spec.fingerprint` becomes `RunFingerprint`** and the separate `fingerprint_sha256` field
is removed: two fields that can disagree eventually will. **`observed_fingerprint` on the
claim stays a `Mapping`**, deliberately — a dataclass cannot represent a field the record
never declared, so typing it would delete property 3 by making its subject unrepresentable.
It moves from `Mapping[str, str]` to `Mapping[str, object]`, because a context length is an
integer and stringifying it at the boundary is where a comparison starts passing on the
wrong thing.

### The two limits, written down rather than papered over

**C11 asserts three of its four conjuncts from the serving layer.** The parallel slot count
is a launch-time property of the server and is not in `/api/v0/models`. It therefore arrives
as an explicit argument, and its absence is `not_executed` rather than a quiet pass on the
other three. Naming a plausible key for it would have produced a green assertion over a field
nobody read — the misnamed-key vacuity ADR-0007 names, and the case ADR-0017 withdrew the
"an assertion that harmlessly passes costs nothing" defence for. The slot count is not
optional information: prefix reuse is 140x at one slot and 1.0x above it, so a lane at four
slots is a different lane wearing the same model id.

**C4 treats an unread pull location the same way.** `pulled_in_sandbox_netns` is
`bool | None`, and `None` is `not_executed`. A `bool` with a `False` default would have
turned every inspection that forgot to answer into a pass.

### Vacuity controls

- **C4** — the image count. An inspection that enumerated zero images is `not_executed`,
  because an empty local store and a store that agreed are otherwise indistinguishable, and
  "the image was not found, so nothing contradicted the digest" is the shape of a control
  that stopped running. D57.
- **C11** — inherited from `lane_fingerprint`, where an unreadable fingerprint has always
  been treated exactly as a mismatched one. Both of its raising paths land on
  `not_executed`, which F25 makes a failure.
- **The record** — every field is perturbed and the digest must move; the field groups are
  asserted to account for every field, so the grouping cannot drift into decoration.
- **The register** — a test reads the control migrations' column names from source and
  requires every record field to have one. Read from the AST rather than from a live schema
  on purpose: a drift guard that only runs where Postgres does is a drift guard that stops
  running.

### Migration

`migrations/harness/control/versions/0002_fingerprint_run_fields.py` adds the eight columns
the register had no home for: `model_id`, `quantization`, `executor_name`,
`executor_commit_sha`, `adaptor_version`, `runtime_image_digest`, `oracle_denylist_version`,
`seed_layer_order_sha256`. All `NOT NULL` with no server default — the table starts empty in
every environment, and a nullable fingerprint field is a field an assertion cannot be written
against, which is the state this migration exists to end. `control` is configuration rather
than evidence and sits outside `lint_migrations.py`'s additive-only guard by design; the
`downgrade` still raises, because dropping a column rewrites what past rows claim.

### Consequences and enforcement

- C4 and C11 are written: `harness/containment/image.py` and `harness/containment/lane.py`.
  The Sandbox Specification's rows and the containment package docstring are amended to match.
- C11 wraps `harness/lane/lane_fingerprint.assert_fingerprint` rather than reimplementing it.
  That module was written against an observed defect — a model loaded at 262,144 found serving
  at 28,672 after an idle gap, turning 10/10 tool calling into 0/10 with nothing erroring — and
  a second implementation of the same control is a second place for that defect to be missed.
- `FieldDiff` has exactly one definition, in the record module; the lane module imports it.
- **One conjunct of C11 remains unread**, and the assertion says so on every run rather than
  reporting three-of-four as green.
- **Not addressed here:** `ExecutorObservation.config` is still `Mapping[str, object]`,
  adaptor-supplied and unvalidated. Typing the fingerprint does not type the adaptor contract,
  and the two are separate reviews.
- **Stale and operator-owned:** `docs/tier2/execution-order.md` is `owner: human`. Its O9 row
  names two items and the queue is now eleven; its boot-assertion count says fifteen in three
  places, the table held sixteen before this change and holds eighteen after. Neither is
  corrected here.

### Why this is an inspector patch

`harness/` is inspector machinery under D20, and so is the migration tree. Major-fix #8
permits an agent-drafted inspector patch only under line-by-line human review with a mandatory
ADR. This is that ADR. The review is O9, it has not happened, and this change joins the queue
rather than clearing it — landed and unreviewed, which is the honest state to record.

---

## ADR-0021 — Enumeration drift, and the two claims of CI coverage that were false

**Date** 2026-08-19 · **Status** Accepted · **Supersedes** nothing

### Context

`.github/workflows/gates.yml` states a rule at the top of the file: *"If a check a document
names is not in this file, that document's enforcement value is a wish and the document is
falsified by its own frontmatter."* The rule is right and it was not applied to the file
itself. Two things covered by enumeration had drifted, and both drifted in the direction that
reads green.

**`harness/stamp` and `harness/fingerprint` ran in no CI job.** Every other test directory
under `harness/` is named in an explicit `pytest` step. These two were not — `harness/stamp`
since `c1ca0b4`, `harness/fingerprint` since `cff67cc`. Nothing reported it, because the
verification command everybody actually runs is `uv run pytest tests bench harness`, which
walks the tree. The local run and CI disagreed about what was being checked, and only the
local one was ever looked at. `harness/stamp` holds `verdict_map.py`, which sits under the
evidence chain and is itself an unreviewed O9 item.

**`failure-semantics.md` claimed a check that did not exist.** Its Enforcement section said
CI asserted a one-to-one mapping between the row ids `F1`…`F28` and injection ids, and that a
row with no injection failed the build. Nothing enumerated F ids at all. Four rows were named
somewhere in a test file; twenty-four were named nowhere; and every row added — `F28` most
recently — made an already-false claim falser. The document is `owner: executable` and
`enforcement: ci-gate`, so softening the sentence alone would have left the frontmatter
falsified in the same way `stage-gate-definitions.md` still is.

**And `gen_doc_stubs.py`'s register stood at 55 entries against 63 documents**, with nothing
comparing them.

Three instances, one mechanism: an enumeration missing an entry is indistinguishable from a
complete one. This is the third time this project has paid for it — the first was a document
added without an index entry on 2026-08-13, which is the only evidence anywhere that the
register's completeness check works.

### Decision

**Build the check, not just the fix.** `scripts/lint_ci_coverage.py` carries two checks, each
with a vacuity guard and a committed `--self-test`:

- **T** — every directory holding `test_*.py` under `harness/` and `tests/` is named in a
  `pytest` step of `gates.yml`. A step naming a parent covers its children, so `pytest harness`
  is not reported as thirteen violations. A scan finding zero directories fails.
- **F** — every row id in the fail-closed table has exactly one entry in
  `harness/selftest/failure_register.json`, every entry names a live row, and every entry
  claiming coverage names a file that exists **and mentions the id**. That last clause is what
  stops the register becoming a second unverified claim in place of the first.

`gates.yml` gains the two missing `pytest` steps and runs the new lint in the integrity job,
before any suite reports a number.

`scripts/lint_docs.py --check` gains the register comparison, reading `gen_doc_stubs.py` by
**AST rather than by import**: the lint that guards the register must not execute the
generator to learn what is in it, which is the same reason its frontmatter parser is
hand-written instead of a YAML dependency.

### Why the F check does not require an injection per row

Requiring one today would report twenty-four failures and hold CI red, and a lint that cannot
be landed green enforces nothing. So `not-yet-injected` is a legal status: recorded and
counted, never hidden. What the lint forbids is **drift** — a row with no entry, an entry for
no row, evidence that is absent or that never mentions the row it claims to cover. The two
covered statuses are kept apart: `injected` means a fault is injected, `referenced` means a
test names the row and asserts part of its disposition without injecting anything. Collapsing
them would let the covered count rise without a single fault being injected. **All four
covered rows today are `referenced`, not `injected`.**

### The hole this leaves, stated rather than closed

A register declaring every row `not-yet-injected` would pass. What stops that being silent is
that the covered count is written in the document, asserted against the register on every run,
and printed by the lint — so it falling is a change a reader sees rather than an absence
nobody notices. The stronger check is the one to write when injections exist to check.

### `NOT_GENERATED`, and why the eight missing documents were not simply added

Five of the eight are Tier 0. `gen_doc_stubs.py` is a stub *generator*, and adding the
constitution to its register would record that those documents have a machine-authored origin.
`main()` never overwrites an existing file, so it would have been harmless in effect and wrong
in meaning — Tier 0 authorship is permanently outside the agent boundary. They are declared in
an explicit `NOT_GENERATED` set with the reason, and the lint asserts that the register and
that set together account for every document on disk, in both directions.

### Consequences and enforcement

- The false sentence in `failure-semantics.md` is replaced by what the check actually does,
  with an amendment block recording that the stronger claim was false the whole time it stood.
- The covered count lives in a machine-readable marker rather than in prose. Parsing the
  sentence would tie the lint to wording, which is what the document itself warns against when
  it explains why the row ids are stable.
- **Not addressed here:** `stage-gate-definitions.md` remains `enforcement: ci-gate` while
  naming no check in `gates.yml`, and is falsified by its own frontmatter. That is the subject
  of the next change, not this one.

### Why this is an inspector patch

`scripts/` and `.github/workflows/` are inspector machinery under D20 — `gates.yml` says so
in its own header. Major-fix #8 permits an agent-drafted inspector patch only under
line-by-line human review with a mandatory ADR. This is that ADR. The review is O9, it has not
happened, and this change joins the queue rather than clearing it.

---

## ADR-0022 — Phase 0's exit, narrowed along the ownership seam, with the residue dated

**Date** 2026-08-19 · **Status** Accepted · **Supersedes** nothing · **D28 waiver:** yes

### Context

Phase 0 exit is **2026-09-09**, twenty-one days from this record. The calendar finding in
`execution-order.md` has been on the board since the inventory and says the honest options are
to move the date under a waiver ADR or to narrow the exit the way D36 narrows a task class.
Neither had been taken.

Counted against the criteria rather than against the stages, four of the seven are met: the
null-agent floor test, the seeded-defect suite reddening correctly, deploy and rollback
verified, and the egress canary — as a probe. Three are not: byte-identical deterministic
replay, CriMe's asserted values reproduced on the six named scenarios, and an off-machine
backup with a verified restore.

**Two of the three unmet criteria are S5, and S5's exit is domain content.** The ownership rule
is the operator's, stated verbatim: the factory is Alfred, and AV-project work belongs to the
local models. Reproducing CriMe's numbers is that work. Phase 0 as written therefore gates the
factory on work the factory does not own and cannot honestly schedule — which is a defect in
the criterion, not a shortfall in the effort, and it is the reason narrowing is available here
without lowering a bar.

The remaining two have a different shape. `nftables` default-drop and a recorded D-production
restore are the operator's to execute and are not code in this repository. They are also the
only two criteria that test whether the containment and durability claims are true of anything
outside CI. Narrowing those out would remove the half of Phase 0 most worth keeping.

### Decision

Both halves of the option, not one. **Narrow along the ownership seam, and date the residue.**

**The narrowed Phase 0 exit:**

1. The null-agent floor test (met).
2. The seeded-defect suite reddening correctly (met).
3. Deploy and rollback verified against what is serving (met).
4. The egress canary firing against real enforcement — `nftables` default-drop in the host
   network namespace, not the probe alone.
5. Byte-identical deterministic replay, demonstrated end-to-end on a synthetic trajectory the
   factory owns.
6. A recorded **D-production** restore: the actual off-machine backup restored and compared
   against the live anchor. A green CI run is D-synthetic and proves the mechanism only.
7. **No unreviewed inspector patch enforces any of the above.**

**The residue, dated 2026-10-07:** CriMe's asserted values reproduced on the six named
scenarios, and everything downstream of D49's P3 rung — which is O3, already carrying
2026-09-09 and moved here with it.

### Why 2026-10-07, and why not a fresh date

The residue is domain work by the local models, which is exactly what Phase 1 dispatches and
what K3 measures. Pinning it to an existing milestone rather than inventing one makes it
self-measuring: if the six scenarios are not reproduced by Phase 1 exit, K3's per-task merge
rate on that task class is the evidence for why, and no separate post-mortem is needed. A
fresh date would have to come from an estimate of the domain work, and the last such estimate
is the sixty-six-hour figure that produced this problem.

### Criterion 7, and why the review is a criterion rather than a note

Every criterion above is enforced by inspector machinery, and eleven inspector patches stand
unreviewed on O9 before this plan adds to them. A gate nobody has reviewed is not a gate — it
is ADR-0007's vacuity class one level up, where the thing executed and passed and the reader
concluded more than the check performed. Making the review a criterion makes the debt dated
and countable instead of "Rolling". Review is batched by subsystem — the containment patch as
one change, the lint family as one, the stamp and fingerprint pair as one — because sixteen
separate reviews is the shape most likely to be skimmed.

### The O1 derivation, recorded here because it closes half of an operator item

`O1` asks for `F` and a target `n`, with `n` **stated as dispatched or merged**. The
dispatched-or-merged half does not need an operator preference; it follows from the formula.
The capacity ledger is `5·n·m + F ≤ C` with `m` defined as per-task human minutes **across
authorship, review and escalation**. All three are paid on every task the operator dispatches,
whether or not it merges. A merged `n` would therefore silently drop the minutes spent on
rejected tasks, so **the capacity gate's `n` is dispatched**. The risk register's own
arithmetic already reads it that way — "2–3 dispatched tasks/day is 80–120 dispatched and
roughly 40–60 merged".

K3's denominator stays **merged**, and the two are different quantities that happen to share a
letter. That is where the factor of two the board flags actually lands.

`F` remains open and is the one term nobody can derive. Either it is supplied, or 300 min/week
stands as a declared assumption whose falsification condition is a measured `F` above it,
invalidating every `m` budget in `mission-control-design.md`.

### Consequences and enforcement

- This is a **D28 waiver** and counts toward the waiver total the operating principles use as
  a health metric. It is the first.
- The narrowed criteria become the content of `docs/tier2/stage-gate-definitions.md`, which is
  `owner: executable` and `enforcement: ci-gate` and has named no check since it was written —
  falsified by its own frontmatter until the next change lands the check.
- **Criterion 6 cannot be evaluated yet.** No Tier 0 recovery objective exists (D43), so a
  restore drill produces a duration and nothing to compare it to. The gate reports that as a
  failure rather than skipping it, per F25. Tier 0 authorship is permanently outside the agent
  boundary, so this is owed by the operator and by nobody else.
- **Operator-owned and not done here:** the `ttc_1`/`ttc_4` labelling defect in the plan's
  exit-criterion prose — `ttc_1≈2.4` is `TTCStar` and `ttc_4≈1.25` is `TTR` on
  `ZAM_Urban-7_1_S-2`, with `bench/tasks/phase1_tasks.json` already correct. It sits in the
  residue's half of the criteria, so this narrowing does not transcribe it, but it must be
  fixed before the residue is judged or the reproduction target is a different measure.
- `docs/tier2/execution-order.md` is `owner: human` and is not edited. It does not yet carry
  this narrowing, its O9 row names two items against a queue of twelve, and its
  boot-assertion count is stale in three places.

### What this decision does not do

It does not lower a bar. Every criterion removed is moved, dated, and assigned to the party
that owns the work; none is weakened in place. The failure this is written against is the one
the plan names by name — arriving at 2026-09-09 and declaring exit on a subset without saying
so — and the defence against it is that the subset and its remainder are both written down
here, before the date rather than after it.

---

## ADR-0023 — Which of ADR-0019's unhardened defaults are Alfred's, and the two that are

**Date** 2026-08-19 · **Status** Accepted · **Supersedes** nothing

### Context

ADR-0019 recorded four properties of the executor that D38's sandbox rationale asserted by
implication and the tree does not provide, and closed none of them. Its Consequences section
left three items open. **Two of those three were discharged before this record and the ADR had
gone stale saying otherwise** — `69a09e9` wrote C16, the workspace-kind control ADR-0019 calls
*"the missing control that makes the other four vacuous"*, and the same commit added C1's
fourth clause for `delete_on_close`. ADRs are immutable and are corrected by successors rather
than edited, so this is where that is written down.

What genuinely remained open is the third: whether points 1 and 2 — the unauthenticated server
and the unhardened container — are Alfred's to assert or already covered by S6's host-level
`nftables` work.

### Decision

**The deciding property is direction, and it settles the question without a judgement call.**

S6's `nftables` default-drop is **egress**. The stage names it precisely: the run refuses to
start unless a known non-allowlisted connection *fails*, because environment-variable proxy
configuration is advisory and bypassable. Everything it covers is the container reaching out.

Point 1 is **ingress**. `session_api_keys` defaults empty and its own field documentation says
an empty list means the server will be unsecured; `DockerWorkspace` then sets `api_key = None`
outright; the server is told to bind `0.0.0.0` and is published with `-p {host_port}:8000`,
which Docker binds on **all host interfaces**. That is an unauthenticated remote-code-execution
endpoint reachable off-box, and no egress rule touches it, in either direction of the word. It
is Alfred's.

Point 2 is neither ingress nor egress: it is a property of the `docker run` argv — no
`--cap-drop`, no `--read-only`, no `--security-opt`, no user namespace, no `--network`. Those
are readable from **outside** the sandbox, which is exactly where Alfred's assertions already
run, so they are assertable rather than merely regrettable. Also Alfred's.

Both become **C17**, a new shell in `harness/containment/shells.py`, running outside at
dispatch.

### The one that is not Alfred's, and why the split is not arbitrary

The agent user's `NOPASSWD:ALL` sudo is baked into the image, not chosen at launch. No runtime
flag asserts it away and reading the launch argv would never see it — an assertion about it
would have to inspect the image, which is S6's layer-1 build-closure check against a real
resolved lockfile. Putting it in C17 would produce a clause that cannot fail for the right
reason, which is worse than an absent one.

The fourth property, `webhooks` and `telemetry` as unenumerated egress channels, stays with C6
as ADR-0019 already recorded. It is egress, so the direction test assigns it there too.

### C17's clauses, and why the ingress half is two of them

1. **The server requires authentication** — `session_api_keys` present, non-`None`, non-empty.
   Absent, `None`, empty and blank are four distinct findings and each is reported by name,
   because the four arrive by different routes and the fix differs.
2. **Every published port binding is loopback.** An unparseable binding is a finding rather
   than loopback: a binding whose shape nobody recognizes is not one anybody checked.
3. **`--cap-drop` present and the network off the default bridge.** `--network bridge` is
   reported specifically, because naming the flag is not the same as leaving the default
   network and an argv carrying it looks hardened at a glance.

Clauses 1 and 2 are separate because either alone is insufficient. An authenticated endpoint on
`0.0.0.0` is one credential away from the same outcome; a loopback binding with no credential
trusts every process on the host.

### Vacuity control

An unread `container_launch_args` or an unread `published_port_bindings` reports
`not_executed`, never a pass. An assertion over an argv nobody collected returns the same
answer on a hardened launch and an unhardened one, which is the shape D57 rejects and which
F25 turns into a refusal to start. Both are tested, parametrized over each field in turn.

### Consequences and enforcement

- `ExecutorObservation` gains `container_launch_args` and `published_port_bindings`. Both
  default empty, and empty is the unread case rather than the benign one, matching every other
  field on that record.
- The Sandbox Specification gains a C17 row and an amendment block recording the direction
  test and the stale Consequences section.
- **Not done here:** C17 is not in C14's re-assertion set. A container relaunched mid-run with
  different flags would not be caught, and the argv is recorded in `observed` precisely so that
  it *could* be compared — the comparison is simply not wired. That is a smaller change than it
  looks and is deliberately separate from this review.
- **Not done here:** `--read-only`, `--security-opt` and the user namespace are named in the
  ADR and not asserted. Two flags were chosen because they are the two whose absence has a
  consequence this specification already argues about; widening the list is a policy decision
  with no new evidence behind it.

### Why this is an inspector patch

`harness/` is inspector machinery under D20. Major-fix #8 permits an agent-drafted inspector
patch only under line-by-line human review with a mandatory ADR. This is that ADR. The review
is O9, it has not happened, and this change joins the queue.

---

## ADR-0024 — C15's third clause runs, the denylist's names are read, and a gate nobody had

**Date** 2026-08-19 · **Status** Accepted · **Supersedes** nothing

### Context

Three things, found together because they share a cause: something that looked checked and was
not.

**C15 clause 3 had never run.** The clause catches the vendoring case the other two miss
entirely — a copied measure implementation under a new name declares no dependency and imports
nothing denied — by comparing normalized content hashes against hashes of the oracle's source.
`denied_source_hashes` was supplied in two test cases and by nothing else. There was no
generator, no file in `policy/`, no production caller. So every real invocation of C15 reported
`PASSED — 2 of 3 clauses (no denied source hashes supplied)`, and the module's own comment
names the shape: *"a report that reads green over a check that did not run."*

**The denylist's import names were `UNVERIFIED`** (D54), taken from this project's records
rather than read from each distribution at a pinned version. A wrong import name is an
assertion that passes while naming nothing.

**And neither `ruff` nor `pyright` covers `harness/`.** Both declare `include = ["src",
"tests"]`. A function in `harness/containment/` annotated `-> str` and returning an `int`
passes both gates; this was verified by planting one. Every "ruff clean, pyright 0 errors"
recorded in this log is true and says nothing about the inspector tree.

### Decision — the hashes are produced inside the image, and only digests leave

`harness/oracle/fingerprints.py` runs inside the pinned oracle image under the posture
`run_oracle` already established — `--network none`, `--read-only`, non-root, no repository
mount — and emits normalized digests for CriMe's measure sources, the real top-level import
names of each denied distribution, and its answers to a committed vector suite. Output is
`policy/oracle-source-hashes.json`: **47 files at commit `60bebed8005610`**.

The hashing happens *inside* because D54 says the oracle's outputs cross the boundary as data
and its code never crosses at all. Hashing outside would mean extracting CriMe's source text
into this repository, which is the thing D54 forbids in as many words.

### The normalization therefore exists twice, and that is the interesting decision

`normalized_source_hash` in `patch_side.py` runs outside on the diff. `_normalized` in
`fingerprints.py` runs inside. They cannot share a module: `extract.py`'s stated property is
that nothing baked into the oracle image imports Alfred code, and that property is worth more
than the duplication costs.

Two implementations of one canonical form is exactly the hazard ACS-1 met and answered —
publish vectors, make both sides answer them. `harness/oracle/normalization_vectors.json`
carries nine, chosen for the rules where plausible implementations differ rather than for
coverage: comment stripping at end-of-line versus whole-line, both comment syntaxes, whitespace
runs across newlines, trimming, case folding, and a `#` inside a string literal — which *is*
stripped, and the vector records that rather than hiding it. `run_fingerprints` refuses the run
on any disagreement. Without that check a drift would make every digest in the register a
digest of something else, clause 3 would match nothing, and the result would be
indistinguishable from a clean patch.

**Measured 2026-08-19: nine of nine vectors agree.** One file, in the build context, so the two
sides cannot drift by somebody updating a copy.

### The default polarity is inverted, because the old one was the defect

Omitting `denied_source_hashes` now **loads the register**. Passing an explicit empty mapping
still disables clause 3 and still says so in the detail. The dangerous option has to be asked
for by name. A register that exists but cannot be read is `not_executed`, never a quiet
fallback to two clauses: an unreadable policy is not an absent one.

### Finding 8, documented rather than closed

Clause 3 hashes a path's **added lines** and compares them against digests of **complete
files**, so only a whole-new-file diff can match. A vendored fragment pasted into an existing
file adds a fragment, and a fragment's normalized hash is not the file's.

Written into the module's existing *"The limit"* section beside the reformatting and renaming
limits, into the register's own header, **and pinned as a test** carrying its own control: the
same content added as a whole file must fail, or the miss proves nothing. Asserting the limit
means a future change that closes it fails there and has to say so, instead of quietly widening
what a green C15 means.

Not closed, because closing it is a different check. Hashing post-application content would
catch the fragment and would cost the *"runs on the diff, never on a working tree"* property
this module is built around, whose failure mode is a dirty tree. Two checks, and the second one
is not written.

### The denylist, verified

All four denied distributions' import names match the records exactly:
`commonroad_crime`, `commonroad_reach`, `commonroad_dc`, `commonroad_clcs`. The `UNVERIFIED`
note is rewritten as a verification record rather than deleted, because what it said was true
when it was written.

One thing the reading found that the records did not have: **`commonroad-crime` installs a
second top-level name, `tests`.** It is deliberately not denied — nothing in the schedulable
task class is delegated to it, and denying a name that generic would collide with Alfred's own
tree and with most third-party packages, producing false positives in the one check whose
findings are meant to be acted on. Recorded so a future reader comparing this file against the
distribution's metadata does not have to re-derive why.

The denylist's `version` stays `1`: the digest input is `version`, `denied` and
`permitted_substrate`, and none of those changed. The entries were confirmed, not edited.

### Recorded and not fixed: `harness/` has no type gate and no lint gate

`uv run pyright harness` reports **300 errors** under the strict settings the product tree is
held to, and `uv run ruff check harness` reports *"No Python files found"* — the `include` list
excludes it even against an explicit path.

The exclusion is deliberate and its reason is sound: a product gate that fails for
inspector reasons is a gate no product change can fix. What is not sound is the consequence,
which is that the tree everything else is verified *by* is the one tree nothing verifies. This
compounds with ADR-0022's criterion 7 — the unreviewed inspector patches on O9 are also
untyped and unlinted, so "unreviewed" is a stronger statement than it reads.

Not fixed here. Three hundred strict-mode errors in inspector code is its own piece of work
with its own review, and folding it into this change would bury both. It is recorded so that
the next reader does not have to plant a broken function to discover it, as this one did.

### Consequences and enforcement

- `harness/containment/source_hashes.py` loads the register and fails closed four ways:
  absent, unparseable, zero hashes, or no oracle commit recorded. A register that parsed to
  nothing is a generation failure, not an empty policy.
- The oracle image gains `fingerprints.py` and the vectors by `COPY`, never a mount — the same
  discipline and the same reason as `extract.py`. It is not the entrypoint; the driver
  overrides it, so the image's default path stays the extractor.
- **Not done:** no production code calls C15 yet. The register makes clause 3 work whenever
  something does; it does not create the caller. The patch gate is where that lands.

### Why this is an inspector patch

`harness/` and `policy/` are inspector machinery under D20. Major-fix #8 permits an
agent-drafted inspector patch only under line-by-line human review with a mandatory ADR. This
is that ADR. The review is O9, it has not happened, and this change joins the queue.

---

## ADR-0025 — Byte-identical replay, with the domain left out of it

**Date** 2026-08-19 · **Status** Accepted · **Supersedes** nothing

### Context

P0-5 of the narrowed Phase 0 exit is byte-identical deterministic replay. `src/replay/`
carried the port and no implementation; nothing in the tree had ever replayed anything twice
and compared the results.

The criterion is the **harness's** determinism, not any measure's correctness. Building a
CommonRoad adapter and a TTC implementation to test it would test exactly the same property
and would also be domain content the ownership rule assigns to the local models.

### Decision

**Real harness in `src/`, synthetic plugs in `harness/`.** `src/replay/harness.py` holds
`DeterministicReplay`: load through a `TrajectorySource`, evaluate through a `Metric`, stamp,
and return the stamped record's own content hash. It names no dataset and no measure. The
`SyntheticSource` and `SyntheticMetric` that exercise it live in `harness/selftest/`, beside
the synthetic criterion S4 built for the stated reason that *"a factory gate does not depend
on a domain that may be written off."*

When the local models land a CommonRoad source it plugs into a harness that already carries a
byte-identical proof.

### The input hash is taken over what was loaded, not over what was asked for

`input_hash` covers the tracks the source actually returned — every sample of `t`, `x`, `y`,
plus the geometry — and not merely the `ScenarioRef`. A hash over the request would be stable
across a source that silently returned different data, which is precisely the failure a
determinism check exists to catch. Arrays go in whole rather than by length or summary: a
digest over shapes is identical for two scenarios with the same sample count.

Tracks are hashed in the dataset's own identifier order rather than in load order. A source
free to return them in any order would otherwise produce a different digest per run and fail
the criterion for a reason that is not about determinism. That is asserted by a test with a
deliberately order-reversing source.

**Tenancy and track ids are deliberately excluded** from the preimage. `org_id`, `project_id`
and `track_id` are not properties of the measurement, and including them would make the same
scenario measured by two tenants two different numbers.

### Non-derivable stamp fields are supplied, not discovered

`code_commit`, `upstream`, `tolerance`, `assumption_set` and `metric_version` arrive through
`StampContext`. The harness could shell out to `git` or read an environment variable; D40's
argument against that is the one S8 made about release identity — a fact read from outside the
artifact describes the reader's situation and not the artifact's. The caller knows these and
the harness does not, so guessing would produce a stamp that is confidently wrong rather than
one that is absent.

### Two refusals, and both produce no number at all

- **A source returning zero tracks raises.** A metric over nothing still returns something,
  and that something would be stamped and stored as a measurement of a scenario nobody loaded.
  D57 at the product boundary.
- **A metric whose declared `arity` disagrees with its result raises.** A declaration nobody
  checks is a comment.

Both are `ReplayContractViolation`, never a partial `ReplayResult`. A result meaning "some of
it worked" is a result nothing downstream could refuse.

Degeneracies remain values: a single-track scenario is E24, stamped as `Undefined`, not raised.
ADR-0001's split, asserted rather than assumed.

### How this would be shown vacuous

Every determinism test here would pass against a harness returning a constant digest. The
control is `test_a_changed_input_moves_the_digest`, parametrized over the loaded data, the
sample count, the metric version, the tolerance and the harness version, so a hash taken over
a subset of the inputs fails at least one case. A determinism test that never watches the
digest change is one a constant satisfies.

### Consequences and enforcement

- **P0-5 moves to `met`** in the stage-gate register. The Phase 0 gate now reports 4 of 7.
- The metric fixture is not a measure and says so in its own citation: `separation` has no
  safety semantics, no paper behind it and no threshold. It reads all of its input on purpose
  — a constant-returning metric would replay identically no matter what the source did.
- **Not done:** no `ReplayHarness` runs against real data, because no real source exists.
  That is R0-1, dated 2026-10-07, and it is the local models' work.

### Why this is partly an inspector patch

`src/replay/harness.py` is product tree and ordinary agent territory. `harness/selftest/` is
inspector machinery under D20, so Major-fix #8 applies to the fixtures and this ADR authorizes
them. The review is O9 and has not happened.

---

## ADR-0026 — The adaptor configuration contract, typed at the boundary

**Date** 2026-08-19 · **Status** Accepted · **Supersedes** nothing

### Context

`ExecutorObservation.config` was `Mapping[str, object]`: adaptor-supplied, unvalidated, with
no agreed serialization. **Six of the seven findings in the containment self-review were that
one root cause.** `1a631f0` made the *reading* consistent — `_read`, `_as_flag`,
`_flag_problem`, and the one-sentence discipline that absent is unknown, uninterpretable is a
finding, and neither is a pass. It did not make the contract typed.

Every existing test passed before those fixes. The suite was thorough about the paths the
checks were written for and silent about the shapes an adaptor might send.

### Decision

`ConfigValue` is a closed, recursive union — `str | int | float | bool | None`, sequences of
them, and mappings of string to them — and `validated_config` refuses anything outside it.
`ExecutorObservation.__post_init__` calls it, so the refusal happens **at construction**
rather than inside a check.

That placement is the decision. A check reading an arbitrary Python object renders it with
`str()` and compares a repr: a comparison that can only fail, and that fails for a reason no
report can explain. An adaptor sending something unserializable should be told so where it
sent it.

`None` is in the union deliberately. The SDK uses it meaningfully — `persistence_dir: None` is
how persistence is switched off — and C1 already distinguishes it from absent.

### Why a union and not a model

The keys are not knowable in advance. Every one of them is a hole, answered by reading the
executor, and a different executor answers differently. A model enumerating today's keys would
have to be edited by anyone adding a hole, and the check would then be typed against the
harness's expectations rather than against what an adaptor may legally send — which would
convert an honest "uninterpretable value" finding into a validation error at the wrong layer.

Typing the **values** removes `object` without pretending the key set is closed.

### What this does not do, asserted rather than promised

It does not make a wrong value right. A string where a boolean belongs is legal JSON, still
reaches `_as_flag`, and is still reported as uninterpretable — there is a test that asserts
exactly that, so a green C-assertion is not over-quoted as meaning the configuration was
semantically checked. This closes the **serialization** half of the finding. The semantic half
is what the holes and their citations are for.

### Two details that are defects in waiting

- **Booleans are checked before integers.** `bool` subclasses `int`, so an `isinstance(value,
  int)` test accepts `True`, and that is how a flag becomes the number 1 somewhere downstream.
  Asserted by a test rather than left to ordering.
- **NaN and the infinities are refused.** They have no JSON spelling, so admitting them would
  put a value in the configuration that cannot survive being written down while every check
  downstream reads it anyway. The same argument ADR-0001 makes about metric values, one layer
  out.

Violations name the path — `outer.inner[1]` — because a nested violation reported as "the
configuration is invalid" is a bug report nobody can act on.

### Consequences and enforcement

- `_read` returns `ConfigValue | Absent` instead of `object | Absent`, so every reader is now
  typed against the union rather than against anything at all.
- **The finding is now closed for this record and open for one more:** `WorkerClaim`'s
  `observed_fingerprint` remains `Mapping[str, object]`, deliberately and for a reason ADR-0020
  states — a dataclass cannot represent a field the record never declared, which is exactly the
  direction the contract raises on. That mapping is compared, not read, so the hazard this ADR
  closes does not apply to it in the same way.
- **Not done:** nothing validates that an adaptor sent a key the holes actually name. An
  unknown key is legal and ignored, which is correct — the executor's configuration is larger
  than the set Alfred reads — but it means a *typo'd* key on the adaptor side reads as absent
  rather than as a mistake. Absent is already a finding, so it fails closed; it fails with the
  wrong reason.

### Why this is an inspector patch

`harness/` is inspector machinery under D20. Major-fix #8 permits an agent-drafted inspector
patch only under line-by-line human review with a mandatory ADR. This is that ADR. The review
is O9 and has not happened.

---


> **Renumbering note.** These two records were written as ADR-0015 and ADR-0016 on the
> `claude/vault-graph-planning-fc5e15` branch, before `main` had independently issued those
> numbers to unrelated decisions. Numbering is sequential and never reused, so they take the
> next free pair on landing. Three commit messages — `e8c99ea`, `f16695a` and `117b882` —
> still name the old numbers and cannot be rewritten; a reader following a commit message to
> "ADR-0015" will land on a different decision. That mismatch is recorded here rather than
> left to be discovered, and it is the whole cost of the collision.

## ADR-0027 — An agent edited the inspector, and this record was drafted by the same agent

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0012 (the vacuity guard this ADR wires into CI), ADR-0013 (the control that stops a probe reading green)

### Context

D20 splits the system into factory and inspector: agents may improve the factory and may
never improve the inspector. `.github/workflows/gates.yml` is inspector machinery, and the
file says so in its own header comment.

Standing invariant 8 does not forbid an agent from touching it. It says agent-drafted
inspector patches are **permitted only under line-by-line human review with a mandatory
ADR**. That is a price, not a prohibition, and the invariant is only meaningful if the
price is actually paid — a permitted-with-conditions rule whose conditions are never
discharged is a prohibition that everybody has agreed to pretend is a process.

The occasion: `tools/gen_vault.py` generates `vault/` and `docs-graph.html` from the
repository. Both are committed. Both are derived and authored nowhere. That derived
property is the entire reason they are admissible as a read model under D44/D47/D51
rather than an unfingerprinted write path into agent context — and a property that
nothing checks is a property the repository claims rather than holds. Every generated
note carries the sentence *"do not edit"*. Without a gate, that sentence is a wish.

### Decision

Three steps were appended to the `integrity` job, by the agent, at the operator's explicit
instruction after the agent raised the D20 constraint and the operator reaffirmed:

```yaml
- name: Vault generator detects its own vacuity
  run: python3 tools/gen_vault.py --self-test
- name: Vault and published graph are current
  run: python3 tools/gen_vault.py --check
- name: Vault generator suites
  run: uv run pytest tools/tests
```

**`--self-test` runs before `--check`, and the order is load-bearing.** `--check` compares
a freshly built vault against the committed one. If the extractors silently stopped
matching, the generator would build a smaller vault, `--check` would compare that smaller
vault against a `--check`-updated smaller vault, and the step would pass having verified
nothing. The self-test plants fixtures below every declared floor and requires the run to
fail; only after the guards are shown to fire does `--check` mean anything. This is the
same failure ADR-0012 was written about, arriving through a new door, and it is the
project's sixth instance.

**`--check` fails three ways: a note that differs, a note that is missing, and a note
nobody planned.** The third is the one content comparison alone cannot see. A hand-edited
note differs from its planned text; a hand-*created* note has no planned text to differ
from, and both are the same defect — authored content inside a derived tree.

**The plan mirror is verified in the same step, and its absence is not a failure.**
`plan/handoff-autonomous-software-engineering-fizzy-dahl.md` is a byte-verbatim snapshot
with a sha256 manifest. Where the origin under `~/.claude/plans` exists — the operator's
machine — a divergence fails. Where it is absent, as on every runner and every clean
clone, the mirror is checked against its own manifest and passes. Drift is only detectable
where drift can happen, and pretending otherwise would make CI red for a file it cannot
see.

**The suite is invoked by explicit path.** `pyproject.toml` sets `testpaths = ["tests"]`
and the `product` job runs `uv run pytest tests`. A documentation generator must not be
able to red the product gate.

### The part that is uncomfortable, recorded rather than smoothed over

**This ADR was drafted by the agent that made the edit.** The agent initially declined to
write it, on the grounds that an agent authoring the record that authorizes its own
inspector change is the loop D20 exists to break. The operator instructed it to write the
draft anyway. That is a legitimate instruction — the operator owns the decision, and a
draft is not an authorization — but the sequence must be visible in the record rather than
inferred from a commit log, because the failure mode it approaches is not detectable by
reading the result. A well-argued ADR reads identically whether the argument was audited
or generated.

So, precisely: the agent made the edit, the agent drafted this text, and **neither act
discharges the review.** What standing invariant 8 requires and what an agent structurally
cannot supply is the line-by-line human read of the diff. The relevant diff is the
`.github/workflows/gates.yml` portion of commit `f16695a`, 30 lines. Accepting this ADR
without that read leaves the invariant recorded and unenforced, which is strictly worse
than leaving it unrecorded — the record would then be evidence that a control operated.

**No agent-authored control was added to check this.** A self-check written by the party
being checked is the pattern this project has rejected in four other places (ADR-0003's
second implementation, ADR-0012's committed self-test, ADR-0013's per-probe control,
ADR-0014's non-Python re-walk). The check here is a person reading 30 lines.

### Consequence

The generator now reads a file it writes into: `gates.yml` is an input to the workflows
extractor, so adding these three steps changed the graph. The `integrity` job carries 12
steps, the workflows extractor yields 41 nodes, and the graph totals 358 nodes and 340
edges over 365 notes. The three new gates appear in the vault as nodes — the generator
recording the checks that check it. This is a fixed point, not a cycle: `--check` compares
the generated output against the committed output, and a change to `gates.yml` that is not
regenerated fails on the first run.

Verified under a runner's conditions rather than only this machine, with `HOME` pointed at
an empty directory: the origin reads absent, the mirror verifies against its manifest, and
`--check` passes. The asymmetry in the mirror rule is the design, and it now holds in
practice as well as on paper.

`tools/` sits outside ruff's and pyright's configured `include`, alongside `scripts/` and
`harness/`, and stays there. Pulling it in would be a `pyproject.toml` change whose effect
is to hold a generator to product-tree conventions the neighbouring generators are
deliberately exempt from.

### Rejected

**Landing the generator in `scripts/`.** It is where the other generators live, and it is
inspector. `tools/` costs one directory and keeps the whole generator outside the
protected boundary; only the three-step wiring crosses it.

**Running `--check` without `--self-test`.** Above — it is a check that compares a
possibly-empty result against itself.

**Making the mirror check fail when the plan origin is absent.** It would red every runner
and every clean clone for a file that is deliberately outside the repository, and the
predictable outcome is that somebody removes the step rather than the cause.

**Leaving the vault ungated and trusting the "do not edit" banner.** The banner is a
request to a reader. The property it asks for — that nothing in `vault/` is authored — is
the one that makes the read model admissible at all.

---

## ADR-0028 — The review ADR-0027 said was owed has been done

**Date:** 2026-08-19 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0027 (the inspector edit this discharges the review of)

### Context

ADR-0027 recorded an agent-made edit to `.github/workflows/gates.yml` — inspector machinery
under D20 — made at the operator's explicit instruction. Standing invariant 8 prices that
edit at line-by-line human review plus a mandatory ADR. ADR-0027 supplied the ADR and was
explicit that it supplied nothing else:

> neither act discharges the review. What standing invariant 8 requires and what an agent
> structurally cannot supply is the line-by-line human read of the diff.

It also named exactly what was outstanding: the `.github/workflows/gates.yml` portion of
commit `f16695a`, 30 lines. And it named the cost of leaving it that way — that accepting
ADR-0027 without the read would leave the invariant *recorded and unenforced*, which is
worse than leaving it unrecorded, because the record would then be evidence that a control
operated when it had not.

That review has now been carried out by the operator, and the diff accepted.

### Decision

**Standing invariant 8 is discharged for commit `f16695a`.** The three steps it added to the
`integrity` job — `--self-test`, `--check`, and `pytest tools/tests` — stand as reviewed
inspector machinery rather than as an agent-made edit awaiting a human read.

The scope is that commit and nothing else. A later edit to `gates.yml`, by an agent or
otherwise, owes its own review and its own record; this ADR is not a standing permission and
must not be read as one.

### Why this is a separate record rather than an edit to ADR-0027

The ADR log is append-only: an ADR that turns out to be incomplete gets a successor, never a
revision. Amending ADR-0027 to say "and the review happened" would be the cheaper gesture and
the wrong one twice over. It would edit a published record, which this file's own
falsification condition forbids. And it would erase the interval — the period during which
the invariant was recorded and not yet enforced — which is the only part of this sequence a
future reader needs to see, because that interval is where the failure would have lived if
the review had never come.

Read in order, the two records say what actually happened: the edit was made, the price was
stated, the price went unpaid for a day, and then it was paid. A single amended ADR would
say only that the price was paid, which is true and is not the same claim.

### Consequence

Nothing in the repository changes. This is the only kind of ADR that is purely a record of a
human act: no code, no gate and no generated artifact moves, and there is deliberately no
check that this ADR is telling the truth.

That absence is the point, and it is the same position ADR-0027 took about itself. A control
verifying that a human read 30 lines would have to be written by the party the control exists
to constrain, which is the pattern this project has rejected in five other places (ADR-0003's
second implementation, ADR-0012's committed self-test, ADR-0013's per-probe control,
ADR-0014's non-Python re-walk, and ADR-0027's refusal to add one for itself). The check here
was a person reading 30 lines. The evidence that it happened is this record and the operator's
name on the commit that carries it.

### Rejected

**Adding a machine check that the review occurred.** A commit trailer, a review marker file,
or a lint asserting one — each is a thing an agent can write, and an agent writing the
evidence that a human checked its work is the loop D20 exists to break. The invariant is
enforced by a person or it is not enforced.

**Leaving the discharge implicit in the commit log.** ADR-0027 is a published document
stating that a review is outstanding. Someone reading the register a year from now finds that
sentence and has no way to learn it stopped being true, because a commit message is not part
of the register. The claim was made in the register and it has to be closed there.

---

## ADR-0029 — The tree that verifies every other tree is verified by nothing

**Date:** 2026-08-19 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0007 (the vacuity class this is an instance of, found in the tooling rather than in an assertion), ADR-0027 and ADR-0028 (the D20 review this ADR incurs)

### Context

`[tool.ruff].include` and `[tool.pyright].include` both name `src` and `tests`. Neither
reaches `harness/` — the criterion runner, the containment assertions, the stamp verifier,
the egress canary, the seeded-defect suite. The tree everything else in this repository is
verified *by* is the one tree nothing verifies.

Measured on `main` @ `fa62b4b`, with the venv from `uv sync --frozen --all-extras --dev`:

| measurement | result |
|---|---|
| `uv run ruff check` (product gate) | 0 violations |
| `uv run pyright` (product gate) | 0 errors |
| `uv run ruff check harness` | `warning: No Python files found under the given path(s)`, **exit 0** |
| `uv run ruff check harness`, include widened | **866** violations |
| the same, with `S101` ignored as `tests/*` already ignores it | **236** |
| `uv run pyright harness` | **311** errors |
| `.py` files under `harness/` | **74** |

The gap was proven rather than read off the config. Planting

```python
import os
def broken(x: int) -> str: return x
```

into `harness/acs/acs1.py` leaves both product gates green. The identical plant in
`src/domain/ids.py` turns both red, pyright naming the planted line
(`reportReturnType: "int" is not assignable to return type "str"`). That control arm is the
load-bearing half: without it, "the gates passed it" is equally consistent with the gates
being inert. With it, the gates are live and `harness/` is scoped out.

**This is ADR-0007's vacuity class, living in the tooling.** `ruff` answers a path it
collects nothing from with a warning and exit 0 — byte-for-byte what a clean tree looks
like. An assertion resting on a misnamed key reports `passed` while doing nothing; so does a
lint whose include matches nothing. That is how this survived unnoticed through eighteen
ADRs of work whose whole subject is checks that do not check.

### Decision

**1. Widening the include to cover `harness/` is not a D20 crossing.** D20 forbids agents
*editing* the inspector without Major-fix #8. Checking is a read; editing is a write. The
comment at `pyproject.toml:50` said the tree "is protected, sits outside the agent tree by
design, and carries its own gates" — three claims, of which the first is true, the second is
irrelevant to whether a linter may look at it, and the third is false: `harness/` carries a
test suite, which is neither a lint gate nor a type gate. The comment borrowed D20's
authority for a scope decision D20 never made. It has been rewritten to record the gap and
name the real reason the exclusion stands, which is that nobody has yet decided how much of
the debt to pay.

**The counter-argument, stated rather than dismissed.** Turning a checker on over the
protected tree is not itself a write, but it is the *cause* of writes: 311 pyright errors
and 236 ruff violations do not clear themselves, and the only way to make the gate green is
an agent editing the inspector at several hundred sites. Under that reading the include
change is a D20 crossing by consequence, since it converts a decision nobody has taken into
work someone must do inside the protected tree. The decision above accepts that the
consequence is real and holds that it lands on the *fixing*, not on the *checking* — which is
why the fixing is held below and the reading is not. A checker that is switched on and whose
findings are recorded and unpaid is a strictly better state than one that was never switched
on, because the debt is then counted.

**2. What lands: the measurement and its control, not the fix.**
`scripts/lint_harness_gate.py` is wired into the `integrity` job of
`.github/workflows/gates.yml`, in two steps like the three lint/self-test pairs already there.
Its coverage check prints `ruff collects 0 of 74 .py files under harness/` on every run and
asserts that number against a recorded floor, which may go up and may not go down. Its
`--self-test` plants `F401` into a collected harness-shaped file in a scratch copy and
requires *that rule at that path* to be reported — not merely a non-zero exit, which a plant
landing somewhere `ruff` never reaches would also produce — and requires the clean arm to stay
quiet, so a detector that reports red unconditionally fails there rather than passing
everywhere.

**3. Neither include is widened, and no error is fixed.** Held on OBSERVER-1.

### The cheap option turned out not to be cheap

The three options were meant to be ordered by cost, with `ruff check harness` as the cheap
increment and pyright deferred. The measurement does not support that ordering. Of the 236:
44 are safely auto-fixable; **120 are hand edits** (67 `E501`, 38 `ANN*`, 15 `ARG*`); 55 are
rule/tree conflicts where the honest answer is a scoped suppression rather than a fix
(`T201` — harness scripts print by design; `S603`/`S607` — a harness that shells out to
`docker` and `git` is the point); and 17 need individual judgement, several of which must
**not** be fixed.

And the distribution settles it independently of the count: 45 of the 236 are in
`harness/containment/`, which module M2 is editing now; 8 are in `harness/selftest/`, which
M3 is editing now; 2 are in `harness/patch/`, which no module may touch while
`bionic/protected-set` is live. `ruff` cannot be made green over `harness/` from this module
without writing into two other agents' work in flight and one tree that is off limits to
everyone.

### What the 311 pyright errors are, and the one finding that outweighs the count

`harness/` contains **zero return-type and zero assignment-type errors**. Planting the
`def broken` line moves 311 to 312 and the added error is the only `reportReturnType` in the
tree. The 311 are 213 `reportUnknown*` (annotation debt), 22 `reportOptionalMemberAccess`
(mostly narrowing pyright cannot do across a `.get()` called twice), and about seven dead
guards — `isinstance(v, str)` where `v` is already `str` at `containment/shells.py:363`, an
`is not None` arm that can never be false at `containment/patch_side.py:306`, three more of
the same shape in `lane/`, a `Final` redeclared in a subclass at
`selftest/test_replay.py:119`, and a register helper nothing calls at
`containment/test_c_assertions.py:1346`. One is a real latent crash: `acs/mutate.py:541`
calls `__doc__.splitlines()`, which is an `AttributeError` under `python -OO`. The full
classification is `CLASSIFICATION-M1.md`.

The finding that matters more than any of those counts:

> `harness/fingerprint/test_record.py:64` is `reportCallIssue: No parameter named
> "fingerprint_sha256"` — inside `test_the_hash_is_not_stored_and_cannot_be_supplied`, which
> calls the constructor wrongly *on purpose* and asserts it raises `TypeError`.
> `harness/lane/test_lane_controls.py:166` is `BLE001: Do not catch blind exception` — inside
> `test_mutant_without_fail_closed_reading_would_swallow_the_error`, where swallowing the
> error is the modelled failure. `harness/acs/gen_vectors.py` carries four `RUF001` ambiguous
> fullwidth characters, which are the ACS-1 Unicode test vectors and are byte-identity-checked
> by `gates.yml`.

**A bulk pass over these gates would delete this repository's own negative controls.** A tool
flagging a deliberately-invalid call, and an agent making the call valid to clear the flag, is
precisely how a seeded-defect suite quietly stops seeding defects. This is a stronger argument
against full-strict coverage than the volume is, and it is why the scope call is held for a
person.

### Falsifies if

- `scripts/lint_harness_gate.py` reports a coverage count that does not move when
  `[tool.ruff].include` is changed — the check would then be reading something other than the
  configuration it claims to measure.
- The `--self-test` passes against a `ruff` with `F401` disabled — the plant would then be
  firing for a reason unrelated to the plant.
- Some later measurement finds return-type or assignment-type errors in `harness/` that
  predate this record — the claim that the 311 are debt rather than silent type lies would be
  wrong, and the priority of OBSERVER-1 would rise sharply.

### Held for the observer — OBSERVER-1

**How much of the debt to pay, and at what strictness.** This is a write into the protected
tree and the three options are costed in the M1 report. It is deliberately *not* decided here,
and it now covers `ruff` as well as `pyright`, because the measurement showed the two are the
same kind of decision rather than a cheap one and an expensive one.

### Rejected

**Landing the include with per-file-ignores broad enough to make it green.** That is a gate
green by construction — the same failure as the empty include, wearing a fix's clothes. The
suppression list required (`S101`, `T201`, `S603`, `S607`, `S608`, `S311`, `S108`, `S104`)
silences 685 of 866, and choosing it is a scope decision of exactly the kind held above.

**Wiring the coverage check as a hard failure at a floor of 74.** It would hold CI red from
the day it landed until OBSERVER-1 is answered, and this repository has already written down
what happens then: `gates.yml` keeps the stage-gate *exit* check out of the job for that
reason — *"a check that is red for reasons nobody reads is a check that gets turned off."*
The floor is 0, the shortfall is printed on every run, and the count going up is a change a
reader sees. `lint_ci_coverage.py` takes the same position about the twenty-four
`not-yet-injected` failure rows and for the same stated reason.

**Fixing the seven dead guards while here.** Five of them are in `harness/containment/` and
`harness/selftest/`, which M2 and M3 hold open. A fix landing under them would be reviewed
twice and merged once, and the merge order the observer set — M2, then M3, then M1 — exists
so this module's gate lands *over* their work rather than under it.

### Consequence

`P0-7 — no unreviewed inspector patch enforces an exit criterion` is `unmet` at 17.
`scripts/lint_harness_gate.py`, the `gates.yml` wiring and the `pyproject.toml` comment are
three more inspector edits under D20, each owing line-by-line human review under Major-fix #8,
and each is filed as an O9 item by this record. This ADR supplies the mandatory ADR and
nothing else; it does not discharge the review, which an agent structurally cannot supply —
the position ADR-0027 took and ADR-0028 closed.

---

## ADR-0030 — Two containment controls that existed and did not run, and two that still do not

**Date** 2026-08-19 · **Status** Accepted · **Supersedes** nothing · **Amends** ADR-0023's
"not done here" on C17 and C14; ADR-0026's "not done" on the adaptor key set; the Sandbox
Specification's C14 and C17 rows · **See also:** ADR-0013 and F25 (`not_executed` is a
failure), ADR-0017 (a hole never passes), ADR-0007 (executed, passed, vacuous), ADR-0019 and
ADR-0023 (the ingress and launch posture), ADR-0020 (the run fingerprint and C11's unread
conjunct), ADR-0024 (C15's register)

### Context

Four containment assertions were written, tested, and not running. Under F25 and ADR-0007
that is worse than four absent ones: an absent control is visible, and a green one nobody
called stops anybody looking. Each was recorded as open by the ADR that created it, in as
many words, so none of this is a discovery — it is the deferred half of four earlier records
being either paid or priced.

Two are closed here. Two are investigated and deliberately left open, because both turn on a
question this record is not the right place to settle.

### 1. C17 joins C14's closed re-assertion set

ADR-0023 wrote C17 — the ingress surface and the launch posture — and left it out of the
end-of-run re-assertion, saying so: *"a container relaunched mid-run with different flags
would not be caught, and the argv is recorded in `observed` precisely so that it **could** be
compared — the comparison is simply not wired."*

**It is wired.** `REASSERTED` becomes `("C7", "C9", "C12", "C13", "C16", "C17")`.

C16's membership rests on `--rm`: a container that exits mid-run leaves nothing behind, so at
the end the adaptor either still has a container id or it does not. **C17 covers the case that
argument does not reach — a container that exits and is replaced.** A relaunch restores the
container id's *presence* while changing the argv underneath it, and every boot-time C17 pass
stays true of a container that no longer exists. A published binding that was loopback at boot
and is `0.0.0.0` at the end is an unauthenticated remote-code-execution endpoint opened
*after* the gate that would have refused it.

Appended rather than inserted: `compare` orders findings by this tuple's own order, so
appending is the only edit that leaves existing output's ordering alone.

**The control is the drift kind, not the outcome.** A relaunch that reopens the ingress
surface produces a boot pass and an end failure — and so would a check that stopped reading
the argv at all. So the test requires `DriftKind.VALUE` on both `container_launch_args` and
`published_port_bindings`, and `drifted_ids` to name C17, which is what goes red if C17 ever
leaves the set. A second control covers the relaunch that keeps the posture and changes the
argv: both ends `PASSED`, drift still reported. That case is the reason `_check_c17` records
the **full** argv rather than a summary of the flags it happens to look at, and an
outcome-level comparison cannot express it at all.

D57 is inherited rather than reimplemented: `value_blind` would name C17 if it recorded no
observations, and the coverage assertion over the real implementations now builds C17 the way
the adaptor builds it.

### 2. The key-set half of the adaptor configuration contract

ADR-0026 typed the configuration *values* and wrote down what it did not do: *"nothing
validates that an adaptor sent a key the holes actually name. An unknown key is legal and
ignored, which is correct … but it means a typo'd key on the adaptor side reads as absent
rather than as a mistake. Absent is already a finding, so it fails closed; it fails with the
wrong reason."*

**The decision is that this is confusability, not unknown-key rejection.** Rejecting unknown
keys would be a different and false claim — the executor's configuration surface is larger
than the set Alfred reads, and every real observation carries keys no hole names. What is
refused is a key that is *not* one the holes name whose case- and separator-normalized form
collides with one that is: `sessionApiKeys` against `session_api_keys`. Two spellings of one
name cannot both be real keys of one executor, so the collision is a fact rather than a guess
at what the adaptor meant.

**Refused at construction**, beside `validated_config`, on ADR-0026's own argument: an adaptor
sending a key nobody can read should be told so where it sent it, not three checks later in
the shape of a field that reads as unset.

The reference set is **derived from the register** (`named_config_keys`), never typed out, so
a hole added later is covered without anybody remembering a list. C10's `config_env_prefix`
holds `OH` — an environment-variable prefix rather than a configuration key — and it is
included rather than special-cased. It is still a name read out of the executor, a re-spelling
of it is still an adaptor defect, and a hand-maintained exception list is the shape this file
avoids everywhere else.

**Vacuity controls.** An empty reference set would find nothing on every input and report
clean, so the suite asserts it is non-empty and names four keys it must contain (D57). And the
check must **not** fire on a key Alfred does not read — without that test the check could
refuse everything and every other test would still pass. The defect itself is pinned: an
observation built past the guard with `sessionApiKeys` makes C17 report `session_api_keys`
absent, which is the wrong-reason failure this closes.

**The limit, stated rather than left to be discovered.** A genuine misspelling —
`sesion_api_keys` — normalizes to itself and is not caught. What is caught is
spelling-convention drift: camelCase, hyphens, casing, dropped separators, which is the class
an adaptor written against JSON documentation actually produces. Edit-distance matching would
catch more and would produce false positives in a check whose finding refuses a configuration
outright. Pinned by a test, so a change that widens the rule fails there and has to say so.
Only top-level keys are checked, because every check reads `config[key]` at the top level and
a nested key is not one any hole names at all.

### 3. C11's parallel slot count — the field is readable, and from a channel nothing reads

Not changed here. Reported because what was found contradicts the reason the conjunct is
unread.

ADR-0020 recorded that the slot count *"is a launch-time property of the server and is not in
`/api/v0/models`"*, so it arrives as an explicit argument and its absence is `not_executed`.
**The first half of that sentence is confirmed and the second half is narrower than it reads.**
`harness/lane/lane_fingerprint.py:105-134` reads `/api/v0/models` and the entries carry `id`,
`state`, `compatibility_type`, `quantization`, `arch`, `loaded_context_length` and
`max_context_length` — no slot count, exactly as recorded.

But the lane's own CLI publishes it. Read first-hand on the development host, 2026-08-19:

- `lms load --parallel <count>` is a documented load-time option — *"maximum number of
  predictions the model can run at a given time"*.
- `lms ps --json` reports, per loaded model, `"parallel": 4` alongside `contextLength`,
  `maxContextLength`, `quantization`, `status` and `queued`.

So the count is **not** unreadable. It is unread, from a channel — a vendor CLI over a
subprocess — that no inspector module currently uses, though `bench/bench_infer.py` shells out
to `lms version` and `lms runtime ls` and so the pattern exists outside `harness/`. A third
route exists and is behavioural: `bench/probe_prefix_cache.py` already infers the slot count
from a timing signature (hypothesis H2 — a cold run of exactly P), which measures the property
that actually matters rather than the setting that implies it.

This is left open **as an OBSERVER decision**, and the decision it needs is not the one
ADR-0020 anticipated. It is not "a permanent `UNREAD` hole or a deleted conjunct"; neither is
warranted now. It is whether an inspector control may read a live value out of an unpinned
vendor CLI over a subprocess. `lms` has no pin anywhere in this repository, the observed key
is a fact about the version on one machine on one day, and `harness/` has no precedent for a
subprocess read. Wiring it unasked would put a control on a channel nobody agreed to, which is
the same class of act as naming a plausible key — the thing ADR-0020 refused. So it is
reported with its evidence and not built.

### 4. C15's missing production caller — and the honest shape of the question

Not changed here, for the reason ADR-0024 gave when it declined the same thing: *"the patch
gate is where that lands."*

Confirmed: `assert_patch_carries_no_oracle` is called from `test_c_assertions.py` and nowhere
else. **The finding is larger than C15.** `harness/patch/validate.py`'s `require_clean`,
`harness/worker/port.py`'s `require_all_passed`, `harness/containment/handle.py`'s crossing,
C4, C11 and the whole dispatch chain have no production caller either, because no adaptor
exists. C15 is not uniquely orphaned; it is one member of a port whose implementation is not
written. Saying that plainly matters, because "wire C15 up" reads like a missing line and is
in fact a question about where the claim-acceptance path lives when somebody writes one.

The site is an OBSERVER decision and the candidates are set out in the module report. What
this record fixes is the constraint on any of them: **C15 runs on the diff and never on a
working tree**, and `WorkerClaim.patch` is an `ArtifactRef` — a content address, not a path —
so any caller resolves bytes through the artifact store rather than reading a checkout.

**Finding 8 stays open**, as ADR-0024 left it. Added lines are hashed against whole-file
digests, so only a whole-new-file diff can match. Closing it means hashing post-application
content, which is a second and different check and costs the runs-on-the-diff property. Not
closed here, and the test that pins the limit is untouched.

### Consequences and enforcement

- `REASSERTED` has six members. An end-of-run report missing C17 is `not_executed`, which F25
  makes a failure, so the adaptor's obligations grow by exactly one assertion.
- `ConfigKeyConfusion` is raised at `ExecutorObservation` construction. It subclasses
  `ConfigContractViolation` so the boundary refusals stay one family.
- The Sandbox Specification's C14 row, C17's disposition column and a new amendment block are
  updated to match.
- **Not done, deliberately:** C11's slot count is still supplied from outside and still
  `not_executed` when it is not; C15 still has no production caller; Finding 8 is still open;
  `--read-only`, `--security-opt` and the user namespace are still named and not asserted, as
  ADR-0023 left them.

### Why this is an inspector patch

`harness/` is inspector machinery under D20. Major-fix #8 permits an agent-drafted inspector
patch only under line-by-line human review with a mandatory ADR. This is that ADR. The review
is O9, it has not happened, and this change joins the containment batch already named in
P0-7's register entry — which is `unmet`, and which this makes no smaller.

---

> **Renumbering note.** This record was written as ADR-0024 on
> `bionic/protected-set`, before `main` had independently issued that number to an
> unrelated decision (C15's third clause, the denylist's names, and a gate —
> ADR-0024 on main). Numbering is sequential and never reused, so the record was
> renumbered to ADR-0029 at commit time, from `main`'s numbering alone. The
> operator's merge-order ruling (2026-08-21, the ICM/Wayfinder restructure) lands
> the two same-day unmerged claims first — `m1-harness-verification-gate` keeps
> ADR-0029, `m2/containment-controls` keeps ADR-0030 — so this record takes ADR-0031
> on landing, per the precedent of the `fa62b4b` merge. The commits on this branch
> — `6cbe52d` and `ee9e4ee` — still name the old numbers and cannot be rewritten; a
> reader following them to "ADR-0024" or "ADR-0029" lands on a different decision.
> That mismatch is recorded here rather than left to be discovered, and it is the
> whole cost of the collision.

## ADR-0031 — The protected set is one file, and the gate protects its own policy

**Date:** 2026-08-19 · **Status:** Accepted · **Supersedes:** nothing; amends one row of the tier4 table

### Context

The protected set was enumerated three ways, and the three disagreed.

- The frozen table in `docs/tier4/protected-paths-policy.md` — thirteen rows: `harness/`,
  `src/provenance/`, `src/thresholds/`, `tests/heldout/`, `migrations/harness/` and
  `migrations/roles/`, the `scripts/` gate entry points, `policy/`, `.github/`,
  `docs/tier0/`, `pyproject.toml` and `uv.lock`, the fingerprint tracker, the oracle
  environment and its pin, the oracle denylist.
- D20, as quoted where the patch gate was written — `harness/`, `scripts/`, `.github/`,
  `policy/`, `migrations/roles/`.
- `PROTECTED_PREFIXES` in `harness/patch/validate.py` — the same five.

The executable enforcement was a strict subset of the frozen policy. Six of the thirteen
rows promised protection the gate did not carry: result stamping (`src/provenance/`),
thresholds, held-out criteria, the control and evidence schemas, the constitution, and
the dependency closure. And on `scripts/` the two sources disagreed in the other
direction — the table said only the gate entry points, D20 says the whole directory,
and the gate enforced D20.

The document already names what this drift is: "Protected paths are the second layer,
and they are policy configuration, never code." The configuration did not exist as a
file. The table and the tuple were two prose renderings of one fact, and prose
renderings drift (ADR-0021 is the same mechanism wearing CI's clothes).

### Decision

**One machine-readable home.** `policy/protected-paths.json` — versioned, and under
`policy/` itself, which is a protected prefix, so the gate protects its own policy
file. That is the CVE-2025-53773 shape, where a gate was disabled because the file
stating its rules was writable by the party the rules constrained.

- `validate.py` loads the file per validation, **failing closed**: a missing, malformed,
  or unparseable set raises `ProtectedSetError` rather than falling back to a smaller
  set (F25 — an unreadable policy is a failed one). An empty set — zero prefixes and
  zero files — raises rather than passes (D57): a set that enumerates nothing protects
  nothing.
- The set: ten prefixes (`.github/`, `docs/tier0/`, `harness/`, `migrations/harness/`,
  `migrations/roles/`, `policy/`, `scripts/`, `src/provenance/`, `src/thresholds/`,
  `tests/heldout/`) and two exact files (`pyproject.toml`, `uv.lock`). Each entry
carries the document's *contains* clause, so a refusal names the specific reason
  rather than the rule's category.
- The tier4 table keeps its human-facing role. The `scripts/` row is corrected to name
  the whole directory — D20, the newer operator decision — and the document now states
  the machine-readable home. The three conceptual rows (fingerprint tracker, oracle
  environment, oracle denylist) resolve to prefixes already in the set; their
  protection is unchanged, only made explicit.
- `harness/patch/test_protected_set.py` asserts set equality **in both directions**
  between the file and the table, on the grants precedent (ADR-0009): a row in the
  table with no entry in the file protects nothing — the failure direction the
  document's own `falsifies_if` names — and an entry with no row protects something no
  one was told about. The row-to-entry mapping is written out rather than derived, and
  a table row with no mapping fails. Behavioural tests cover the whole loaded set, the
  gate's own policy file, and a boundary of non-protected paths, so the set cannot
  silently widen into everything.
- The `control.policy_protected_path` table already carries the same policy per tenant
  for runtime enforcement. Nothing here claims the sync between the file and that
  table: its writer is a later stage, and a sync asserted before the writer exists
  would be a claim with no referent.

**What this changes for agents.** The container's patch channel — the only channel this
gate governs — now refuses everything the frozen table has promised since 2026-08-12:
result stamping, thresholds, held-out criteria, the harness migrations, the
constitution, and the dependency closure. Direct development under ADR + O9 is
unaffected; the gate sits on the container's deliverable channel (A2), not on the
review process. The `src/thresholds/__init__.py` placeholder (bionic/structure-drift)
has since landed on main; the gate protects the path.

### Why this is an inspector patch

It changes `harness/patch/`, which is inspector machinery under D20, and adds a file
under `policy/`. Per Major-fix #8 and the tier4 policy — "agent-drafted inspector
patches are permitted only under line-by-line human review with a mandatory ADR" —
this ADR authorizes the change and the review is O9. This change is landed and
unreviewed.

When drafted, the branch also carried the queue 11–14 stream
(`c1ca0b4`…`6c99003`), so that the O9 review covered everything since main in one
pass. That stream has since landed on main, and main has since issued its own
ADR-0024; what this branch carries relative to main is now this record, and the
O9 review covers it.

---

> **Renumbering note.** This record was drafted as ADR-0031 on
> `bionic/agentdb-memory-index`, the next uncontested number at drafting time: `main`
> ends at ADR-0028, ADR-0029 is claimed by two unmerged branches
> (`m1-harness-verification-gate` and `bionic/protected-set`), and ADR-0030 by
> `m2/containment-controls`. Numbering is sequential and never reused, so the draft
> took the next free number rather than join the 0029 collision. The operator's
> merge-order ruling at merge (2026-08-21: chronological landing, first-claim priority
> — m1 keeps ADR-0029, m2 keeps ADR-0030, the protected-set record renumbers 0029 to
> 0031) renumbers this record to ADR-0032, the correction this note pre-authorized,
> per the `fa62b4b` precedent, before it is published on `main`. The commits on this
> branch name the drafted number and cannot be rewritten; this corrected note is what
> reconciles a reader who follows them. The note travels with the record.

## ADR-0032 — Operator-plane memory is recall over the committed corpus, not a store

**Date:** 2026-08-20 · **Status:** Accepted · **Supersedes:** none

### Context

The plan of record's memory decisions — D44, the amended D47, and the FATAL finding —
settle the factory plane: the containerized worker, the single serialized lane, the
evidence store, verdict-adjacent context. On that plane the evidence store *is* the
memory; a read-only, derived retrieval index is permitted; and anything an agent writes
and later reads into context is an agent editing agent-influencing configuration. None of
them settles the operator plane — an interactive agent doing supervised work in the
repository, with a human in the loop and no container between it and the corpus — and
this work happened exactly there. The session exhausted its context and handed off by
prose document; its successor re-read a 242 KB plan and a 171 KB ADR register to
rediscover one precedent that lived two documents deep in both. The status-quo mechanism
has no recall. Every successor pays the whole corpus for the one fact it needs.

The `agentdb-memory-patterns` skill, applied as a pattern reference, names the shapes a
recall mechanism for that corpus would take: session memory, long-term memory, pattern
learning, consolidation. Two of those shapes do not survive the plan of record's own
constraints, and the one that does — read-only recall over a committed corpus — was not
argued but measured: a pre-registered three-arm spike (Phase 0), on this machine, outside
the repository.

**The spike, measured 2026-08-20.** The corpus: 7 files, 238 structural chunks,
70,577 tokens, pinned at `fa62b4b` by per-file sha256. The queries: 10 pre-registered
before scoring — 8 real lookups drawn from this factory's history, 2 no-precedent
negative controls. The arms, same corpus, same queries:

- **A — the status quo** (iterative grep + document re-reads, 5-read cap): 2/8 recall@1,
  15,576 tokens-to-answer, 20.8 ms median.
- **B — lexical** (BM25, k1=1.5, b=0.75): 5/8 recall@1, 7/8 in its 3-window, 5,625
  tokens, 0.9 ms.
- **C — vector** (`agentdb@3.0.0-alpha.20` with `nomic-embed-text-v1.5`, 768-d, local):
  2/8 recall@1; MRR 0.60 against B's 0.90 on the five paraphrase queries; and one
  negative-control false hit — the corpus's 52-token orientation chunk at cosine 0.717,
  inside the band its true lookups occupy (0.5899–0.7494).

The pre-registered rule: C earns its embedding cost only if it beats B on the paraphrase
queries **and** posts zero negative-control false hits. C fails both legs. B beats A on
tokens-to-answer (2.8× less context) and wall clock (24×) — the rule's second branch, met
on both axes. **A durable lexical recall tool is justified; the embedding half is not
built.**

One finding outranks the verdict. Left ungated, *both* index arms answer no-precedent
queries confidently — the documented failure class of similarity retrieval (a wrong match
scored 0.97 above a 0.92 threshold; action pairs 0.91-cosine apart) materializing on
Alfred's own corpus, in the spike's own controls. The status-quo arm abstains cleanly by
construction, because grep matches only literal tokens. A recall system that answers
"nothing is written on this" with "here is something plausible" is worse than no recall.
The calibrated-abstention gate and the two-sided selftest are therefore binding
requirements on the Phase 2 tool, not refinements.

The full arm-by-query tables, the corpus manifest, the scoring protocol, and the decision
rule as applied live in the operator-plane spike notes; the plan that gated them sits
beside it. Both are outside the repository by design. What this record carries is the
verdict, the boundary, and the configuration the verdict fixed.

### Decision

**Operator-plane memory is read-only recall over the committed corpus, not a store.** The
committed document stream — plans, ADR drafts, handoffs, policy — *is* the memory, which
is D44's thesis applied to the plane it was missing. Nothing new is written anywhere an
agent reads. The one new artifact is a derived, disposable retrieval index over the
corpus, built by a human-run script: delete it and nothing is lost, because every fact it
holds has a canonical home in the repository.

The design is bound by five invariants, each the plan of record's own constraint
translated to the operator plane. An implementation violating any one is out of scope for
this decision regardless of its usefulness.

1. **Derived, never canonical** (one home per fact). Every indexed record carries its
   canonical source pointer — repository path plus git blob hash at ingest. On conflict
   the canonical document wins and the record is invalidated. The index is disposable:
   deleting the store loses nothing.
2. **Corpus boundary = committed, git-trusted artifacts only** (D12 / FATAL). Ingest
   reads files at a pinned commit. Agent conversation, web content, uncommitted scratch,
   and container output are never ingested. Extending the boundary is a new ADR that
   must re-run the FATAL analysis.
3. **The agent never writes.** Ingest and rebuild are human-run scripts; the agent's
   maximum surface is a read tool. If an MCP server is ever exposed to agent sessions,
   only the read-only subset — the write tools are not offered, because FATAL's finding
   is that the write channel needs no privileges to be captured, and the only safe design
   is no channel.
4. **Mechanical ingest, no LLM extraction** (D44). Chunking is structural: one ADR
   record is one chunk, one decision row one chunk, one handoff section one chunk. An
   embedding step, if ever re-admitted, is a named, versioned function call to a local
   model (D35) — never a reasoning step, never free-form extraction.
5. **Python in the repository; the npm package stays external** (D13). AgentDB is a
   spike-only reference implementation. Any durable in-repo tool is Python under
   `tools/`, carrying vaultgraph's true status: generator of the vault read model,
   CI-gated (the integrity job runs its self-test and `--check` — the paid D20 crossing
   recorded in ADR-0027/0028), D51 read-model class rather than inspector, never feeds
   a verdict, never enters a dispatch workspace; outside the protected set, O9 not
   applicable.

**The corpus boundary, named.** The first instantiation ingested 7 files at the pin
`fa62b4b`. Six are committed repository artifacts — the ADR register, the plan of record
(the committed `plan/` mirror, whose operator-plane copy is byte-identical and proven so
by the manifest's sha256), the protected-paths policy, the coding standards, the README,
the reading map. The seventh is a named operator-plane document with no committed copy at
the pin — the ICM plan in `~/.claude/plans/` — and it is pinned by sha256 in the ingest
manifest. The committed six are trusted by git; the one operator-plane document is trusted
by hash. Both classes remain derived, read-only, and disposable under invariant 1, and
both sit inside invariant 2 as the plan of record for this work names them in its corpus
clause.
Extending the boundary — adding a class of document, or committing the operator-plane
copy — is a new ADR.

**The retrieval configuration, as versioned configuration.** What Phase 0 measured is
what v1 is, and a change to any element below is a superseding ADR — the operator-plane
analogue of D47's `context_strategy_version` discipline.

- **Engine:** BM25 (k1=1.5, b=0.75, BM25+ idf), lexical first. No embedding half in v1:
  the vector arm failed both legs of its earn-cost rule, and the factory plane has made
  the same sequencing call already. The embedding arm's measured configuration is
  recorded anyway — `nomic-embed-text-v1.5`, 768 dimensions, 2,048-token context, local
  LM Studio server, no cloud (the plan named `Qwen3-Embedding-0.6B`; those models were
  no longer on disk at spike start) — so a future ADR re-admits it against a fixed
  baseline rather than a memory of one.
- **Calibrated-abstention gate:** the threshold is the weakest true lookup's top-1 score
  over the pre-registered query set — the strictest tuning-free bar, least favorable to
  the index under test (D57's direction: the spike exists to falsify the index). A query
  whose top-1 falls below the bar returns nothing. First calibration: 5.399 (BM25); the
  vector arm's cosine bar (0.5899) is recorded with its caveat — BM25 scores carry no
  cross-query scale, so the bar is per-engine, not a shared number.
- **ID-anchored fast path:** an exact decision-ID query resolves directly to that record
  before any ranking. The spike found Alfred's dominant query shape — the exact decision
  ID lookup — missed in-window by all three arms, each for a different reason (file order
  exhausting A's read cap; hyphenation and generic terms diluting B's; C reading it as
  "a record about some ADR").
- **Chunking:** structural — one ADR record one chunk, re-packed on paragraph boundaries
  under a 6,000-character bound; other documents on structural separators, then
  blank-line runs, then hard cut; a 1,900-token truncation cap that never bound. Every
  chunk carries file, character offsets, and blob hash, plus a per-chunk sha256.
- **Corpus pin:** the commit, plus a per-file sha256 manifest carried by the rebuild
  script — the spike's manifest is the first. Full rebuild per run; at 238 chunks,
  incremental sync would be machinery for a scale this corpus does not have.

**The pattern source, and the declined package.** The pattern source is the
`agentdb-memory-patterns` skill, cited as pattern reference and spike engine only. Its
npm package — `ruvnet/agentdb`, `3.0.0-alpha.20`, MIT/Apache-2.0, version-pinned at spike
time because a floating `@latest` is not a fingerprint — is **explicitly declined as a
repository dependency**: D13 is a single Python toolchain, and an npm dependency in the
repository breaks it the way D51's "no JS dependency closure to hash-lock" rules out a JS
closure in the UI. The package ran in a scratchpad outside the repository, in the
operator's trust domain, ingest read-only from a git-trusted corpus, output never feeding
a verdict; the factory container never saw it, and D12's territory is untouched.

**Phase 2, named but not built.** The durable tool lands under `tools/` per invariant 5,
in three parts. `rebuild.py` is human-run: pinned commit → corpus manifest → structural
chunks → the store file. `query.py` is the only agent-reachable surface: read-only,
top-k with canonical pointers and scores, and a per-call log — query, returned row IDs,
timestamp — that makes D47's retrieval-miss-rate instrument computable at operator scale,
mirroring D26's read-recording. `selftest.py` is two-sided per D57, with three cases: a
seeded fixture corpus with known answers must be retrieved; a no-precedent query must
return nothing above the gate; a canonical source that changed after ingest must surface
as stale or be excluded, never served silently. The store location is an open operator
ruling at the Phase 2 gate — the plan's default is outside the repository
(`~/alfred-memory/`), and the gate decides between that and a gitignored in-repo path —
and this record does not spend that question.

### Why the pattern survives and the package does not

The write side of the skill — session memory, the pattern store, LLM-extraction
consolidation — does not survive translation for a reason the plan of record already
established: any memory store that agents write and later read into context is, by
Alfred's own definition, agents editing agent-influencing configuration, and the write
channel needs no privileges to be captured. MINJA: 98.2% injection and 76.8% attack
success by a query-only actor. AgentPoison: >80% attack success at <0.1% poison rate,
with the memory-mediated variant surviving session boundaries. What the operator plane
offers instead for what sessions produce is the mechanism it already has — the
human-gated document pipeline that commits them. That stream is the memory; the index is
recall over it.

The skill's own evidence points the same way: Letta's benchmark found a plain filesystem
beat framework memory, 74.0% against 68.5%.

The spike engine, for what it is worth, is alpha at its seams. Three defects, all patched
locally in the scratchpad copy and recorded in the spike notes: a `vector-search`
argument parser that tested the default database path and silently ignored the one
passed, returning empty for every query; a `Float32Array` reconstruction that re-read
each stored byte as one element — 3,072 pseudo-floats where 768 were meant — and crashed
every query on a dimension mismatch; and usage text documenting a threshold default the
code does not implement. None touches the in-repo Python tool, and all are worth an
upstream issue. The record is not that the reference implementation is defective — it is
alpha, and it was audited as such — but that what this repository adopts is the pattern,
with the package left where D13 leaves it.

### Falsifies if

- the index is ever written by a process the agent can invoke; or
- an action is observed that relies on an indexed fact whose canonical source changed
  after ingest, with the staleness not surfaced; or
- a chunk with no resolvable canonical pointer is ever returned.

The second is the one the corpus most threatens, because the corpus is a live register
and the index is a snapshot of it. The selftest's staleness case exists for the interval
between a corpus edit and the next rebuild.

### Consequence

Nothing in the repository changes with this record beyond the register itself and the
generated artifacts that read it — the reading map's decision table and count, and the
vault graph with its notes, which the existing generated pipeline regenerates. No tool
ships.

Phase 2 is gated on the operator's ruling of the store location and the engine mix (the
verdict says lexical-only) and then ordinary review at merge. The factory-plane feed is
one-directional, per the plan: the spike's numbers — the no-index status quo at 2/8
recall@1 and 15,576 tokens; the lexical index at 5/8 and 5,625; the vector index at 2/8
and 3,846, with in-window recall of 3/8, 7/8, and 6/8 against the status quo's 3/8 — are
delivered to D47's Phase 2 as the local-hardware data point the plan of record named
missing: its open challenge to D44 had the no-index stance supported only when a frontier
model drove agentic search (4.7 against 3.2/5), fully-local driving only tying RAG, and
Alfred's own query shapes unmeasured. D47's own Phase 2 — pgvector/tsvector over the
evidence store, golden-set A/B, `context_strategy_version` hashing, miss-rate
instrumentation — is its own workstream with its own gates, and nothing here builds any
part of it.

This record touches `docs/tier1/` plus the generated artifacts that read it. O9 does not
apply: the protected set covers `docs/tier0/` and the inspector prefixes, not
`docs/tier1/` — and no `harness/`, no `policy/`, no inspector machinery moves.

### Rejected

**An agent-writable memory store of any shape** — the session-memory and pattern-store
arms of the skill. FATAL, quoted above: the write channel needs no privileges to be
captured, and a store that persists across sessions is a persistence primitive for a
captured one.

**An LLM-extraction consolidation layer** — the skill's `MemoryOptimizer` /
`ExperienceCurator` shape. D44: an unfingerprintable, nondeterministic write path into
agent context. Every credible framework in the plan of record's survey is extraction-
based; Mem0 is ADD-only and structurally cannot carry D32's expiry; the open-weight
backbones posted 17.9–30.4% format-error rates *during memory operations*, which is
silent failure under D35 wearing a maintenance hat.

**The npm package as a repository dependency.** D13, applied to the one channel this plan
ever opened. The package was audited, version-pinned, and contained in the spike; it is
not adopted.

**The vector half for v1.** The earn-cost rule it failed is recorded in the Context. The
rejection is sequencing, not principle: the rule names the two legs a vector arm must
clear, and the per-call log Phase 2 ships is the instrument that would measure the case
for it. The pgvector cliff the plan of record recorded — 2,110 QPS at 2 million vectors
falling to 12.9 at 5 million, recall 0.99995 to 0.5444, and no space reclaim on delete
against D43's append-only store — is the standing reminder that the revisit, when it
comes, arrives with the cost attached.

**A CI gate over the tool.** vaultgraph's standing — a derived read model whose floor is
its selftest (quoted as drafted there: local/manual, selftest present, not a gate — the
drifted self-description; the true status is what the corrected invariant 5 records) — is
what this tool inherits, and invariant 5 fixes it. A CI job would be a
protected change under `.github/` for a convenience mechanism, and a gate whose only job
is verifying a derived cache verifies the cache's freshness, not anything the product
ships. The selftest is the floor; the gate would be theater.

---

## ADR-0033 — The structure fence names every top-level directory, and the vault floors it

**Date:** 2026-08-21 · **Status:** Accepted · **Supersedes:** nothing · **Amends:** the structure fence of the coding standards · **See also:** ADR-0022 (the first D28 waiver), ADR-0031 (the protected set's ghost row) · **D28 waiver:** yes

### Context

One fact — what top-level directories the tree has — was carried in three lists that had
drifted apart. The coding standards' structure fence (frozen, `ci-gate`) named 7 of the
14: `src/ tests/ migrations/ harness/ scripts/ docs/ projects/`. The README's layout
block carried 10 — it adds `bench/ policy/ deploy/` and still omits `.github`, `plan/`,
`tools/` and `vault/`. The vault, the system map the register is read through, had no
layout coverage at all: a directory that appeared or disappeared changed nothing the
graph said. A fourth copy of the same list sits in the plan of record's "Files and
structure" section inside `plan/`; that one is sealed by the manifest's sha256 — a hand
edit fails `--check` — so it can be labeled and excluded, never amended, and it is not
a candidate for the home.

The home question is settled by decision A4 of the restructuring plan: the structure
fence, because `pyproject.toml` already cites it — "Layout is fixed by
docs/tier2/coding-standards.md § Structure" — and the alternatives were a second index
(one-home violation) or inverting an existing citation. What the home question does not
settle is enforcement. A frozen fence that names 7 of 14 is not conservative, it is
stale: the seven unnamed directories include the plan mirror, the protected set and the
vault itself, so the canonical document did not name the very machinery that guards it.
The status that makes this a waiver rather than a routine edit is the document's own:
`status: frozen`, `enforcement: ci-gate`.

### Decision

**The structure fence names every top-level directory, and the vault floors it.**

1. **The seven absent lines land in the fence.** `.github/ bench/ deploy/ plan/ policy/
   tools/ vault/`, one line each, in that order; the fence now names all 14 top-level
directories, `.github` included. The ignore files are not the fence. `.gitignore` and
   `.git/info/exclude` declare machine-local and generated state; the walked tree
   subtracts exactly the literal `name/` patterns they declare, and a pattern with a
glob or a subpath in it is left in: it cannot name a top-level directory either way, and
   an undecided directory must surface, never pass silently.
2. **The vault gains a `layout` extractor** (`tools/vaultgraph/extract/layout.py`). It
   mints one LAYOUT node per fence line and holds a floor of 14: a fence that loses a
   line is under the floor and the build is not current. It also walks the top-level
directories and surfaces two anomalies — `layout-miss`, a directory that grew in and
   the fence does not yet name; and `layout-ghost`, a fence line whose directory is not
   there. The ghost is the protected set's ghost row wearing a layout hat — ADR-0031's
   `lint_run_records` line, a declared file that exists nowhere, is the same shape of
   finding: a declared thing with no referent, committed to `vault/_anomalies.md`
   rather than resolved by the generator picking a side.
3. **The README's layout block is retired to a pointer** at the fence. The README is the
   human entry; it routes, it does not restate. One home per fact.

This is a **D28 waiver** and counts toward the waiver total the operating principles use
as a health metric. It is the second. The gate is the frozen status over the coding
standards' structure fence; what it overrides is the fence's declared content — 7 of
the 14 lines, above; the reason is the drift and the enforcement gap stated in the
Context; and the condition that would reverse it is the falsification clause below,
which the waiver must state or it is a note rather than a gate.

### Falsifies if

- a top-level directory exists in the tree and neither a fence line nor a committed
  `layout-miss` anomaly accounts for it; or
- a fence line names a directory that is not there and no committed `layout-ghost`
  anomaly accounts for it; or
- the floor is lowered, or a second list of top-level directories is carried in the
  README or any register document.

### Consequence

The drift now fails in both directions instead of accumulating silently. The shrink
direction fails the floor: delete a fence line and the vault build is red, so a fence
cannot quietly lose a line the way it has lost seven. The growth direction is committed
and visible: a new top-level directory produces a `layout-miss` row in
`vault/_anomalies.md` in the same build that first sees it, a finding an operator
closes with the line, the same way the protected set's ghost row was closed. The plan
mirror's stale fourth copy is untouched: sealed files are labeled at the point of use,
not edited.

The change is seven fence lines, one extractor module with its registry entry, the
README's block becoming a pointer, and this record. The extractor sits in `tools/`,
which is agent-writable and CI-gated, not the protected set, so it is ordinary review;
the frozen document is the part this waiver exists for, and its diff is the O9 surface
of the change.

---

## ADR-0034 — The ADR number claim lint: a branch may not claim a number the base has issued

**Date:** 2026-08-21 · **Status:** Accepted · **Supersedes:** none

### Context

The register's self-hygiene item. The ADR log is append-only, and its preamble states the
numbering discipline: sequential, and never reused. Nothing had ever enforced the *claim*
half of it. A collision is discovered at merge, when two branches land on the same number,
and it is paid for by hand — a renumbering note, corrected in-repo references, and a vault
rename, per the `fa62b4b` precedent. That cost was paid twice in one week when the four ADR
branches landed under the operator's merge-order ruling: the protected-set record renumbered
0029 to 0031, its note having reasoned from main's numbering without seeing the m1 claim;
the agentdb record renumbered 0031 to 0032, pre-authorized by its own note but still a hand
edit at merge. Both renumbers were correct, and neither was caught before merge.

### Decision

**A branch may not claim a number the base has issued.** `scripts/lint_adr_numbers.py`,
run in the integrity job after the reading-map check, compares the log as the branch has
it against the log the base ref has (`origin/$GITHUB_BASE_REF` in CI, else `origin/main`,
else `main`, else `HEAD`) and reports:

- a **re-claim** — the base has issued a number and the branch carries a different record
  under it — as a failure, and a number twice in the branch log as a failure; the merge
  of two records under one number is the collision the log's discipline forbids;
- a **gap** in the branch log as a print, never a failure: a record may deliberately take
  a number it expects to lose at merge (the agentdb record took 0031 knowing 0029 was
  contested), and the vault already surfaces gaps as the declared `adr-numbering-gap`
  anomaly, which is the committed home for that fact. A gate that reds on a deliberate
  skip is a gate branches work around;
- a base that resolves to nothing, or a log that parses to no heading, as a failure: a
  claim check with nothing to check against is the vacuity class.

The comparison is over the heading and the decision text. A trailing renumbering note is
excluded from it: the note travels with the record it reconciles, and the merge that
renumbers a record is the same merge that rewrites the note, so the note cannot take part
in the comparison. The self-test plants a new number (passes), a re-claim (fails), a
deliberate skip (prints, passes), an in-branch duplicate (fails), and a heading-less log
(fails), and runs with no git repository at all, because a check whose negative control
needs a repository runs only where a repository happens to be.

The record also closes the other half of the self-hygiene item. The retired Phase 0.5 row
is out of the reading map (retired 2026-08-14, folded into 0.75 per the plan of record),
and the eight-entry manifest discipline is already on main, so those halves needed no
change beyond the generator table this lint stands beside.

### Falsifies if

- a branch lands a number the base has issued without the lint failing at the branch tip;
  or
- the lint reds on a deliberate gap, or on a record whose only difference from the base's
  copy is a renumbering note; or
- the self-test passes with any guard unwired.

### Consequence

The collision is found where the fix is still cheap: at the branch tip, a renumber with a
note per the `fa62b4b` precedent, instead of at merge, where it is a note plus corrected
in-repo references plus a vault rename. The vault keeps surfacing gaps as declared
anomalies, so a deliberate reservation stays visible without being a failure, and the
append-only log keeps its numbering discipline enforced rather than stated.

This is a `.github/` change — the protected set — and a `scripts/` addition, so the O9
line-by-line review and this record are the price, per major-fix #8.

---

## ADR-0035 — The protected set's single home names its fourth shape as a projection, not a second authority

**Date:** 2026-08-21 · **Status:** Accepted · **Supersedes:** nothing · **Amends:** the protected paths policy · **See also:** ADR-0022 (the first D28 waiver), ADR-0033 (the second), ADR-0031 (the protected set) · **D28 waiver:** yes

### Context

The protected set has four shapes: the frozen table in the policy document, the hardcoded
prefixes in the patch validator, the machine-readable `policy/protected-paths.json`, and
the `control.policy_protected_path` database table. The first three became one when
ADR-0031 landed: the JSON is the machine-readable home, the validator loads it failing
closed, and the test asserts set equality between the file and the table in both
directions. The fourth shape — the database table, whose DDL and grants landed with the
control schema — was named in the policy's provenance section as carrying the same policy
per tenant for runtime enforcement, its writer a later stage, no sync claimed.

What the single-home statement did not yet say is what the table *is* in the home
hierarchy. A table that carries the policy per tenant can read as a second authority: a
place the policy also lives, that could drift from the file and be cited as ground truth.
The read-model governance ruling (the restructuring plan's W6) requires the single-home
statement to name the fourth shape as a runtime per-tenant projection, not a second
authority, with the sync obligation attaching at its writer stage. The policy document is
`status: frozen`, `enforcement: ci-gate`; the line that completes the statement is a
change to a frozen document, which is what this waiver exists for.

### Decision

**The single-home statement names the fourth shape as a projection, not a second authority.**

The policy's provenance section gains one line: the `control.policy_protected_path` table
is a projection of the policy, not a second authority — the single home is the file. The
sync obligation stays attached to the table's writer stage, a later one; nothing in the
file claims it, and a projection cannot become a competing source of truth because the
home it projects from is the only place the policy is authored.

This is a **D28 waiver** and counts toward the waiver total the operating principles use
as a health metric. It is the **third**. The gate is the frozen status over the protected
paths policy; what it overrides is the policy's declared content — the single-home
statement, above; the reason is that the fourth shape of the protected set must be named
as a projection rather than left to read as a second authority; and the condition that
would reverse it is the falsification clause below, which the waiver must state or it is
a note rather than a gate.

### Falsifies if

- the `control.policy_protected_path` table is cited as a source of the protected set
  rather than as a projection of the file; or
- a writer for the table lands and the file is not the source it projects from; or
- a second machine-readable home for the protected set appears beside
  `policy/protected-paths.json`.

### Consequence

The four shapes are now one home with a named projection. The file is the single
machine-readable authority; the table is its per-tenant runtime projection, and the
statement says so at the point where a reader would otherwise infer a second authority.
The sync obligation stays with the writer stage, a later one, so the projection cannot be
cited as ground truth before it has a writer to be in sync with. The change is one line
in a frozen document and this record; the line is the O9 surface of the change.

---

## ADR-0036 — Run Fingerprint Record Schema & Production

**Date:** 2026-08-24 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0018, ADR-0019 (C4/C11 blocked on this record)

### Context

Containment assertions C4 (runtime image digest) and C11 (serving lane) compare live observations against a declared `RunFingerprint`. The schema exists in code (`harness/fingerprint/record.py`: 27 frozen fields across 4 groups D19/D40/lane/worker) but **no real record is produced or stored** in the repository. Both assertions currently report `NOT_EXECUTED` because there is no truth to compare against.

The `bench/` directory holds per-seed evidence but has no writer for fingerprint records. The `bench/bench_infer.py` captures a partial `Fingerprint` (model_id, server, engine, quantization, arch, context_length) for benchmark runs, but this lacks the 27 fields C4/C11 need.

### Decision

1. **Add `scripts/capture_run_fingerprint.py`** (factory-owned, single responsibility):
   - Collects all 27 `RunFingerprint` fields from live sources:
     - `orchestrator_sha` ← `git rev-parse HEAD`
     - `runtime_image_digest` ← `docker image inspect alfred-api:r1 --format '{{.RepoDigests}}'`
     - `lockfile_sha256` ← `sha256sum uv.lock`
     - Lane fields (`model_id`, `quantization`, `loaded_context_length`, `parallel_slots`) ← serving `/v1/models` + `lms version`
     - `adaptor_version` ← `harness/worker/port.py` version constant
     - Remaining fields from CI/env (`server_version`, `inference_runtime_version`, `harness_identity`, `criterion_set_version`, `quant_artifact_sha256`, `oracle_denylist_version`, `tool_description_sha256`, `seed_layer_order_sha256`)
   - Constructs `RunFingerprint` (validates all 27 fields present, no defaults)
   - Computes `fingerprint_sha256` via `acs_sha256("run_fingerprint", record.as_mapping())`
   - Writes `bench/fingerprints/<seed>.json` with structure:
   ```json
   {
     "seed": 3355,
     "record": { /* 27 fields */ },
     "fingerprint_sha256": "<ACS-1 digest>",
     "captured_at": "ISO8601",
     "source": "factory-dispatch|bench-infer|manual"
   }
   ```
2. **Add `just fingerprint` target** (or `make fingerprint`) to run the script.
3. **CI job** on every `main` push: runs capture, publishes `bench/fingerprints/*.json` as artifact (90-day retention).
4. **`bench/` stays pure evidence** — no writers in repo; this script is factory-owned, not bench-owned.

### Consequences

- C4/C11 positive controls become integration tests against truth (real record in `bench/fingerprints/`).
- Negative controls unchanged (`NOT_EXECUTED` paths still tested).
- `bench/fingerprints/` becomes immutable input to containment assertions — the measurement contract.
- No schema change to existing `bench/results/*.json` (they remain per-task evidence).

### Enforcement

- CI asserts `bench/fingerprints/` artifact exists on every `main` push.
- `policy/protected-paths.json` entry for `bench/fingerprints/` (append-only) — see ADR-0038.

---

## ADR-0037 — `arity` Semantics in Replay Harness

**Date:** 2026-08-24 · **Status:** Accepted · **Supersedes:** none

### Context

`src/replay/harness.py:94` asserts `metric.arity != len(series)` but `arity` has **no documented meaning** in the codebase. The field exists in `MetricValue` wire type (`harness/acs/acs1.py` `MetricValue` includes `arity: int`) but is never defined — is it expected series length? max depth? schema version? A metric definition cannot declare what `arity` it expects.

### Decision

**Define `arity` as: "the number of independent observations a metric aggregates."**

Examples:
- A 3-hop chain metric (TTC through 3 obstacles) → `arity = 3`
- A single-point collision check → `arity = 1`
- A derived metric combining 2 base metrics → `arity = 2`

`len(series)` is the *actual* observations collected in the replay run. Mismatch (`metric.arity != len(series)`) = data loss or injector bug — the harness should fail fast rather than compute on incomplete data.

**Implementation:**
- Update `MetricValue` docstring in `harness/acs/acs1.py` with the definition.
- Update `src/replay/harness.py:94` comment to reference the definition.
- **No wire change** — `arity` remains `int` in the ACS-1 payload.

### Consequences

- Future metrics must declare `arity` at definition (in metric catalog / criterion).
- Replay harness validates collection completeness via the mismatch check.
- Removes silent mismatch class where wrong-length series silently produced wrong results.

---

## ADR-0038 — bench Immutability: Convention → Git-Level Control

**Date:** 2026-08-24 · **Status:** Accepted · **Supersedes:** none · **See also:** Issue #4 (review output)

### Context

`bench/results/` holds per-seed evidence (immutable by convention). Currently no writer exists in the repo; CI only reads. Issue #4 asks to harden or accept the convention.

### Decision

**Harden with git-level control:**

1. Add `bench/results/` and `bench/fingerprints/` to `policy/protected-paths.json` as **append-only** prefixes (no rewrite, no delete).
2. CI step: `git diff --name-only HEAD~1 -- bench/results/ bench/fingerprints/` — fails if any file shows as modified (only `A` added status allowed).
3. No schema change — existing JSON stands; future records follow same format.

### Consequences

- Accidental overwrite caught in CI (not at audit time).
- Intentional rewrite requires ADR (raises cost, creates record).
- Evidence integrity guaranteed by the same gate that protects the vault and register.

### Enforcement

- `scripts/lint_protected_paths.py` (existing) asserts no modified files under protected prefixes.
- CI runs lint on every push.

---

## ADR-0039 — Orchestration Canvas: Protected Topology Source & Palette Binding

**Date:** 2026-08-26 · **Status:** Accepted · **Supersedes:** none · **See also:** docs/tier1/orchestration-canvas-spec.md, ADR-0031 (protected-set as policy), D51

### Context

Prototype #13 shipped palette (`policy/node-palette.json`, 21 entries, v1) and topology (`orchestration/topology.json`, 8 nodes/7 edges) with generator and lint in commit e04544a on `feat/orchestration-canvas`. Two open decisions: where to seat the canvas, and which artifacts to harden.

**Seat.** Two surfaces offered: a served page (new origin, auth, CSP, D51 split extended) and an **operator-local generated artifact** (single-file HTML, `file://` origin, no server). Served reads as the more capable surface and is the more expensive one: it reopens D51's overlay model (ADR-0008) — agent-authored fragment positioned over a verdict — and requires a second origin, credential handling, and a content policy for a file whose sole author is the operator and whose write frequency is low. Operator-local follows a proven precedent — `docs-graph.html` via `tools/vaultgraph/render/` (vanilla JS, zero deps, JSON-in-`<script type="application/json">`, `<` escaped to `\u003c`) — with no network requests, no external resources, and no new trust boundary. **Choosing served would have meant D51 touched; choosing local means it is untouched and no new attack class is introduced.** Trade-off accepted: no collaborative editing, no remote access. Correct for an artifact whose author set is exactly one human.

**Sources.** Both JSON files are hand-authored and operator-owned. Palette was already protected — `policy/` prefix in `policy/protected-paths.json` covers it — but topology was not: its directory `orchestration/` had no entry, so an agent patch could rewrite the graph that the canvas and the lint both trust. An unprotected source that two validators read without recomputing is a source nobody protects.

### Decision

1. **Protect `orchestration/topology.json` by adding `orchestration/` as a protected prefix** in `policy/protected-paths.json` (ADR-0031). Entry carries rationale referencing this ADR and version stays 1. Any diff touching `orchestration/**` is now refused by `harness/patch/validate.py` before it reaches a tree.

2. **Palette stays under `policy/` (no new prefix).** `policy/node-palette.json` was already covered; this ADR records that coverage explicitly so a future move out of `policy/` cannot be treated as uncovered without an ADR of its own.

3. **Binding lint is paired to the source.** `scripts/lint_topology.py` (TOP001–TOP009) enforces topology↔palette coherence; `tools/tests/test_orchestration.py` extends the `test_protected_binding` pattern — every code-side node-kind spelling must be bijective with a palette `id`, one spelling each, drift fails CI. The gate that refuses the edit and the lint that rejects the drift are different controls on the same invariant (no silent palette/topology divergence).

### Consequences

- Edits to topology or palette now require the protected-path gate — operator commit, ADR if intent changes. Factory agents cannot land a topology rewrite through a patch.
- `docs/tier4/protected-paths-policy.md` gains the `orchestration/` row; `harness/patch/test_protected_set.py` gains the matching `ROW_COVERAGE` entry (`orchestration/ → orchestration/`). The doc↔set equality asserted there fails on any mismatch in either direction.
- Generator (`tools/orchestration/gen_canvas.py`) remains pure — deterministic function of the two sources — so protecting the inputs protects the output without protecting the generated HTML.
- Cost: one more prefix in the gate's hot path (negligible) and one more table row. Benefit: the hand-authored graph is no longer the single place an agent can redefine what the system thinks its own orchestration is.

### Enforcement

- `harness/patch/validate.py` → `load_protected_set()` fails closed on missing/corrupt set (F25/D57).
- `harness/patch/test_protected_set.py` → set-equality in both directions (ADR-0009 precedent).
- `scripts/lint_topology.py` + `tools/tests/test_orchestration.py` → structural and binding checks, including `--self-test`.
- `tools/orchestration/gen_canvas.py --check` → generated canvas matches sources.

---

## ADR-0040 — The structure fence grows to eighteen

**Date:** 2026-08-29 · **Status:** Accepted · **Supersedes:** none · **Amends:** the structure fence of the coding standards (ADR-0033) · **See also:** ADR-0033 (the fence's first full enumeration), ADR-0039 (orchestration/ as protected prefix), ADR-0031 (protected set as single home) · **D28 waiver:** yes

### Context

ADR-0033 made the structure fence in `docs/tier2/coding-standards.md` the one home for "what top-level directories the tree has" and floored it at fourteen, with a vault `layout` extractor that surfaces `layout-miss` (directory exists, fence does not name it) and `layout-ghost` (fence names a directory that is not there). At that point the tree and the fence agreed at fourteen.

Three facts have since diverged from that agreement, two by drift and one by design.

**Drift — `orchestration/` exists and is protected but not fenced.** Commit `e04544a` (`feat/orchestration-canvas`) added `orchestration/topology.json` and ADR-0039 added `orchestration/` as a protected prefix in `policy/protected-paths.json`. The fence was not updated in either change, so every `gen_vault.py` run since has carried `layout-miss: orchestration/` in `vault/_anomalies.md` and `graph.json`. The directory is not transient — it holds the hand-authored topology source that two validators read — and the anomaly is not a discovery, it is a debt the record left open.

**Drift — `prototype/` is dead and its anomaly is the same shape in reverse.** `prototype/` was the wayfinder map #8 prototype (#13) that shipped the palette and the topology before they were promoted to `policy/` and `orchestration/`. It is not built, not imported, and not deployed. Its only live referrer is a comment in `tools/orchestration/gen_canvas.py:141` ("Reuse prototype canvas JS?"). The fence does not name it, so it also surfaces as `layout-miss: prototype/`. The intended end state is not to fence it but to remove it from the walked set (ADR-0043).

**Design — the ICM workspace adds three shelves the fence must name or it will re-break the floor the next build.** Numbered pipeline `stages/`, template shelf `_templates/`, and archive `_archive/` are top-level directories by construction: they sit beside `src/` and `docs/`, they are not subdirectories of an existing fence entry, and the layout extractor walks `ctx.root.iterdir()` minus exactly the literal `name/` patterns from `.gitignore` and `.git/info/exclude` plus `_MACHINE_LOCAL`. A directory that is not ignored and not named is a `layout-miss` by definition — the extractor has no third option and no silent pass. Landing any of the three without a fence line recreates the same anomaly this ADR is closing, one commit later.

`.autoforge/` and `.claude-flow/` are not in this count. Both are machine-local tooling state, gitignored (`.gitignore` literal `name/` patterns), and therefore subtracted before the walk. The former was added to `.gitignore` in `c699ce6` precisely so it does not count.

The home question is already settled by ADR-0033: the fence is the one home. The question this ADR answers is the new enumeration, the constant that floors it, and the ordering that keeps history legible.

### Decision

**The structure fence names eighteen top-level directories, and the vault floors at eighteen.**

1. **Four lines land in the fence in `docs/tier2/coding-standards.md § Structure`, in this order, after the existing fourteen which are left untouched:** `_archive/` — dead material that the register superseded but must keep for provenance; `_templates/` — blank templates instantiated by copy, never edited in place; `orchestration/` — protected topology source (ADR-0039), already on disk; `stages/` — numbered pipeline `01_s0` … `10_s9` (ADR-0041). The fourteen existing lines keep their order; the four new lines are appended as a contiguous block. No line is reordered, no description is rewritten. A fence whose history is a pure append is a fence whose diff is reviewable without reconstructing a sort.

2. **`tools/vaultgraph/extract/layout.py:31` `EXPECTED = 14` becomes `18`, and the comment "Fourteen on the restructured tree" becomes "Eighteen on the ICM workspace (fence v2, ADR-0040)".** The floor and the fence move together in the same commit; a floor that moves without its fence, or a fence that moves without its floor, is the drift this mechanism exists to catch. `_MACHINE_LOCAL` is not changed — it continues to hold only `.git` and `.claude`; `.autoforge` and `.claude-flow` remain ignored via `.gitignore`, which is the correct layer for tooling state.

3. **No other top-level list is carried.** The plan mirror's "Files and structure" block inside `plan/` is sealed by `plan/manifest.json:8` sha256 and is labeled and excluded, never amended (ADR-0033). CI workflows (`.github/workflows/gates.yml`, `fingerprint.yml`) name only existing subtrees (`harness/*`, `bench/*`, `scripts/*`, `tools/*`, `tests/`) and carry no top-level directory list. Any future list of top-level directories outside the fence is a defect, not a second home.

This is a **D28 waiver** and counts toward the waiver total the operating principles use as a health metric. It is the third. The gate is the frozen status over the coding standards' structure fence; what it overrides is the fence's declared content — four of the eighteen lines; the reason is the drift and the workspace design stated in the Context; and the condition that would reverse it is the falsification clause below.

### Falsifies if

 - a top-level directory exists in the tree and neither a fence line nor a committed `layout-miss` anomaly accounts for it; or
 - a fence line names a directory that is not there and no committed `layout-ghost` anomaly accounts for it; or
 - the floor is lowered, or a second list of top-level directories is carried in the README or any register document.

### Consequence

The two committed `layout-miss` anomalies (`orchestration/`, `prototype/`) stop being anomalies for different reasons in the same build: `orchestration/` because the fence now names it; `prototype/` because ADR-0043 moves it under `_archive/` and the fence names `_archive/` instead. `stages/` and `_templates/` land fenced from their first commit and never surface. A new top-level directory added without a fence line again fails in both directions — the shrink direction fails the floor, the growth direction commits a visible `layout-miss` — rather than accumulating silently.

### Enforcement

 - `tools/vaultgraph/extract/layout.py` → floor 18, walk minus ignored, `layout-miss`/`layout-ghost` anomalies.
 - `vault/_anomalies.md` + `graph.json` + `docs-graph.html` → byte-compared in CI (`gen_vault.py --check` in `gates.yml:192-193`); a hand edit fails the check.
 - `docs/tier2/coding-standards.md` → frozen, `ci-gate`; this ADR is the waiver that authorizes its diff.

---

## ADR-0041 — The S0–S9 build materialized as a numbered pipeline

**Date:** 2026-08-29 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier2/execution-order.md` § Stages and § What must not be built yet (graph-editor line) · **See also:** ADR-0039 (topology canvas as protected source), ADR-0040 (fence v2, `stages/`), docs/tier2/stage-gate-definitions.md

### Context

`docs/tier2/execution-order.md` orders what gets built by what it unblocks. Its central fact is the stage sequence S0 (backlog) through S9 (Phase 1 build), with S0–S4 and S8 marked **DONE** (2026-08-17/18), S5 in progress, S6/S7 probes done with enforcement outstanding, and four operator items blocking S9. That order is the project's spine: every gate, every waiver, and every "blocks" edge in the vault stages extractor reads it.

What the spine does not have is a place. Stages are declared in one document and realized — when they are realized — in whatever directory their output happens to land (`harness/`, `src/`, `deploy/`, …). There is no folder a newcomer can open to learn whether S3 is done, what it produced, or what residue it left; no folder an agent can write that is unambiguously *the work of S5* rather than a file in `src/` that happens to have been written during S5. A build whose order exists only as prose is a build whose order an agent reconstructs from prose, and that reconstruction is where sequence errors enter.

ICM invariant 3 makes the missing shape explicit: *numbered pipeline* — one folder per stage, in build order, each with an explicit contract (inputs, process, outputs, one human check). The workshop's number is not a second numbering: `NN` is build order and `sN` is the stage id the register and the vault already use. Both travel in the directory name so a filesystem listing and the register agree without a lookup table.

Two related ambiguities must be settled in the same decision or they will be settled by assumption.

**Where stage status lives.** The naïve answer is a status file in each stage folder. That duplicates a truth the register already owns: `execution-order.md` declares each stage DONE/provisional/blocked, and `harness/selftest/stage_gate_register.json` records each gate. A second status that can disagree with the first is a second source of truth, and a vault that reads both must pick a side or surface a disagreement that a writer should never have created. Status belongs in one place; evidence that the status is honest belongs in another.

**What "No graph editor" forbids.** `execution-order.md` § What must not be built yet carries: "No graph editor. The graph definition declares field ownership and verdict-node placement, so a GUI writing it is a second authoring path around the D16/D39 lint." Prototype #13 shipped `orchestration-canvas.html` — a single-file HTML page that edits `orchestration/topology.json` (8 nodes / 7 edges, palette-bound). Taken literally, the prohibition and the canvas contradict: the canvas is a graph editor. The contradiction is terminological, not substantive. The state graph (`docs/tier1/state-and-graph-specification.md`, `harness/` graph definition) declares field ownership and verdict placement and is guarded by `scripts/lint_verdict_boundary.py` (D16/D39). The orchestration graph (`orchestration/topology.json`, `policy/node-palette.json`) declares which roles exist and how they hand off, guarded by `scripts/lint_topology.py` and `tools/tests/test_orchestration.py` (ADR-0039). One forbids a GUI writing the state graph; the other authorizes a local page editing the topology source. The line must be scoped or the canvas must be removed — and the canvas is the operator's chosen surface for an artifact whose author set is one human.

### Decision

**Stages S0–S9 are materialized as `stages/01_s0_backlog` … `10_s9_phase1`, with a single evidence record per stage and a scoped prohibition on the graph editor.**

1. **Folders.** `stages/` (fenced by ADR-0040) holds ten directories, lexically sorted equals build order:
   `01_s0_backlog`, `02_s1_db-foundation`, `03_s2_oracle-env`, `04_s3_inspector-core`, `05_s4_suites-together`, `06_s5_product-path`, `07_s6_containment`, `08_s7_durability`, `09_s8_deploy-rollback`, `10_s9_phase1-build`.
   `NN` is zero-padded build order; `sN` is the stage id from `execution-order.md` and the vault `stage` nodes; slug is the stage's short name from the same document. The register's S-ids do not change; the filesystem carries them.

2. **Per-stage contract and evidence.** Each `stages/NN_sN_slug/` holds `CONTEXT.md` (the stage's working contract — one job, Inputs with exact paths, Process as numbered steps, Outputs, exactly one human check; instantiated from `_templates/stage-contract.md` per ADR-0043), an `input/` directory (empty unless the stage stages material), and `output/exit.md` (the stage's evidence record). `output/exit.md` is the *only* stage-scoped evidence: what was done, the commit that landed it, the ADRs it produced or amended, the register-entry pointer where the fact now lives, and the residue it left. Agent-drafted as a claim; the human confirms at the stage gate; real outputs stay in canonical homes (`src/`, `harness/`, `docs/`, `bench/`) and the exit record points, never copies. No other status file is carried in the folder.

3. **Where status lives and how it is checked.** Status is `execution-order.md` § Stages — the line that says **DONE**, **PROBES DONE**, or **blocked by** — and nowhere else. The vault `stages` extractor (extended by ADR-0042) cross-checks each DONE declaration against `stages/NN_sN_slug/output/exit.md` and the register entry the exit record points to; a DONE stage without an exit record, or an exit record whose commit/ADR/register pointer does not resolve, surfaces as an anomaly. The exit record is evidence, not a second status; a mismatch fails the vault rather than creating a disagreement between two files an operator must reconcile by hand.

4. **Backfill.** All completed stages (S0–S4, S8) are backfilled with a one-paragraph `output/exit.md` citing the commit, ADR, and register entry from `git log` and the vault at the time of landing. No gate is re-run — a gate is a point-in-time check and re-running it rewrites history. S5 (in progress, "Product path to a reproduced number") gets an empty `output/` with a `README.md` stating it is in progress and naming its unblockers. S6/S7 keep their "probes done, enforcement outstanding" shape; their exit records record that shape and its residue. The walk test (ADR gate) is the check that the backfill is honest: a cold agent derives stage status by scanning `stages/` and `execution-order.md` and the two agree.

5. **Scoped prohibition.** `execution-order.md` § What must not be built yet, line "No graph editor. The graph definition declares field ownership and verdict-node placement, so a GUI writing it is a second authoring path around the D16/D39 lint." is amended to: "No **state-graph** editor. The state graph (`docs/tier1/state-and-graph-specification.md` and the `harness/` graph definition) declares field ownership and verdict-node placement; a GUI writing it is a second authoring path around the D16/D39 lint and is forbidden. The **orchestration canvas** (`orchestration/topology.json` via `tools/orchestration/gen_canvas.py`, ADR-0039) is a topology editor over a different artifact (`policy/node-palette.json` + `orchestration/topology.json`), protected and lint-bound, and is not in scope of this line." The canvas is not an exception; it is a different graph.

### Consequences

 - A newcomer learns stage order by listing `stages/` and learns stage state by reading `execution-order.md`; the two agree by construction and a third read (`output/exit.md`) tells what the stage actually left behind. The 2k–8k token band the walk test measures is entry (`CLAUDE.md`) + one stage contract (`stages/NN_sN_slug/CONTEXT.md`) + its inputs.
 - `execution-order.md` remains the one home for order and status; `stages/*/output/exit.md` is the one home for stage evidence; the vault is the one home for the cross-check. No second status file can drift from the first because no second status file exists.
 - The "No graph editor" line no longer contradicts the shipped canvas. The state graph remains without a GUI authoring path; the topology graph remains editable through the single-file local page the operator chose. A future GUI for `state-and-graph-specification.md` is still forbidden and the lint still guards it.

### Enforcement

 - `docs/tier2/execution-order.md` → provisional, `review-cadence`; this ADR is the amendment that authorizes its diff (no D28 waiver — the document is not frozen).
 - `tools/vaultgraph/extract/stages.py` (ADR-0042) → reads `execution-order.md` § Stages and `stages/*/output/exit.md`; DONE without evidence or evidence without DONE surfaces as an anomaly.
 - `scripts/lint_verdict_boundary.py` → D16/D39 still guards the state graph; the topology canvas remains guarded by `scripts/lint_topology.py` + `tools/tests/test_orchestration.py` (ADR-0039).

---

## ADR-0042 — The vault gains verbs and effects

**Date:** 2026-08-29 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0041 (stages pipeline, `stages/`), tools/vaultgraph/README.md (vault vocabulary), `docs/README.md` (register as document catalog)

### Context

The vault is the single generated system map the register is read through. It currently answers noun questions well — what documents exist, what decisions were made, what stages block what, what modules depend on what, what the layout floor is — because its node kinds name nouns: DOCUMENT, ADR, STAGE, OPERATOR_ITEM, RISK, MODULE, SCHEMA, GATE, LAYOUT, and its edges name the relations between them.

Two noun-adjacent questions it does not answer, and both are asked at the point of change rather than at the point of reading:

**"What process do I run to change this, and where does it live?"** Vault regen, gate run (`gates.yml`'s five jobs), dispatch (`harness/worker/` + `harness/patch/validate.py`), bench run, canvas generation (`tools/orchestration/gen_canvas.py`), fingerprint capture (`scripts/capture_run_fingerprint.py`), doc generation (`scripts/gen_reading_map.py`) — these are the verbs the repository actually runs, and they live in `scripts/`, `harness/`, `.github/workflows/`, `justfile`, and the README Checks code block. Today they are not nodes. A map that names every document but not the process that regenerates it is a map that cannot answer "what do I run after I edit this."

**"If I change X, what cards should I open?"** The vault already computes in-edges per node, but it renders them only as backlinks on each note. There is no index that inverts the question — no board that says "change `policy/protected-paths.json` → open the protected-paths doc, the D20 lint, the patch validator, the vault code extractor, and the gates job that runs it." That index is derivable from the graph the vault already builds; it is not a new extraction so much as a rendering of an existing relation. Carrying it as a hand-authored `map/` shelf would be a second map that can disagree with the first.

A third, smaller gap is stage-aware: once `stages/` exists (ADR-0041), the stages extractor must read it. Today it reads only `docs/tier2/execution-order.md`; after the pipeline lands it must also read `stages/*/output/exit.md` for the DONE-vs-evidence cross-check, or the pipeline and the register will be two lists that agree only because nothing checks whether they do.

The user's decision, recorded in grilling, is one generated map layer, no hand-authored `map/` shelf.

### Decision

**The vault gains two node kinds — PROCESS and EFFECT — and the stages extractor reads `stages/`.**

1. **`NodeKind.PROCESS` → `vault/processes/`.** One node per verb the repository actually runs: vault regeneration (`python3 tools/gen_vault.py` / `--check` / `--self-test`), gate run (the five `gates.yml` jobs and `fingerprint.yml`), dispatch (worker port + patch validation), bench run, canvas generation, fingerprint capture, doc generation, reading-map generation. Extracted from `scripts/*.py`, `harness/**/*.py`, `.github/workflows/*.yml`, `justfile`, and the README Checks block, with `path:line` citations on every node (the provenance a walk test reads to find the runnable). A process node names its inputs (the trees it reads), its outputs (what it writes or gates), and the command that runs it. Source authority per verb — which file is the home for which process — is recorded on the node; the detailed per-verb authority table graduates as `stages/10_s9_phase1` is worked (the Not yet specified item from the grilling), and until then the extractor's `TREES`/`FLAT_TREES`/`WATCHED_TREES` constants are the authority.

2. **`NodeKind.EFFECT` → `vault/effects/` (also rendered as a board).** The change-impact index — "if you change X, open these cards" — derived from the vault's own in-edges, not from a new extraction. For each node, its EFFECT board lists the nodes that point at it, grouped by kind and rendered with the `path:line` of the edge's source. A hand-authored `map/` shelf is not created; the board is a view over the graph, recomputed on every `gen_vault.py` run, so it cannot disagree with the graph it inverts.

3. **`FOLDERS` += the two kinds.** `tools/vaultgraph/render/vault.py:23` `FOLDERS` gains `NodeKind.PROCESS: "processes"` and `NodeKind.EFFECT: "effects"` (the EFFECT board is also rendered via `render/dataview.py` + `render/canvas.py` as a board, not just as notes; the folder holds the per-node effect cards). No existing folder mapping changes.

4. **Stage extractor reads `stages/`.** `tools/vaultgraph/extract/stages.py` gains a walk over `stages/*/output/exit.md` (ADR-0041). For each `execution-order.md` § Stages row marked DONE, it expects an exit record; for each exit record it resolves the cited commit, ADR, and register entry; mismatch in either direction — DONE without evidence, evidence without DONE, or evidence pointing at a non-existent commit/ADR/register entry — surfaces as an anomaly (`stage-evidence-miss` / `stage-evidence-orphan`). The floors remain as today (`min_nodes = EXPECTED` stages) plus the new kinds' floors.

### Consequences

 - The vault answers the verb question from the same place it answers the noun question. "What do I run after I edit `docs/tier2/coding-standards.md`?" resolves to the PROCESS node whose inputs include `docs/` and whose outputs include the layout floor — `gen_vault.py` and the doc lint — with the exact command on the card.
 - The change-impact question is answered without a second map. A hand-authored `map/` would have to be kept in sync with the vault; a board derived from in-edges cannot drift because there is nothing to drift from.
 - Stage status remains in one place (`execution-order.md`); stage evidence remains in one place (`stages/*/output/exit.md`); the vault is the cross-check that the two agree. The pipeline cannot quietly add a DONE stage without evidence, nor leave evidence for a stage the register does not claim is done.

### Enforcement

 - `tools/vaultgraph/model.py` → new `NodeKind` members `PROCESS`, `EFFECT`.
 - `tools/vaultgraph/extract/process.py` (new) + `tools/vaultgraph/extract/effect.py` (new, or board-only in `render/`) → PROCESS nodes from the verb sources, EFFECT boards from in-edges.
 - `tools/vaultgraph/render/vault.py` → `FOLDERS` extended; `gen_vault.py --self-test` asserts the new extractors' floors and that `render/` does not import `extract/`.
 - `tools/vaultgraph/extract/stages.py` → reads `stages/*/output/exit.md` in addition to `execution-order.md`.
 - `vault/` + `graph.json` + `docs-graph.html` → byte-compared in CI (`gen_vault.py --check`).

---

## ADR-0043 — Dead material archived and templates shelved

**Date:** 2026-08-29 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0040 (fence v2, `_archive/` + `_templates/`), ADR-0041 (stage contracts from templates), Issue #1 (O9 review; the root files are its provenance until O9 completes)

### Context

Two shelves are missing and one shelf is dead.

**Dead shelf — `prototype/`** is the wayfinder map #8 prototype that shipped `orchestration-canvas.html` and `sample-topology.json` before they were promoted to `orchestration/topology.json` and `policy/node-palette.json`. It is not imported, not deployed, and not the home for any fact the register names. Its only live referrer is a comment in `tools/orchestration/gen_canvas.py:141`. Its generated anomaly (`layout-miss: prototype/`) is not a finding to keep — it is a directory that should not be in the walked set at all. The correct end state is not to fence it but to move it out of the walk.

**Dead files — `PLAN-M1.md`, `PLAN-M2.md`, `CLASSIFICATION-M1.md`** sit at the repo root, outside `docs/` and outside any fence entry. `PLAN-M1.md` and `PLAN-M2.md` are the M1 plan (MUSE.md-sourced rule tightening, widened to `ruff` plus `pyright`); `CLASSIFICATION-M1.md` is the full harness classification the stage gate and `scripts/lint_harness_gate.py:74` cite. The latter two are referenced: `docs/tier1/adr-log.md:3017` (ADR-0029: "The full classification is `CLASSIFICATION-M1.md`.") and `scripts/lint_harness_gate.py:74` (`… See CLASSIFICATION-M1.md.`). The plan files are also the provenance for issue #1 (O9 line-by-line review of inspector patches — the operator item that says "if any fix would change…" and the review the plan records as owed). While #1 is open, the files are live provenance even though they are dead product. The move must happen after O9 completes or carry O9's sign-off in the same change — otherwise the review's source is moved before the review is done.

**Missing shelf — `_templates/`** — ICM invariant 10 is *instantiate-by-copy*: a new task, ADR, criterion, or stage contract is created by copying a blank template named for what it produces, not by recalling a shape from an old file. Today there is no shelf. Agents copy the last ADR's heading and inherit its `See also` by accident; criteria are written against no template at all.

A move without a discipline is a move that breaks sibling-path references, case-folded destinations on macOS, and the walk test's "every pre-move reference still resolves" check. The apparent cheapness of `git mv` is why the reference-integrity survey (Issue #28 / T1) exists before this ADR lands.

### Decision

**Dead material moves to `_archive/` by copy-verify-remove; blank templates land in `_templates/` by copy.**

1. **`prototype/` → `_archive/prototype/`.** Copy-verify-remove: `cp -R prototype _archive/prototype`, verify file count and content hash parity (every file identical, no file left behind), then `rm -rf prototype`. In the same commit, update the one live referrer — the comment in `tools/orchestration/gen_canvas.py:141` — to point at `_archive/prototype/` (or remove the speculative "reuse" note if the decision is not to reuse). The fence does not gain a `prototype/` line; it gains `_archive/` (ADR-0040), and `_archive/prototype/` is not a top-level directory so it does not participate in the layout walk.

2. **`PLAN-M1.md`, `PLAN-M2.md`, `CLASSIFICATION-M1.md` → `_archive/`.** Same discipline, same commit, after O9 (issue #1) completes — or, if O9 and this move land together, with O9's sign-off as the gate for the same change. Verify parity, then remove from root. Update every referrer in the same change:
   - `docs/tier1/adr-log.md:3017` → `_archive/CLASSIFICATION-M1.md`
   - `scripts/lint_harness_gate.py:74` → `_archive/CLASSIFICATION-M1.md`
   `CLASSIFICATION-M1.md:8,171` references `PLAN-M1.md` (outbound from a mover); both files move together so the relative pairing survives, but the root-relative spelling goes stale — update to `_archive/PLAN-M1.md` inside the archived copy. `PLAN-M2.md` has no inbound referrers (T1 finding) and needs no referrer update.

   Before any copy, check for case-folded collisions on the destination: `_archive/` is new, but a file named `plan-m1.md` or `classification-m1.md` differing only in case would be the same file on macOS and two files on Linux. The check is `python3 -c "assert len({p.casefold() for p in dests}) == len(dests)"` over the destination basenames.

3. **`_templates/` shelf.** Five blank templates, each named for what it produces and each carrying a one-line purpose and a `path:line` example:
   - `_templates/task-spec.md` — the task specification shape (from `docs/tier2/task-specification-standard.md`).
   - `_templates/adr.md` — the ADR shape (Context / Decision / Consequences / Enforcement / Falsifies if), with the `Date · Status · Supersedes · See also · D28 waiver` header.
   - `_templates/criterion.md` — visible/held-out criterion shape (interface signature + threshold provenance, per cross-stage-invariants).
   - `_templates/stage-contract.md` — the per-stage `CONTEXT.md` shape (one job, Inputs with exact paths, Process as numbered steps, Outputs, exactly one human check) that `stages/*/CONTEXT.md` instantiates (ADR-0041).
   - `_templates/run-fingerprint.md` — the Run Fingerprint record shape (27 fields, hash derived via ACS-1, groups D19/D40/lane/worker, per `CONTEXT.md` Core Terms).
   Templates are instantiated by copy, never edited in place; a template edited in place is a second home for the shape it defines.

4. **Fence and ignore.** `_archive/` and `_templates/` are fenced by ADR-0040 and therefore not ignored. No new `.gitignore` line is added for them. `_archive/` is ordinary history, not a second protected set — it is not added to `policy/protected-paths.json`.

### Consequences

 - The walked set loses `prototype/` and gains `_archive/` and `_templates/`; the fence gains the same, so no new `layout-miss` or `layout-ghost` surfaces. The `prototype/` anomaly is closed by the move, not by a fence line that would have enshrined a dead shelf.
 - Dead material remains reachable at a stable archived path, case-fold safe, with every in-repo referrer updated in the same commit. An external consumer (other repo, agent config, Obsidian vault) pointing at `prototype/` or a root file is the human-gate question at PR review — the in-repo survey (T1) is not an unbounded grep of other systems, and the review is where the operator answers it.
 - New work starts from a blank template named for its product rather than from the last file of that kind, which is how accidental `See also` edges and stale headers enter the vault.

### Enforcement

 - Move discipline: copy, verify count + hash, remove, update referrers, check case-fold — all in one commit. A move that leaves the source behind or updates a referrer in a follow-up is a move that broke the walk test for one commit and relied on a second commit to repair it.
 - `docs/tier2/coding-standards.md` § Structure (fence v2) → `_archive/` and `_templates/` are fence lines; the walk test asserts every pre-move reference still resolves after the move.
 - `_templates/*.md` → not generated, not gated, but instantiated by copy; a template edited in place rather than copied is a drift the vault cannot see and review must catch.

---

## ADR-0044 — Register drift reconciled

**Date:** 2026-08-29 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0018 (executor source read, Discharges O5), docs/tier0/risk-register.md, docs/tier2/execution-order.md § Operator-owned, tools/vaultgraph/extract/stages.py, tools/vaultgraph/extract/charter.py

### Context

Three finding kinds committed in `vault/_anomalies.md` on `main` were not discoveries about the domain — they were the register disagreeing with itself, and the vault faithfully reporting the disagreement rather than picking a side.

**1. Risk register out of numeric order.** `docs/tier0/risk-register.md` listed R12 before R11 — a transposition in a table whose ids are the stable handles every other document cites. The register is `status: provisional`, `enforcement: review-cadence`, `owner: human` (Tier 0), so its content is under Gate D when it touches protected premises, and this fix does: the diff reorders two adjacent blocks (R11: `commonroad-reach compiles Cython at import time`; R12: `polygon3 is sdist-only and needs a compiler`) with no text change to either. The anomaly kind was `risk-register-order`; the detail named the two rows.

**2. Operator-item count: 8 found, 9 declared.** `docs/tier2/execution-order.md` § Operator-owned, non-delegable declares nine items O1–O9. The vault `stages` extractor walks that table and mints one `operator-item` node per data row; it found eight. The ninth row exists but is struck through: `| ~~O5~~ | ~~Read OpenHands at the pinned SHA~~ | — | **DONE 2026-08-18.** ADR-0018. … |`. The extractor's row pattern `^\|\s*(O\d)\s*\|` does not match `~~O5~~`, so the row was invisible and the floor failed. The defect is not in the document — the strikethrough is the correct way to mark a discharged item done — it is in the extractor, which had no rule for a discharged row.

**3. Discharge target absent: ADR-0018 Discharges O5.** ADR-0018's `Discharges: O5` edge points at `operator-item:O5`. The node did not exist (see 2), so the edge was unresolvable and the vault surfaced `discharge-target-absent`. The ADR's history must not be edited after publication (`adr-log.md` preamble: "An ADR is edited after publication rather than superseded" falsifies the log). The fix cannot be to edit ADR-0018's `Discharges` line, nor to remove the strikethrough from the execution order to make the row match.

All three are register drift — a document, an extractor, and an ADR that should agree and do not. The vault's job is to surface the drift, not to resolve it by preferring one source over the others.

### Decision

**The drift is reconciled at source, in one commit, without editing ADR history.**

1. **Risk register reordered — `docs/tier0/risk-register.md`.** Swap the two adjacent blocks so the ids run strictly R1–R12 in numeric order, R11 before R12. No text inside either block changes; the ids, bodies, and line counts are preserved. This is the tier0 touch of this effort and the Gate D surface: the diff is two blocks swapped and nothing else, and it is staged but not merged until the operator confirms line-by-line that the reorder is exact and no wording changed. The Gate is satisfied in this ADR's review, not in a later one.

2. **Stages extractor reads the struck-through row — `tools/vaultgraph/extract/stages.py`.** Import `strip_strikethrough` from `tools/vaultgraph/mdscan.py`, change the row pattern to `^\|\s*~{0,2}(O\d)~{0,2}\s*\|`, and mint the node with `status="discharged" if withdrawn else "open"`. `~~O5~~` is now a node (status discharged), the operator count sees nine of nine, and the DISCHARGES edge resolves. No document is rewritten to make the extractor pass; the extractor is taught to read the document as it is written.

3. **Charter extractor docstring corrected — `tools/vaultgraph/extract/charter.py`.** The module docstring's ordering example is updated from the stale order to the numeric order, so the docstring no longer describes a different order than the file it documents. No logic change.

4. **Machine-local `.autoforge/` gitignored — `.gitignore`.** `.autoforge/` (ephemeral agent tooling state, created externally 2026-08-29) added as a literal `name/` pattern beside `.claude-flow/`, so the layout extractor's `_ignored_dirs` subtracts it. It is not a project directory and is not fenced. This was not one of the three committed anomalies but a fourth `layout-miss` that appeared on the same walk; handling it in the same commit keeps the vault wave atomic.

Regenerated: 535 nodes, 970 edges, 541 notes (17 changed) in `c699ce6`. The three committed anomalies no longer surface; the two `layout-miss` that remain (`orchestration/`, `prototype/`) are by design and resolve with ADR-0040/0043. Final regeneration after those lands → 0 anomalies and `gen_vault.py --check` clean.

### Consequences

 - The risk register is numerically ordered and the vault's `risk-register-order` check passes without special-casing. A future transposition again surfaces as an anomaly rather than being tolerated by a looser check.
 - Operator items are nine of nine, with O5 carried as a discharged node. ADR-0018's `Discharges: O5` resolves, and the vault renders O5 as discharged rather than absent — the register's strikethrough and the graph's status agree.
 - ADR history is untouched. An ADR that turns out to point at a discharged item is not edited; the extractor is taught to read the discharged form. The log's "never edited after publication" invariant holds.

### Enforcement

 - `tools/vaultgraph/extract/stages.py` → struck-through row pattern + `status="discharged"`; unit coverage via the extractor's own tests and the committed vault's 9-found/9-declared.
 - `tools/vaultgraph/extract/charter.py` → docstring matches the file's numeric order.
 - `docs/tier0/risk-register.md` → provisional, `review-cadence`; this ADR is the Gate D record for the reorder — the diff is staged, reviewed line-by-line, and merged only on confirmation.
 - `vault/_anomalies.md` + `graph.json` + `docs-graph.html` → byte-compared in CI (`gen_vault.py --check`); the three drift anomalies no longer appear.


## ADR-0045 — The ECC coupling is factory scope, ring-fenced, and overrides no gate

**Date:** 2026-09-02 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0022 (the first D28 waiver, and the narrowing this effort does *not* repeat), ADR-0018 (Discharges O5 — the discharge shape this record follows), `docs/tier2/execution-order.md` § Operator-owned · **D28 waiver:** no

### Context

Alfred is being coupled with Everything Claude Code (ECC 2.2.1, commit `ca185ef`). The
effort is charted as [wayfinder:map — Alfred × ECC: one factory](https://github.com/Akamel01/Alfred/issues/41).
Its destination is one unified multi-agent framework — one palette, one task contract, one
state-authority map, one model policy — with Mission Control built over it.

That work targets the **factory**, not the AV product. It advances neither Phase 0 exit nor
the AV wedge, and the four empty product directories (`src/ingest`, `src/replay`, `src/api`,
`src/thresholds`) stay empty. Recording that plainly is the reason this ADR exists.

**The claim this record was opened to make was wrong, and correcting it is most of its
value.** The map's charting asserted the effort "needs a D28 waiver the way ADR-0022
narrowed Phase 0." It does not. A D28 waiver **overrides a gate**, and every prior one
names the gate it overrode: ADR-0022 the Phase 0 exit criteria; ADR-0033 and ADR-0040 the
frozen status of the coding standards' structure fence; ADR-0035 the protected paths
policy. This effort overrides nothing. It changes no exit criterion, freezes nothing,
lowers no bar, and edits no frozen document. O1 is a gate that *sizes S9 work packets*; it
is not a gate forbidding factory work, and no such gate exists.

Operating principle 9 makes overriding a gate "expensive and permanent," and the waiver
count is a health metric the operating principles read. Spending a waiver where nothing is
overridden inflates that metric and cheapens the instrument. So this record carries
`D28 waiver: no` deliberately, and states the reason, because a reader who sees a scope ADR
without a waiver should be able to tell that the absence was reasoned rather than forgotten.

What the effort does consume is human attention, and that is the scarce resource: O1 fixes
`F = 1200 min/week` against `n = 5 merged/day`. **There is no instrument to measure the
consumption.** `docs/tier1/mission-control-specification.md` specifies per-review timing and
names the failure directly — review time recorded by the person being measured "is worse
than absent, because it looks like data" — and the surface that would record it does not
exist as code. Any minutes figure asserted here would be a guess wearing a number's
clothes.

### Decision

**Factory scope is recorded, the effort is ring-fenced rather than costed, and no gate is
waived.**

1. **Scope.** The ECC coupling is factory work. It does not advance Phase 0 exit, the four
   dated operator items, or the AV product path, and it is not to be counted as though it
   did. The counter-argument is recorded rather than assumed away: the factory is what
   builds the product, the product path is four empty directories, and a factory that
   cannot reliably run multi-agent work will not fill them faster by being ignored.

2. **A ring-fenced budget, not an estimated cost.** The effort may consume up to
   **300 min/week of O1's `F = 1200`** — one quarter. A budget is a decision the operator
   can make and enforce today; a cost is a measurement nothing can currently take. This
   mirrors the plan of record's treatment of BD, which is ring-fenced weekly hours from
   Phase 0 for the same reason: so it cannot lose every prioritization contest to
   engineering.

   The derivation of the discarded estimate is kept so a later reader can recompute it
   against a real instrument: as of this record the effort had consumed roughly ten human
   turns; at a plausible 5–10 minutes of attention per turn that is 50–100 minutes for the
   map plus two resolved decision tickets. That is an inference from message count, **not a
   measurement**, and it is recorded as a footnote rather than a finding.

3. **The stop condition.** Human minutes per task do not fall across the first **ten** tasks
   dispatched through the seven-phase lifecycle (ADR pending; decided in
   [ticket #42](https://github.com/Akamel01/Alfred/issues/42)) → the effort stops and the
   coupling is re-argued. Ten is small enough to fail fast and is the first point at which
   the number O1 already cares about could move. A merge-rate-based criterion was rejected
   because the factory does not yet produce merge-rate data.

4. **The kill criterion does not enter Tier 0.** `docs/tier0/charter-and-non-goals.md` is
   protected and carries **company-level** kill criteria. This is an internal factory-effort
   stop condition. Putting it in Tier 0 would spend a Gate D line-by-line review on scoping
   an internal effort, and would mix two kinds of criterion in one home.

5. **No protected path is touched and no Gate D applies.** `docs/tier1/adr-log.md` and
   `docs/tier2/execution-order.md` are both outside `policy/protected-paths.json`'s prefixes.
   Checked, not assumed.

### Consequences

- A reader can tell what this effort is and is not paying for. "Factory work" is on the
  record with its budget, its stop condition, and the counter-argument that was weighed.
- The waiver count is not inflated. ADR-0045 is the first ADR to carry `D28 waiver: no`
  with a stated reason, which makes the absence legible rather than ambiguous.
- The 300 min/week ring-fence is enforceable by the operator without any instrument, and
  becomes measurable the moment the Mission Control review-timing instrument exists.
- If the coupling is later observed to advance Phase 0 exit or the product path, the scope
  classification in item 1 was wrong and this record is falsified — see below.

### Falsifies if

Factory-scope work under this effort is observed to block a dated operator item (O1–O9) —
meaning a gate *was* overridden, the `D28 waiver: no` in this record's header was wrong,
and the decision should have carried a waiver.

### Enforcement

`none`. This is a scope and budget decision owned by the operator; nothing in CI can check
whether an effort is factory work or whether 300 min/week was respected. The instrument that
would make item 2 measurable is `task_end.human_review_ms`, specified in
`docs/tier1/mission-control-specification.md` and not yet built — tracked as
[Mission Control read model](https://github.com/Akamel01/Alfred/issues/52). Stating `none`
here is the honest label under the documentation standard's rule that a document with no
mechanism must be small and human-owned.

---

## ADR-0046 — Registry additions to the register generators are inspector patches, and carry this ADR

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** nothing; this record supplies an obligation that was owed and initially misread · **See also:** ADR-0031 (the machine-readable protected set), D20, `docs/tier4/protected-paths-policy.md` § *The inspector stays small*, ADR-0045 (the effort this work belongs to) · **D28 waiver:** no

### Context

The wayfinder map #41 effort produced eight research and decision documents. The register
refuses documents it does not know about: `scripts/lint_docs.py --check` asserts that
`gen_doc_stubs.py`'s `REGISTER` and `NOT_GENERATED` together account for every document on
disk, in both directions, and `scripts/gen_reading_map.py --check` fails when a document has
no reading-map entry. Both failed. The documents could not land without registry entries in
two files under `scripts/`.

`scripts/` is protected in full — *"Register lints and generators — inspector machinery
(D20) … A validator an agent may edit validates nothing."*

**A correction is the reason this record exists.** The first Gate D request for this work
(commit `557c0b3`) argued no ADR was required, on the reading that the mandatory-ADR rule in
ADR-0031 attaches to changing `policy/protected-paths.json` — the definition of what is
protected — rather than to writing to a protected path. The operator approved on that basis.

That reading is wrong. `docs/tier4/protected-paths-policy.md` states the rule directly and
without that distinction:

> Agent-drafted inspector patches are permitted only under line-by-line human review with a
> **mandatory ADR**.

A registry addition inside a generator is a patch to inspector machinery. The obligation was
owed at `557c0b3` and is discharged here, covering that commit and the same-shaped additions
that follow it in this effort.

### Decision

1. **Registry additions to `scripts/gen_doc_stubs.py` and `scripts/gen_reading_map.py` made
   by the map #41 effort are agent-drafted inspector patches.** They require line-by-line
   human review and are covered by this ADR. No further ADR is required per document
   registered under this effort; the class is decided once, here.

2. **The permitted change is data only.** An entry added to `NOT_GENERATED`, or a row added
   to a `PHASES` section. No control flow, no predicate, no threshold, no exclusion applied
   to a check. A diff under this ADR that adds or removes a `def`, `if`, `return`, `for`,
   `while` or `assert` line is outside it and needs its own record.

3. **`NOT_GENERATED` membership exempts a document from generation, never from validation.**
   This was verified rather than assumed: a frontmatter key was deliberately broken on a
   newly listed document and `lint_docs.py --check` still failed it
   (`unknown frontmatter key 'XXbrokenXX'`). Corroborated independently — two of the seven
   documents were subagent-authored with no header contract at all and were rejected while
   already listed, so real headers had to be written.

4. **The reason a registry addition is not a weakening is that it adds an obligation.** A
   document in neither list is invisible to the generator; a document in `NOT_GENERATED` is
   asserted to exist, is checked against the header contract, and is required to keep a
   reading-map entry. The register knows more after the edit than before it.

5. **This ADR does not widen what an agent may write.** It records that a narrow, data-only
   class of inspector patch is permitted under human review. Every write still stops at
   Gate D; nothing here makes one automatic.

### Consequences

- The Gate D approval on `557c0b3` now rests on the correct rule rather than on a
  distinction the policy does not draw. The approval itself is not disturbed — the review
  was performed and its basis recorded — but the record it required now exists.
- Kernel lines-of-code, tracked as a health metric, is unchanged by this effort: the edits
  add data, not code.
- Later registry additions in this effort cite this ADR instead of re-arguing the class,
  which keeps the ADR log from accumulating one record per registered document.
- If the register is ever changed to accept documents without a registry entry, this whole
  class of edit disappears and this record becomes historical.

### Falsifies if

An edit made under this ADR is found to have changed what a check enforces rather than what
it knows about — meaning "data only" was not a real boundary and the class should never have
been decided once for many diffs.

Or: a document registered under this ADR is found to have bypassed the header contract,
falsifying decision 3 and with it the argument that a registry addition adds an obligation
rather than removing one.

### Enforcement

`review-cadence`, discharged at Gate D. Nothing in CI distinguishes a data-only registry
addition from a logic change inside the same file — that is what the line-by-line human
review is for, and claiming a mechanism here would be the wish that
`scripts/lint_ci_coverage.py` names.

The mechanical part of decision 2 *is* checkable and is stated so it can be checked by
reading the diff: no `def`, `if`, `return`, `for`, `while` or `assert` line added or removed.

---

## ADR-0047 — The ownership router gains the factory's facts, and runtime state is never evidence

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier1/data-architecture.md` § *Ownership, stated once so it is not restated inconsistently* (frozen), and `docs/tier3/run-instrumentation-specification.md`'s record-type enum · **See also:** ADR-0003 (ACS-1 domain separation), I2 and I6, `docs/tier7/ticket-45-state-authority-decision.md`, ADR-0039 (the type graph) · **D28 waiver:** no

### Context

Coupling Alfred with ECC introduces a second orchestration runtime that keeps its own state.
AutoForge writes `.autoforge/state.json`; ECC keeps `ecc.state-store.v1` with `sessions`,
`skillRuns`, `skillVersions`, `decisions`, `installState`, `governanceEvents` and `workItems`.
Alfred already has homes for most of what those hold, and had no statement about the overlap.

`data-architecture.md` is **frozen**, and already carries the router that resolves this class
of question, along with the rule that decides most of it:

> the stream is a field set, the store is a schema, and the store never re-declares a stream
> field.

Amending a frozen document is what requires this record.

Only one genuine collision was found. `workItems` and `control.work` both claim to say which
tasks exist and what blocks what. Everything else dissolved under the rule above, or turned
out to be a fact Alfred does not have a home for because it does not have the fact.

### Decision

1. **The router is extended rather than replaced, and it gains rows, not descriptions.** Six
   new owners: the palette, the role bindings, the model routing policy, the execution
   lifecycle, `control.work`, and runtime state. Each row names a home; content stays in the
   home. A router that describes what it points at becomes a second copy of it.

2. **`control.work` wins the one real collision.** ECC's `workItems` is a projection at best.
   `control.work`'s `capability_id` is set at dispatch and is the grouping key for cost per
   capability (I9) and for every autonomy grant (D19); a second writable home for task state
   would make that key ambiguous exactly where it is load-bearing.

3. **Runtime state owns nothing, and is never evidence.** `.autoforge/`, `ecc.state-store.v1`
   and any successor are machine-local, gitignored and disposable. No gate, verdict or audit
   may cite them. **If a fact matters, it is emitted into the run record stream when it
   happens**; the runtime copy is incidental and may be deleted at any time without loss.

   Mission Control may render a runtime fact for liveness, carrying provenance that says it is
   unverified. A missing display-only fact renders as **unknown**, never as **none** — the
   distinction between "we did not observe this" and "this did not happen" is the whole
   difference between a liveness indicator and a claim.

4. **`phase_start` and `phase_end` join the record stream.** The lifecycle has seven phases and
   the stream could not previously say which one a turn happened in. Per the rule quoted above
   this is a Run Instrumentation change plus a validator change and **is not a migration**: the
   `evidence.run_record` projection is `jsonb` precisely so that adding a stream field does not
   become an additive migration in the one schema whose migrations are additive-only.

5. **`phase_end.outcome` has two values, not three.** `terminated` and `failed`. The
   three-valued verdict stays at the merge gate: `indeterminate` means *excluded from the ratio
   the autonomy gates read*, and upstream phases feed no ratio. Reusing the word there would
   borrow precision those phases do not have, and would raise a question nobody has asked —
   whether a `fail` at Architect counts against measured merge rate.

6. **`phase_end.checked_by` is a one-value enum, and the single value is the point.** A phase
   terminates when its artifact exists and validates, checked by the orchestrator and never by
   the child that produced it. On 2026-09-02 two child sessions holding complete contracts
   returned `completed` having created no branch, written no file and posted no comment, at a
   combined ~136k tokens over 4 tool calls. The contracts were not the defect; nothing checked
   the artifacts before the completion was accepted. A field that always reads `orchestrator`
   costs nothing and converts "the child self-certified" from an untracked possibility into a
   schema violation.

7. **Risk score gets no home.** It was considered and not adopted. Writing a home for a fact
   nothing produces is how a register starts lying.

### Consequences

- A reader asking "where does this fact live" has one table to consult, and the table now
  covers the factory as well as the product.
- Removing an ECC or AutoForge store loses nothing that a gate reads, by construction. That is
  a property worth having before the coupling deepens, not after.
- The re-entry table in `docs/tier3/execution-lifecycle.md` becomes falsifiable. Its static
  default is defended as *"never catastrophically wrong, only sometimes wasteful"*, and
  `phase_start.re_entry_from` plus `re_entry_override` is what will eventually test that.
- Two documents move: one frozen (this amendment) and one provisional. Neither gains content
  the other already holds.

### Falsifies if

A gate, verdict or audit is found citing runtime state — meaning decision 3 was not a real
boundary and the router promised an isolation the system does not have.

Or: a fact is found with two writable homes after this record, meaning the router was extended
without resolving what it was extended for.

### Enforcement

`schema` for the stream half — the run-record validator rejects a `phase_end` whose `outcome`
is outside the two values, or whose `checked_by` is not `orchestrator`.

`review-cadence` for the router half. Nothing in CI can check that a document has not quietly
become a second home for a fact; that is what the router exists to make visible to a reader.
`scripts/lint_state_authority.py` checks the mechanical part — that every home the router names
exists, and that no runtime path is referenced from a gated document.

---

## ADR-0048 — The palette gains seven `hands-off-to` ports so the lifecycle chain becomes expressible

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `policy/node-palette.json`'s port declarations for five kinds · **See also:** ADR-0039 (the palette as type system), ADR-0046 (the inspector-patch class this is *not* in), `docs/tier7/ticket-43-role-bindings-decision.md`, `docs/tier7/ticket-47-edge-semantics-decision.md`, `docs/tier3/execution-lifecycle.md` · **D28 waiver:** no

### Context

`docs/tier3/execution-lifecycle.md` fixes seven phases and `policy/role-bindings.json` binds the
capabilities that run them. `orchestration/topology.json` is meant to be the graph of that chain,
and today it is a leftover sample: eight nodes, seven edges, using kinds that predate the bindings.

Rebuilding it surfaced a blocker that nothing had checked, because nothing had tried.

**An edge requires its contract type to appear in the source kind's `out` *and* the target kind's
`in`** (`lint_topology.py` TOP005). Measured against the lifecycle chain, **four of seven links are
illegal**, and the worst case is not a near miss:

> `planner` declares `"in": []`.

The planner accepts nothing. **No kind in the palette can hand the planner work**, so the phase that
sequences everything downstream is unreachable by construction. The palette has been in this state
since ADR-0039 without failing anything, because `lint_topology.py` checks that the topology is
internally consistent — not that it can express the lifecycle. The sample topology never tried the
links that fail.

### Decision

1. **Seven port additions across five kinds. All of them `hands-off-to`.**

   ```
   examiner    in += hands-off-to    out += hands-off-to
   architect   in += hands-off-to    out += hands-off-to
   planner     in += hands-off-to
   reviewer                          out += hands-off-to
   validator   in += hands-off-to
   ```

2. **No new contract type.** The vocabulary stays at four — `delegates-to`, `feeds`,
   `hands-off-to`, `reviews` — exactly as `docs/tier7/ticket-47-edge-semantics-decision.md` decided
   after refusing five of the brief's nine proposed edge kinds. This record adds *permission to use
   an existing type*, never a type.

3. **Every phase transition is `hands-off-to`, and the uniformity is deliberate.** The alternatives
   were considered per link and rejected. `feeds` reads as *"here is data for you"*; a phase
   transition is *"I am done, it is yours"*. `delegates-to` from architect to planner would make the
   architect the planner's superior, which the lifecycle does not say anywhere else. One arrow type
   for one meaning leaves a map a reader can follow without a legend.

4. **The two backward `reviews` edges need no addition.** `reviewer → code-writer` and
   `validator → code-writer` are already legal. That is the re-entry table made structural: the
   lifecycle's static default sends a Review or Validate failure back to Execute, and those are the
   only backward edges the type graph permits. **An upstream override to Architect or Plan has no
   edge and therefore cannot be expressed as a traversal** — which is correct, because the lifecycle
   makes an override a recorded exception rather than a normal path.

5. **`wayfinder` becomes `bindable: agent` and enters the graph as the entry point.** It was
   `unbound` because the `~/.claude` wayfinder skill carried `disable-model-invocation: true` — no
   agent could run it, so `unbound` was a statement of fact rather than a preference. The operator
   removed that flag on 2026-09-03, the fact changed, and the binding follows it. The edge
   `wayfinder --delegates-to--> researcher` **needs no port addition**: both ends already declare it.

6. **This is not the data-only class ADR-0046 covers.** ADR-0046 bounds itself to registry entries
   that add no control flow. A port declaration changes what connections are *expressible anywhere
   in the graph*, which is a type-system change and heavier than a topology edit. It carries its own
   record, and this is it.

7. **`orchestration/topology.json` is not written by this record.** It is operator-only (ADR-0039).
   The verified draft is on [issue #47](https://github.com/Akamel01/Alfred/issues/47) for the
   operator to paste, amend or reject.

### Consequences

- The lifecycle chain becomes expressible. Verified rather than asserted: the candidate palette and
  topology were built in a scratch tree and run through `check_topology`, which returns clean at 17
  nodes+edges for the eight-role graph.
- The palette's permissiveness grows by seven ports. That is a real widening of what the type graph
  admits, and it is the cost of the chain being expressible at all.
- `planner` stops being unreachable. Any topology drawn before this record that routed work to the
  planner was invalid and would have failed TOP004.
- One class of bug is now visible that was not: a palette that cannot express the lifecycle passes
  every existing check. Nothing added here detects the next instance of that, and
  `docs/tier7/ticket-47-edge-semantics-decision.md` records it as an open gap rather than a solved
  one.

### Falsifies if

A phase transition is found needing a contract type other than `hands-off-to`, meaning decision 3's
uniformity was a simplification rather than a description.

Or: a port added here is found unused by any edge in the topology the operator eventually writes,
meaning the palette was widened for a link that does not exist.

### Enforcement

`schema`, via `scripts/lint_topology.py` TOP003–TOP005, which already reject an edge whose contract
is absent from either endpoint. The additions here change what those checks admit; they do not
change the checks.

Nothing asserts that the palette *can* express the lifecycle — that is the gap decision 7's
consequence names, and finding it required drawing the graph rather than reading the file.

---

## ADR-0049 — Agent-stated intent is rendered on the live view and nowhere a decision is taken

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier1/mission-control-specification.md` § *Deliberately hard to reach, and why* — the third bullet · **See also:** ADR-0047 (runtime state owns nothing), `docs/tier7/ticket-52-read-model-decision.md`, `docs/tier3/handoff-contract-standard.md`, D22 · **D28 waiver:** no

### Context

The operator asked Mission Control to show a live multi-agent view carrying, per agent, *"what each agent is working on right now with the model used and goals."*

Most of that is derivable from recorded facts. `phase_start` carries `capability_id`, `phase` and `task_class`; `policy/model-routing.json` maps `capability_id` to a pinned model; the task carries its executable criterion. *Which capability is running, in which phase, on which model, against which criterion* needs no agent to say anything.

**"Goals" is the part that does not derive.** An agent's statement of what it is trying to do is authored by the party being judged, and the specification forbids rendering it:

> **Any agent self-assessment** of progress, completeness or blockage. It is not recorded, so it cannot be rendered.

The operator was shown that rule and the reasoning behind it, and chose to render agent-stated intent anyway. This record exists because that reverses a stated rule, and a reversal that lives only in a conversation is not a decision the register can be held to.

### Decision

1. **Agent-stated intent is rendered on the live view, and only there.** It is attributed to the agent, marked unverified, and passes the A10 scan before render like every other externally-originated string.

2. **It never appears on S2 Review.** The ban's argument is specific and it survives intact where it applies: on the approval screen, agent prose is *the thing being judged arguing with its judge*. Nobody approves anything on a monitoring view, so the argument does not reach it. S4's existing treatment — behind one click, labelled, escaped, scanned — is unchanged.

3. **It is display-only under ADR-0047.** Agent-stated intent is runtime state. No gate, verdict or audit may cite it. When it is unavailable the live view renders **unknown**, never **none**.

4. **It is never the only thing shown about an agent.** The recorded facts — capability, phase, model, task, criterion, budget consumed — are rendered alongside and with more weight. An operator who ignores the prose entirely loses nothing they need.

5. **The criterion outranks the stated goal, visually and in the record.** Where an agent's stated intent and its executable criterion disagree, the criterion is what the work will be judged against and the surface must not imply otherwise.

### Consequences

- The live view is readable at a glance, which is what the operator asked for and what a wall of `capability_id`s does not deliver.
- The approval gate is unchanged. The rule that was reversed is reversed exactly where its argument does not apply, and nowhere else.
- A new class of content reaches an operator screen: agent-authored prose, on a surface the operator watches while work runs. The A10 scan is what stands between that and a prompt-injection attempt with a shorter path, and it is now load-bearing on one more surface than before.
- The specification's *Deliberately hard to reach* list loses one of its four bullets on one screen. The other three — held-out detail, agent prose on S2, the diff as a default view — are untouched.

### Falsifies if

An operator decision is found to have turned on agent-stated intent rather than on the criterion — meaning decisions 2, 4 and 5 did not actually keep the prose out of the deciding path, and the ban should not have been narrowed.

Or: agent-stated intent is found rendered on S2, or cited by a gate, verdict or audit.

### Enforcement

`review-cadence`. Nothing in CI can tell that a rendered string influenced a human decision. What *is* mechanical is decision 2 — the read model and command surface are separate programs with no import path between them, CI-checked, and the live view is the read model's. S2's decision-critical panel is rendered by the command surface, which has no access to runtime state at all.

That separation is why decision 2 is a boundary rather than a convention: S2 cannot render agent prose because the program that draws S2 cannot reach it.

---

## ADR-0050 — Mission Control is hosted off-host, and the loopback bind is replaced rather than relaxed

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier1/mission-control-specification.md` § *Authentication and exposure*; `docs/tier2/coding-standards.md` § *Structure* (frozen, `ci-gate`) · **See also:** ADR-0049, `docs/tier4/threat-model.md`, `docs/tier4/permission-and-identity-model.md` · **D28 waiver:** no

### Context

The operator has a Vercel account and wants Mission Control deployed from GitHub with automatic deployment — **both programs**, command surface included, so a merge can be authorized from anywhere.

The specification's current position is not "no authentication by oversight." It is a reasoned position that depends entirely on one control:

> **Loopback bind only** — `127.0.0.1`. Asserted at startup; the process refuses to start bound to any other interface. **This is the actual access control.**

Everything else follows from it. No password, no session store, no TLS, because *"on a single-user machine the OS login is the authentication boundary, and a password on a loopback service protects against nothing a local process could not bypass by reading the same database."*

The specification also names, in advance, what changes if the surface ever becomes reachable off-host. That list was written for exactly this moment and it is adopted here rather than rediscovered.

**The operator was shown this and chose full remote for both programs.** The reasoning is recorded so the decision is legible: this is not relaxing a setting. It removes the only access control the design has and requires a different one to be built.

### Decision

1. **Off-host is the target architecture for both programs.** Not the read model alone. A merge may be authorized from a machine that is not the operator's.

2. **Nothing real deploys until the replacement controls exist.** The loopback bind is removed only when what replaces it is in place. Concretely, and taken from the specification's own list:

   - **Real authentication with a per-action identity.** `actor_id` stops being constant and becomes load-bearing. It is already in the envelope for exactly this reason, so this is a behaviour change and **not** a hash-breaking schema change.
   - **TLS**, terminated by the host.
   - **Rate limiting** on every action endpoint.
   - **An audit of the read model's query surface against a hostile client** rather than a trusted one. Every query the read model exposes was written assuming the caller is the operator.
   - **The `Host` allowlist and `Origin` check** are re-derived for the deployed origin. Their purpose — DNS rebinding and cross-origin POST — does not disappear off-host; it grows.

3. **The residual stops being acceptable and is replaced, not carried forward.** Today's accepted residual reads *"any local process running as the operator can authorize a merge."* Off-host, "the person at the machine" is no longer a meaningful identity, and the specification says so. The residual after this decision is whatever the authentication design leaves, and it must be restated there rather than inherited from here.

4. **The static design prototype may deploy immediately.** It carries no database connection, no credentials and no real data. It is a picture. Deploying it exercises the pipeline and lets the design be reviewed on real devices while item 2 is built.

5. **The structure fence gains `src/mission_control/`.** The specification already assigns the read model that path and the command surface `harness/mission_control/`; the latter is inside an existing fence entry, the former is not, and code cannot land where the fence has no room for it.

### Consequences

- Mission Control's security model changes from *"one control, honestly stated"* to *"several controls that must each hold."* That is strictly more surface and strictly more that can be got wrong, and it is the price of remote access.
- The work in item 2 is not incidental. It is a project, and it blocks every real deployment.
- Item 4 means a Vercel deployment exists long before item 2 completes. **The hazard is obvious and named: a working URL invites pointing it at a real database.** The prototype must carry a visible marker that it is not connected to anything, and the marker is not decoration.
- `actor_id` becoming load-bearing is the one piece of good news. The envelope already carries it, so the evidence chain does not need to change shape to record who did what.

### Falsifies if

A real Mission Control surface — either program — is found reachable off-host without the item 2 controls in place.

Or: the deployed prototype is found connected to any database, or presenting any value that is not fabricated.

### Enforcement

`review-cadence` for the architecture. `ci-gate` for the fence entry, via `tools/vaultgraph/extract/layout.py`, which already reads the fence and surfaces an unnamed top-level entry as a layout miss.

The startup assertion that currently refuses a non-loopback bind stays in place and is the thing item 2 must earn the right to change. Removing it before the replacement exists is what decision 2 forbids, and no lint can check that — which is why it is stated as the first falsification condition rather than left implied.

---

## ADR-0051 — The live view is pulled forward ahead of its trigger, and the trigger's reasoning is not discharged

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier1/mission-control-specification.md` § *Deliberately deferred*, the second row · **See also:** ADR-0049, ADR-0050, `docs/tier7/ticket-52-read-model-decision.md`, #69 · **D28 waiver:** no

### Context

The operator asked for a live multi-agent view: a graph of agents with their contexts and contracts, what each is working on right now, and the traffic between them.

The specification already defers exactly this, with a two-part trigger and a stated reason:

> **Live in-flight run observability** — trigger: the first task whose wall-clock exceeds its budget by a margin an operator would have interrupted, **and an interruption path exists**. *Until interruption is possible, watching is not observability, it is anxiety.*

**Neither condition is met.** No task has overrun in a way that mattered, and no interruption path exists. The view is being built anyway, on the operator's decision.

This record exists because the deferral was reasoned, and a reasoned deferral overridden without a record looks in hindsight like a deferral nobody noticed.

### Decision

1. **The live view is built now, ahead of both trigger conditions.**

2. **The trigger's reasoning is not discharged, and is not pretended away.** *"Watching is not observability, it is anxiety"* remains true until an interruption path exists. Building the view does not make it false; it makes it a cost the operator has accepted with the sentence in front of them.

3. **The interruption path is filed as [#69](https://github.com/Akamel01/Alfred/issues/69)** rather than left as an assumption the view will eventually acquire. The ticket carries the hard part explicitly: an operator-interrupted attempt is not an agent failure, and counting it as one corrupts the merge rate the autonomy gates read.

4. **Mechanically it is polling, not streaming.** `docs/tier7/ticket-52-read-model-decision.md` D1 stands unchanged: queries at request time, no snapshots, no event stream. The live view re-queries on a short interval and stamps how current it is. §19's duplicate, partial and reordered event failures therefore still cannot occur, because there are still no events.

5. **It is visually distinct from Part B, deliberately.** Part B renders what happened, per attempt, as *"a pure function of two immutable inputs … never stored."* The live view renders runtime state, which ADR-0047 says owns nothing and is never evidence. Two graphs where one is trustworthy in a way the other structurally cannot be:

   | | Part B | Live view |
   |---|---|---|
   | Edges | solid | dashed for unverified runtime traffic, solid for recorded facts |
   | Ground | full weight | lighter |
   | Marker | none | persistent `live · unverified`, with the poll timestamp |

   Without that separation an operator reads the mutable diagram with the trust the immutable one earned, which is the failure mode the whole read-model/command-surface split exists to prevent, arriving through the graphics.

6. **Missing runtime facts render as `unknown`, never `none`.** The distinction between *we did not observe this* and *this did not happen* is the entire difference between a liveness indicator and a claim.

### Consequences

- The operator gets the view they asked for, and the sentence explaining why it is premature is on the record where a reader will find it rather than in a chat log.
- [#69](https://github.com/Akamel01/Alfred/issues/69) is now load-bearing for this feature being what it claims to be, and is tracked rather than implied.
- A second graph exists in the product, which is a maintenance cost and a chance for the two to drift in appearance until the distinction in decision 5 erodes. That erosion would be silent, and nothing checks it.
- Polling at a short interval against the evidence store is a query-load question that has not been measured. The specification's answer to a slow query is *"an index or a narrower query — never a stored aggregate"*, and that answer still applies.

### Falsifies if

An operator is observed watching a run overrun with no action available — the specification's own prediction, arriving as designed.

Or: the live view and Part B become visually indistinguishable, meaning decision 5 was stated and not maintained.

### Enforcement

`review-cadence`. Nothing in CI can check that two renderings look sufficiently different from each other, and claiming otherwise would be the wish `scripts/lint_ci_coverage.py` names.

What *is* structural is decision 4's consequence: there is no event stream to build, so the failure class it would introduce cannot arrive by accident. And ADR-0049's decision 2 holds by construction — the live view is the read model's, and the program that draws S2 cannot reach runtime state at all.
