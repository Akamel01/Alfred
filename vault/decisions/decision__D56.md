---
kind: decision
id: "decision:D56"
title: "Defect-escape recording starts at the first merge, not at Phase 4"
shape: "table-row"
number: "56"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:101"
extractor: "decisions"
aliases:
  - "D56"
  - "Defect-escape recording starts at the first merge, not at Phase 4"
generated: true
---

# Defect-escape recording starts at the first merge, not at Phase 4

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:101`

## Statement

**Defect-escape recording starts at the first merge, not at Phase 4.** `evidence.defect_escape` records, at *discovery* time, the task that introduced a defect, the fingerprint it was merged under, how it was found, and the basis of the attribution (`bisect` · `criterion_replay` · `operator_judgment`). Corollary, and the reason this is a decision rather than a schema note: **an empty defect-escape table is not a zero defect-escape rate.** The gate reads merged tasks under observation for **a stated window** as its denominator, because a grant issued on a count is a grant issued on how recently anyone looked. An attribution by `operator_judgment` and one by `bisect` are different measurements, and a rate that mixes them without saying so is not a rate. **The window is an operator input and is unstated as of 2026-08-17**, which leaves the 2026-12-31 anchor's pass condition unevaluable until it exists.

## Fields

**rationale**

> Three of `AutonomyGate`'s four inputs are already emitted by the Phase 1 instrumentation; the defect-escape rate is not — and unlike the others it cannot be reconstructed from history, because nothing in a merged history distinguishes a clean merge from one nobody has looked at yet. A gate built in Phase 4 against a table that started in Phase 4 has no denominator.

## Enforced by (code)

- **enforced_by** → [[module__migrations_harness_evidence_versions_0001_evidence_base|evidence: run records, verdicts, operator actions, artifacts, defect escapes.]] — # `defect_escape` is here because D56 starts it at the first merge, and because nothing
