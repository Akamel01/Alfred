---
status:        provisional
owner:         human
enforcement:   none
evidence:      A read of ECC2 at ~/.config/opencode/ecc-source/ecc2 — 17 Rust files, ~54,100 lines, self-described alpha — including harness_eval.rs (579 lines), observability/mod.rs's compute_risk, and config's RISK_THRESHOLDS. Comparison is against Alfred's CriterionRunner, ACS-1 evidence chain, held-out isolation by SQL grant, and the Wilson-interval reading in K3.
falsifies_if:  An ECC2 pattern refused here is later adopted because the refusal reasoning was wrong; or Alfred is found importing, vendoring or executing ECC2 code.
review_after:  Phase 2
---

# Ticket #51 — the ECC2 reuse boundary

Resolves [issue #51](https://github.com/Akamel01/Alfred/issues/51). Five decisions, and they
converge on one answer: **adopt nothing, and record why.**

That is a finding rather than a failure to find value. Three of the five questions were closed by
#45 and #47 before this ticket was worked, and the two genuinely open ones fail on the same
property: they produce numbers that look measured and are asserted.

## D1 — The session model is runtime state. There is nothing to adopt

ADR-0047's ownership router:

> **Runtime state** (`.autoforge/`, any ECC or ECC2 store) — Owns **Nothing.** Machine-local,
> gitignored, disposable … never cited by a gate, a verdict, or an audit.

ECC2's SQLite store is runtime state by that row, so its schema shape is not a decision Alfred has
to take. `scripts/lint_state_authority.py` SA002 now fails any gated document that cites it.

## D2 — `harness_eval` is not adopted. Alfred's chain already does this better

Where the two agree, and ECC2 deserves credit: content-addressed candidates, immutable audit rows,
paired evaluation on explicit shared seeds, an atomic pointer swap, rollback on a failed health
assertion. Structurally close to autonomy graduation.

Where Alfred is ahead, and it is not close:

| | ECC2 | Alfred |
|---|---|---|
| Scores | **operator assertions** — its own README says so | `CriterionRunner` executes a criterion outside the agent tree, from trusted provenance |
| Promotion | mean delta + per-seed win rate | held-out criteria behind a separate DB role, materialized at verdict time |
| Integrity | SQLite triggers rejecting update and delete | ACS-1 hash chain, append-only, SQL grants |
| Significance | its README: arithmetic gates **do not establish significance** | Wilson intervals — K3 reads a 95% lower bound, not a point estimate |

Adopting its gate would replace an executed verdict with an asserted one, which is the direction
the whole architecture is built to prevent.

**The one thing worth taking is not code.** ECC2's README states its own limits plainly. That is a
documentation habit, and Alfred already has it in the stub policy and in every `falsifies_if`.

## D3 — The risk score is not adopted and is not displayed

Measured rather than characterized. `observability/mod.rs::compute_risk` sums hand-tuned constants:

```
bash              0.20    "shell execution can modify local or shared state"
write | multiedit 0.15
edit              0.10
anything else     0.05
```

plus substring matches on the input for file sensitivity, blast radius and irreversibility,
compared against `RISK_THRESHOLDS { review: 0.35, confirm: 0.60, block: 0.85 }` hardcoded in
`config`.

It is fully **inspectable** — every constant is readable — and entirely **uncalibrated**. Nothing
derives 0.20, nothing measures whether 0.35 separates anything, and no evidence exists that the sum
orders real risk.

#45 gave risk score no home on the grounds that *writing a home for a fact nothing produces is how
a register starts lying*. This is the stronger case: the fact **is** produced, and it is arbitrary.
A number on an operator surface is read as a measurement, so displaying it would be worse than
omitting it.

## D4 — Alfred's git discipline is the sole authority; ECC2's worktree code goes unused

Land-or-delete and Gate E (per-deletion confirmation for git refs) are decided and carry a human
gate. Two systems managing worktrees is the competing-framework failure §26 forbids, and this
particular pair has a confirmation gate on one side and none on the other.

This effort is its own evidence that the discipline is load-bearing: it produced eight branches and
a stacked PR chain, and the ADR-numbering hazard it navigated — `main` at ADR-0039, the ICM branch
at ADR-0044 — is exactly what unmanaged parallel worktrees cause.

## D5 — Drift detection: pin the commit, check it, nothing more

Because D1–D4 adopt no code, the drift surface is near zero. That is the strongest available form
of §27 compliance rather than an evasion of it.

`docs/tier7/ecc-capability-audit.md` already records ECC 2.2.1 at `ca185ef`. That commit goes into
the install record, and a check asserts the vendored tree still matches it.

If a later decision does adopt an ECC2 pattern, the pattern is **copied with a citation to that
commit** — never vendored, never imported, never built. Drift then shows up as a documentation
diff rather than a build break, which is the only form of drift a single operator can act on.

## Consequences

- Zero lines adopted, zero build dependency, zero upstream drift to track.
- Five refusals are on the record with their reasoning, so the proposals do not return unargued.
- The one genuinely attractive artifact — `harness_eval`'s promotion gate — is refused for a stated
  reason that would reverse if Alfred's own evidence chain were ever weaker than it is today.
- If the operator wants the pattern adopted anyway, the honest route is
  `docs/tier3/autonomy-graduation-policy.md`, a deliberate stub awaiting Phase 4 evidence.
