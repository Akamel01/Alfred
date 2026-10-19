---
status:        directional
owner:         executable
enforcement:   review-cadence
evidence:      Reads policy/model-routing.json (the empty trivial class and the forbidden list), policy/role-bindings.json (the 24 unset D19 version fields), harness/fingerprint/factory.py (the 11-field record), docs/tier3/run-instrumentation-specification.md (attempt_start, attempt_end, task_end), docs/tier0/charter-and-non-goals.md K3, and docs/tier2/execution-order.md:424. No measurement of any model against any Alfred capability exists; this document specifies the measurement rather than reporting one.
falsifies_if:  A capability enters the trivial class on a run whose fingerprint does not match the pair this document states for the arm that produced it, or a merge rate taken under this protocol is read as a point estimate rather than a Wilson 95% interval, or a run starts while docs/tier2/execution-order.md:424 still forbids orchestration.
review_after:  Phase 2
---

# Ticket #70 — Measurement design for the trivial class

Pre-run design for measuring a capability against the cheap model. No run exists yet; runs remain impossible until K3 clears and a dispatcher exists (`docs/tier2/execution-order.md:424`). This document specifies the measurement; it reports nothing and satisfies none of the ticket's five checkboxes.

## What this document is, and what it is not

This is a pre-run design. It settles the fingerprint pair, the N determination, the paired-run protocol, and the threshold-derivation rule. It is not a grant, not a run, and not a trivial-class entry. No fingerprint instance exists yet, `trivial_class.members` stays empty, and `gpt-5-nano` runs nothing until the conditions in §6 are met.

## The fingerprint pair

`FactoryFingerprint` has exactly these 11 fields, in declaration order (`harness/fingerprint/factory.py:82-101`). The D19 group is imported from `record.py` (`factory.py:62-63`), and `d19_is_shared()` (`factory.py:177-185`) is the callable form of "shared verbatim". Every field is a `str`; `__post_init__` rejects empty and `inherit` (`factory.py:103-122`). The derived digest is never stored (`factory.py:129-132`), so no digest value appears in this document.

