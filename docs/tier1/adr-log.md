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

**Date:** 2026-08-12 · **Status:** Accepted · **Supersedes:** none · **Amended by:** ADR-0002 (encoding clause)

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

**Date:** 2026-08-12 · **Status:** Accepted · **Supersedes:** none · **Amended by:** ADR-0004 (float grammar)

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
