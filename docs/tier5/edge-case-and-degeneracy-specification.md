---
status:        frozen
owner:         human
enforcement:   ci-gate
evidence:      The oracle's own regression suite asserts `0.0` or `inf` for several measures, which is why those measures were excluded from the verified task class — a test pinning a sentinel is not evidence the metric computes. Degenerate geometry is also where a wrong number is least likely to throw and most likely to look plausible.
falsifies_if:  A metric returns a finite number for an input this document declares undefined, or returns NaN anywhere, or a case observed in real scenario data appears nowhere in this catalog.
review_after:  Phase 1
---

# Edge Case and Degeneracy Specification

Surrogate safety metrics are mostly divisions by a closing rate and mostly defined only
where a conflict exists. The interesting inputs are therefore the ones where the
denominator vanishes or the conflict does not exist — and those are exactly the inputs
where a wrong implementation returns a plausible number instead of failing.

This document is the catalog. It exists before Phase 0 code because it defines what the
property tests assert and what the held-out composed criteria perturb.

## The totality rule

**Every metric is total over its declared input domain.** For every input it returns
either a defined value or an explicit `Undefined(reason)` carrying a machine-readable
reason code.

Forbidden without exception:

- **NaN as an output.** NaN propagates silently through aggregation and comparison, and
  `NaN != NaN` means an equality-based test cannot even detect it.
- **A finite number where the quantity is undefined.** This is the plausible-wrong
  failure in its purest form.
- **An exception as the normal representation of a degenerate case.** Degeneracy is
  ordinary — a scenario with no conflict is not an error — and exceptions do not survive
  vectorized evaluation across a scenario.

Exceptions are reserved for **contract violations**: wrong units, unsorted timestamps,
mismatched array lengths. Those are caller bugs, not degeneracies.

## Sentinel policy

| Sentinel | Means | Example |
|---|---|---|
| `+inf` | the event provably never occurs on the declared horizon | TTC with diverging paths |
| `0.0` | the event is occurring at the evaluated instant | TTC when bounding boxes already overlap |
| `Undefined(reason)` | the quantity is not defined for this input | PET where no conflict area exists |

`+inf` and `0.0` are **defined values, not error signals**, and the distinction is
load-bearing: `Undefined(NO_CONFLICT_AREA)` and `+inf` are different claims, and a metric
that returns the second where it means the first is wrong even though both read as "no
collision".

Corollary for testing: a regression test asserting `0.0` or `inf` is a weak assertion. It
is satisfied by a stub that returns the constant. Sentinel cases require a companion
assertion on a nearby non-degenerate input.

## Representation

Settled by **ADR-0001**. Two forms, one conversion point at the metric's return:

- **Inside computation, `MetricSeries`** — `values: float64[]` alongside
  `reasons: uint8[]`, where `0` means defined. The reason array is the mask, so it keeps
  a per-timestep reason where a boolean mask would collapse E7, E8 and E16 into one bit.
  `+inf` is a legal value here; NaN never is.
- **On every boundary — `MetricValue`**, a tagged union of `defined` / `infinite` /
  `undefined`, carrying the reason on the third arm.

The tag is not decoration. **Infinity cannot cross a JSON boundary as a float**: RFC 8259
has no infinity literal, and Pydantic's default serializer converts `+inf` to `null` —
which, under a `float | None` representation, would silently turn E1 into E7 with no
error raised anywhere.

Reason codes are a global enum with **stable names**. The wire format and the
content-addressed hash carry the name; the `uint8` integer is a private in-memory
encoding (ADR-0002). `0` means defined and `255` means `UNKNOWN_CODE` — an unrecognized
code decodes to 255 and **never to 0**, since decoding an unknown reason as "defined"
would reintroduce plausible-wrong output through the deserializer.

Composition never absorbs: an undefined input yields `Undefined(UPSTREAM_UNDEFINED)`
carrying the originating code, so the cause chain survives. Silent absorption is NaN with
extra steps.

## Geometric and kinematic catalog

