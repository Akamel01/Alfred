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