| # | Field | Group | Capable arm | Cheap arm | Basis for the stated value |
|---|---|---|---|---|---|
| 1 | `capability_id` | D19 | `capability:code-writer@1` | `capability:code-writer@1` | `policy/model-routing.json:72`, `policy/role-bindings.json:113` |
| 2 | `model_version` | D19 | pending capture | pending capture | no register line pins a version string for either serving path; the routing file's own authority line says a change there is what moves `model_version` (`model-routing.json:3`) |
| 3 | `prompt_version` | D19 | unset | unset | `policy/role-bindings.json:121` (#86's ruling: all 24 stay `unset`, never placeholder-filled) |
| 4 | `tool_version` | D19 | unset | unset | `policy/role-bindings.json:122` |
| 5 | `context_strategy_version` | D19 | unset | unset | `policy/role-bindings.json:123` |
| 6 | `provider` | served | `anthropic` | pending capture | `model-routing.json:74` for the capable arm; the register names no provider for the cheap model anywhere |
| 7 | `model_id` | served | `claude-sonnet-5` | `gpt-5-nano` | `model-routing.json:73`; `model-routing.json:12-13` (the forbidden-list key, the register's own spelling) |
| 8 | `api_version` | served | pending capture | pending capture | nothing in the register pins it |
| 9 | `routing_key` | served | `capability:code-writer@1` | pending capture | `factory.py:92-95` ("the capability_id the model was resolved through"); today MR001 guarantees exactly one route per capability and it resolves the capable model — the measurement dispatcher must record the key that resolved the cheap arm, and an empty key is refused by `__post_init__` |
| 10 | `harness_identity` | served | pending capture | pending capture | no dispatcher exists |
| 11 | `orchestrator_sha` | served | pending capture | pending capture | no dispatcher exists |

Invariants:

- Rows 1, 3, 4, 5 are identical across arms today; rows 10 and 11 must be identical across arms or the comparison is confounded (two dispatcher revisions are two experiments); row 2 is identical until captured, and capture must record the real value rather than a placeholder (role-bindings.json note at line 8: "Do not fill these with placeholders to make them look set").
- The pair differs in the served group: `provider`, `model_id`, and `api_version` (and `routing_key` once captured); `model_version` is a D19 field and may also differ once captured.
- Correction of the ticket comment, stated in this shape: "The ticket comment says the two fingerprints 'differ in exactly `model_id` and `model_version`. That assumes one provider path. With the cheap model served by a different provider, the pair differs in `provider`, `model_id` and `api_version`, and possibly `routing_key` if the routing lookup differs; `model_version` and `api_version` are pending capture, and the five D19 fields are shared verbatim (the field list, not the values)."
- No construction is possible today: no dispatcher exists to capture rows 6-11 for the cheap arm; the table is a specification, not a record. No placeholder is written where capture has not happened.

## The N determination

This document states which question each N answers, per grilling Q2, with the arithmetic corrected for the two-proportion case.

Decision rule 1 — entry (single arm). A capability enters the trivial class only if its measured merge rate clears a bar. The only bar the register owns is K3's: "read as a Wilson 95% interval rather than a point estimate — the criterion fires when the interval's lower bound sits below 0.50" (`docs/tier0/charter-and-non-goals.md:87`). K3's own evaluation count is 20 (15/20 clears at LB 0.5313; 14/20 fails at 0.4810) — that is K3's convention, not a model-comparison instrument.

Adopted rule-matched number. The entry decision is taken by K3's Wilson-LB rule, so the power calculation must be taken under that rule, not under a normal-approximation proxy. N_entry = 187 tasks on the cheap arm: the smallest n whose exact binomial power under the rule (k* = smallest k with Wilson 95% LB(k, n) ≥ 0.50; power = P(Binomial(n, 0.60) ≥ k*)) is at least 0.80 at true p = 0.60. k* = 107; exact power = 0.802930. At n = 186 the power is 0.777947, so 187 is the first qualifying n. Sensitivity under the same rule: N_entry = 82 at true p = 0.65 (k* = 50, power 0.811209) and 43 at true p = 0.70 (k* = 28, power 0.808087).

Cross-check (normal approximation). The one-sample one-sided normal-approximation formula gives 153 at p = 0.60 (152.46), 67 at 0.65, 37 at 0.70 — the plan handoff's "n≈152" reproduces there (152.27 with rounded constants). At n = 153 the rule's exact power is 0.708241, which is why 187 is adopted rather than 153. The normal-approximation numbers are retained as the cross-check that reproduces the plan's "n≈152", not as the adopted number.

Cross-check at the entry N. At n = 153 the first integer count whose Wilson 95% lower bound clears 0.50 is 89 (LB 0.5025); 88 gives 0.4959. At n = 187 the rule-matched analogue: k* = 107 (LB(107, 187) = 0.5005; LB(106, 187) = 0.4952). This document states these so 187 and the K3 bar are visibly the same decision rule.

Decision rule 2 — comparison (two arms). The claim "the cheap arm's rate is not worse than the capable arm's by more than the declared gap" is adjudicated by a two-proportion test (α = 0.05 two-sided, power 0.80, p1 = 0.60 vs p2 = 0.50, pooled variance); each arm's rate is reported and read as a Wilson 95% interval, never a point estimate (K3's reading).

N_compare = 388 per arm (776 tasks total). Two-proportion, α = 0.05 two-sided, power 0.80, `p1 = 0.60` vs `p2 = 0.50`, pooled variance:

```
n = ( z_{1−α/2}·√(2·p̄·(1−p̄)) + z_{power}·√(p1(1−p1)+p2(1−p2)) )² / (p1−p2)²
  = (1.9600·0.7036 + 0.8416·0.7000)² / 0.01 = 387.34  → 388
```

Correction, recorded here and in ADR-0070: grilling Q2's "two-proportion" arithmetic (`n = 2·(1.96·√(2·0.55·0.45) + 0.84·√(0.6·0.4+0.5·0.5))²/(0.1)² ≈ 152`) is not reproducible: as written it computes 773.8 (a leading factor 2 on top of the √2 already inside the pooled term); de-doubled it computes 386.9, i.e. the same ≈388. The number 152 is the one-sample entry number above, misfiled under a two-proportion label.

Interval-reporting alternative. If the comparison is reported as a difference interval rather than a test, this document states the half-width of 0.10 at the observed rates (0.60/0.50) requires 189 per arm; at the worst case (0.50/0.50) 193:

```
n = z²·(p1(1−p1)+p2(1−p2)) / hw²   →   189 / 193
```

Which N answers which. N_entry = 187 answers "does the cheap arm clear the bar" (one arm, K3's form). N_compare = 388 per arm answers "do the two arms differ by no more than the declared gap" (paired). The 388-per-arm protocol contains the 187-task answer; an 187-task single-arm run cannot answer the comparison. Both rates are read as Wilson 95% intervals, never point estimates; `indeterminate` verdicts and `harness_fault` terminations are excluded from the rate and counted and reported as harness health (charter K3's interval form; `run-instrumentation-specification.md:329-346`).

Reproducibility mechanism (one mechanism, minimal): the doc carries (a) a fenced stdlib-Python block that recomputes every number and prints them, and (b) a machine-readable block the test reads:

```python
# Consolidated transcript: every number the design doc claims. Stdlib only.
import hashlib, math
from statistics import NormalDist

nd = NormalDist()
z1, z2, zp = nd.inv_cdf(0.95), nd.inv_cdf(0.975), nd.inv_cdf(0.80)

def n_one(p, p0=0.50, power=0.80):
    za, zb = nd.inv_cdf(0.95), nd.inv_cdf(power)
    return (za*math.sqrt(p0*(1-p0)) + zb*math.sqrt(p*(1-p)))**2/(p-p0)**2

def n_two(p1, p2, power=0.80):
    za, zb = nd.inv_cdf(0.975), nd.inv_cdf(power)
    pb = (p1+p2)/2
    return (za*math.sqrt(2*pb*(1-pb)) + zb*math.sqrt(p1*(1-p1)+p2*(1-p2)))**2/(p1-p2)**2

def wilson_lb(k, n):
    z, p = nd.inv_cdf(0.975), k/n
    d = 1+z*z/n
    return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)))/d

def k_star(n, bar=0.50):
    # smallest k whose Wilson 95% LB clears bar
    for k in range(n + 1):
        if wilson_lb(k, n) >= bar:
            return k
    return n + 1

def exact_power(n, p, k):
    # P(Binomial(n, p) >= k)
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))

print(f"z(0.95)={z1:.4f}  z(0.975)={z2:.4f}  z(0.80)={zp:.4f}")
for p in (0.60, 0.65, 0.70):
    n = n_one(p); print(f"one-sample one-sided, p0=0.50, true p={p:.2f}, power=0.80: n={n:.2f} -> {math.ceil(n)}")
print(f"one-sample with rounded z (1.6449/0.84): n={ (1.6449*0.5 + 0.84*math.sqrt(0.24))**2/0.01 :.2f}")
n2 = n_two(0.60, 0.50); print(f"two-proportion 0.60 vs 0.50, per arm: n={n2:.2f} -> {math.ceil(n2)}")
g = 2*(1.96*math.sqrt(2*0.55*0.45)+0.84*math.sqrt(0.6*0.4+0.5*0.5))**2/0.01
g2 = (1.96*math.sqrt(2*0.55*0.45)+0.84*math.sqrt(0.6*0.4+0.5*0.5))**2/0.01
print(f"grilling formula as written: {g:.1f}; evidently de-doubled: {g2:.1f}")
for p1, p2 in ((0.6, 0.5), (0.5, 0.5)):
    n = z2*z2*(p1*(1-p1)+p2*(1-p2))/0.01
    print(f"difference CI half-width 0.10, observed {p1}/{p2}: n per arm={n:.2f} -> {math.ceil(n)}")
for k, n in ((15,20),(14,20),(9,10),(8,10)):
    print(f"Wilson 95% LB {k}/{n} = {wilson_lb(k,n):.4f}")
k = next(k for k in range(153) if wilson_lb(k,153) >= 0.50)
print(f"n=153: first k with LB>=0.50 is {k} (LB={wilson_lb(k,153):.4f}); {k-1} gives {wilson_lb(k-1,153):.4f}")
for n in (187,):
    ks = k_star(n)
    print(f"n={n}: k*={ks}, LB(k*,n)={wilson_lb(ks,n):.6f}, LB(k*-1,n)={wilson_lb(ks-1,n):.6f}, exact power at p=0.60={exact_power(n,0.60,ks):.6f}")
    print(f"  exact power at n=186: {exact_power(186,0.60,k_star(186)):.6f}")
for n, p in ((187,0.65),(187,0.70)):
    ks = k_star(n)
    # sensitivity: recompute k* at bar 0.50 for the same n, power at p
    print(f"  n=187 p={p:.2f}: k*={ks} exact power={exact_power(187,p,ks):.6f}")
# sensitivity Ns under the rule
for p in (0.65, 0.70):
    # find smallest n with exact power >= 0.80 at p
    n = 1
    while True:
        ks = k_star(n)
        if exact_power(n, p, ks) >= 0.80:
            break
        n += 1
    print(f"rule-matched N at p={p:.2f}: n={n} (k*={k_star(n)}, power={exact_power(n,p,k_star(n)):.6f})")
s = "\n".join(str(70000+i) for i in range(388))
print("seed list 70000..70387 sha256:", hashlib.sha256(s.encode()).hexdigest())
```

<!-- Numbers recomputed by tests/test_ticket_70_n_sizing.py — edit both or neither. -->

N_entry = 187
N_entry_p65 = 82
N_entry_p70 = 43
N_entry_normal_approx = 153
N_entry_normal_approx_p65 = 67
N_entry_normal_approx_p70 = 37
N_compare = 388
N_halfwidth_060_050 = 189
N_halfwidth_worst = 193
seed_list_sha256 = 902b431005e38429cd2aedfe2c7e0f6ec7e30ee7dbc3ddf27ecdc8212a91aeee


## The paired-run protocol

- Capability: `capability:code-writer@1`, one, justified. Its route reason is "Execution against an already-decided plan, under an executable criterion" (`model-routing.json:76`) — a merged change with an executable criterion, so a merge rate exists at all. Every other capability is disqualified by the forbidden list for the cheap model (`model-routing.json:12-24`): `wayfinder` (planning/architecture-shaping — architecture), `researcher` (requirements — it feeds requirements authoring and its artifact is not a merged change, so no merge rate exists), `examiner` (requirements grilling — route reason says "Explicitly on the forbidden list"), `architect` (architecture), `planner` (architecture-shaping planning plus its independent critique pass — architecture, final review), `reviewer` (final review), `validator` (validation authority).
- Two arms, one task set. Capable arm: the current route value (`claude-sonnet-5` / `anthropic`). Cheap arm: `gpt-5-nano` via a measurement-scoped explicit override (not a routing-policy change — `trivial_class.members` stays `[]`). The dispatcher must record which routing key resolved the model; if the cheap arm's key cannot be recorded, its `FactoryFingerprint` cannot be constructed and check A refuses the attempt — that is a precondition, stated, not a value invented here.
- Seeds, frozen and hashed. One seed per paired task, `seed_i = 70000 + i` for `i in range(388)`, both arms sharing the seed. Provenance: I11 requires deterministic seeds (`docs/tier1/cross-stage-invariants.md:35`); `attempt_start.seed` is an int (`run-instrumentation-specification.md:103`); no dispatcher exists to assign seeds, and `bench/fingerprints/` is protected append-only, so the list is frozen in the doc as a derivation plus a hash rather than as a committed file. Base 70000 is clear of every seed recorded under `bench/results/` (7, 91, 3355, 424242). Hash: `seed_list_sha256 = sha256("\n".join(str(s)))` = the value in the N determination section; the test recomputes it from `N_compare`.
- Held-out criteria by identity only. Tasks reference held-out criteria by `criterion_ref` identity; `tests/heldout/` is protected and never in agent context (`policy/protected-paths.json:17-19`); the stream carries `held_out_result` as a class label only (`run-instrumentation-specification.md:376`).
- Bounded retry budget. Recorded on `task_end.retry_budget` (`run-instrumentation-specification.md:361-376`); the value is owned by the future dispatcher configuration and is pending capture; the design requires it identical across arms and recorded — no register line sets it today, so none is invented.
- Null-agent floor control. The null agent runs the same criterion set and must fail; a floor that passes means the criterion is gameable and the measurement is void (`harness-self-test-specification.md`, null-agent floor; run in CI by the "Harness self-test (null-agent floor, seeded-defect ladder, controls)" step).
- The reading consumes exactly these fields. From `attempt_end` (`run-instrumentation-specification.md:329-359`): `termination`, `verdict`, `stop_reason`, `turns`, `tool_calls`, `mutating_tool_calls`, `wallclock_ms`, `agent_ms`/`criterion_ms`/`harness_ms`, `tree_sha256`, `loaded_context_length` (re-asserted), `progress_final`, `premature`. From `task_end` (lines 361-376): `attempts`, `retry_budget`, `outcome`, `wallclock_ms_total`, `wallclock_ms_to_outcome` (the numerator of wall-clock per success), `verdict_final`, `held_out_result`. Merge rate = `merged` / (`merged` + `rejected`) over tasks with a determinate outcome; `escalated`, `abandoned`, `harness_fault` and `indeterminate` are excluded from the rate, counted, and reported as harness health. Wall-clock per success reads `wallclock_ms_to_outcome` on `outcome = merged` tasks.

## The threshold-derivation rule

`docs/tier3/autonomy-graduation-policy.md` is a deliberate stub (`evidence: none — written pre-Phase-0 as a register stub (D32)`, `review_after: Phase 4`); `model-routing.json:32` makes it the owner of the entry threshold. The design states the derivation rule from data and writes no number into the stub:

> Threshold (Phase 4, from measurement, not now): the cheap arm's per-task merge rate on the stated fingerprint pair (§2, with its recorded served-field differences), read as a Wilson 95% interval, must clear the capable arm's interval on the same task set by no worse than the declared tolerance; at N_compare = 388 per arm the declared detectable gap is 0.10. Until Phase 4 supplies the number, the placeholder decision rule is K3's 0.50 bar (`charter-and-non-goals.md:87`).

## What stays open

None of the five class-entry checkboxes is satisfied. `trivial_class.members` stays `[]` (`model-routing.json:31`). `gpt-5-nano` runs nothing. No measurement exists. The stub stays a stub. Nothing runs until (1) K3 clears (`charter-and-non-goals.md:87`), (2) a dispatcher exists (`execution-order.md:424`), (3) the paired runs execute on the frozen seed list, (4) the cheap arm's rate is computed as intervals, (5) the threshold is set in `docs/tier3/autonomy-graduation-policy.md`, and (6) the capability enters the trivial class via a protected-path commit.