| # | Condition | Required behaviour |
|---|---|---|
| E1 | Paths diverging; separation monotonically increasing | `+inf` |
| E2 | Relative velocity zero, gap non-zero | `+inf` — never a division by zero |
| E3 | Relative velocity zero, gap zero (contact) | `0.0` |
| E4 | Bounding boxes already overlapping at t₀ | `0.0`, and the metric records that it was evaluated post-contact |
| E5 | Ego stationary throughout | defined; not a special case in code, must fall out of the general formula |
| E6 | Both agents stationary | `+inf`, or `Undefined(NO_RELATIVE_MOTION)` where the measure requires motion — declared per metric |
| E7 | Exactly parallel paths, never intersecting | `Undefined(NO_CONFLICT_AREA)` for conflict-point measures; `+inf` for gap-closure measures |
| E8 | Conflict area exists; only one agent ever enters it | `Undefined(SINGLE_OCCUPANCY)` — PET is not defined on one arrival |
| E9 | Conflict area entered simultaneously by both | `0.0` for PET; a collision, not a near-miss |
| E10 | Closing then receding within the horizon (grazing) | minimum over the horizon, not the value at t₀ |
| E11 | Multiple conflict areas along the path | evaluated per area; the aggregate rule is declared, never implicit |
| E12 | Quadratic solution with negative discriminant | no real root → `+inf`, not a complex or NaN result |
| E13 | Quadratic with two positive roots | earliest root; the later root is a second contact and is not the answer |
| E14 | Root at exactly t = 0 | `0.0`, inclusive of the boundary |
| E15 | Solution beyond the declared horizon | `+inf` with the horizon recorded, not the out-of-horizon number |

## Trajectory and sampling catalog

| # | Condition | Required behaviour |
|---|---|---|
| E16 | Single timestep | `Undefined(INSUFFICIENT_SAMPLES)` for any measure requiring a derivative |
| E17 | Two timesteps, measure requires acceleration | `Undefined(INSUFFICIENT_SAMPLES)` — a second derivative needs three |
| E18 | Non-uniform timestep | resampling policy is declared configuration with cited provenance; refusing is permitted, silently assuming uniformity is not |
| E19 | Gap in the trajectory (missing frames) | evaluated per contiguous segment; never interpolated across the gap without recording it |
| E20 | Unsorted or duplicate timestamps | contract violation → exception |
| E21 | Agent appears mid-scenario | evaluated only over its observed window; the window is part of the result |
| E22 | Agent disappears mid-scenario (occlusion or exit) | as E21; absence is never read as a stationary agent at the last position |
| E23 | Zero-length trajectory | `Undefined(NO_DATA)` |
| E24 | Only one agent in the scenario | `Undefined(NO_COUNTERPART)` for pairwise measures |
| E25 | Self-pairing (ego against itself) | contract violation → exception |

## Numerical catalog

| # | Condition | Required behaviour |
|---|---|---|
| E26 | Near-zero denominator | tolerance is **declared, cited, versioned configuration** — never an inline magic epsilon |
| E27 | Catastrophic cancellation in the discriminant | numerically stable form used; the choice recorded in the metric's model card |
| E28 | Values beyond physical plausibility (speeds, accelerations) | computed and emitted, flagged against the published validity envelope — never silently clamped |
| E29 | Very large coordinates (UTM-scale) with small separations | precision loss bounded and stated; local-frame translation applied before differencing |
| E30 | Summation over a scenario | fixed operation order, no reordering reductions — byte-identical replay is a product requirement |

## Aggregation

Aggregation is where undefined values are most often lost. Two rules:

1. **Every aggregate reports `(value, n_defined, n_undefined)`.** An aggregate that
   silently drops undefined entries is forbidden, because "mean TTC 4.2 s" over a set
   where two thirds were undefined is a different claim from the same number over a set
   where none were.
2. **`+inf` is not dropped to make a mean finite.** Either the aggregate is defined over
   the extended reals, or the aggregation excludes them explicitly and reports the count.
   Which one applies is declared per metric, not chosen at the call site.

## Invariance obligations

These are properties, not cases, and they are the load-bearing half of the test suite
because they hold over generated inputs the implementation never saw:

- **Rigid-transform invariance.** Rotating and translating the whole scene changes no
  metric value. This is the single strongest property available in the domain and it
  catches an entire family of frame-handling bugs.
- **Time-shift invariance** for measures not defined against absolute time.
- **Unit consistency.** Scaling all lengths scales length-dimensioned outputs and leaves
  dimensionless ones fixed.
- **Monotonicity in closing speed**, holding geometry fixed.
- **Boundedness** where the definition is bounded.
- **Symmetry or declared asymmetry** on agent swap — several measures are deliberately
  asymmetric, and which ones is stated rather than discovered.

## Why these are held-out material

Degenerate cases are the highest-value held-out criteria in the product. An
implementation that special-cases exactly the degenerate inputs it was shown, and is
wrong on the geometrically identical case it was not, passes every visible check — the
visible/held-out divergence this architecture is built around, arriving with no exploit
and no dishonesty anywhere in the loop.

So: **visible criteria carry a subset of this catalog; the complement stays held out**,
and held-out perturbations resample degenerate configurations that were never published.

## Enforcement

Each row above is a numbered test case. CI asserts that every catalog entry has a test,
that no metric can return NaN on any generated input, that every metric's declared
`Undefined` reason codes are exhaustive over its domain, and that no numeric tolerance
appears as a literal in metric code rather than as configuration. A metric added without
a completed edge-case table for its own domain does not merge.
