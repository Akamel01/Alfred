---
kind: adr
id: "adr:ADR-0007"
title: "Executor-premise assertions may pass vacuously, and that is a third outcome"
status: "accepted"
shape: "heading"
date: "TBD"
source: "docs/tier1/adr-log.md:780"
extractor: "adrs"
aliases:
  - "ADR-0007"
  - "Executor-premise assertions may pass vacuously, and that is a third outcome"
generated: true
---

# Executor-premise assertions may pass vacuously, and that is a third outcome

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:780`

## Statement

**Date:** TBD · **Status:** Accepted · **Supersedes:** none

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- [[adr__ADR-0017|A containment assertion with an unread premise is a hole, and a hole never passes]] **amends** → this
- [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]] **see_also** → this
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **see_also** → this
- [[adr__ADR-0020|The run fingerprint record, and the two assertions that were waiting on it]] **see_also** → this
- [[adr__ADR-0029|The tree that verifies every other tree is verified by nothing]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — from a clean tree. That is the ADR-0007 vacuity class in the tooling, and it is how
- **enforced_by** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]] — """Three outcomes for a containment assertion, and the third is the dangerous one.

`passed` and `failed` are obvious. *
- **enforced_by** → [[module__harness_containment_handle|The one crossing from probe vocabulary to handle vocabulary.]] — """The one crossing from probe vocabulary to handle vocabulary.

Two `Assertion` types exist and both are right. `harnes
- **enforced_by** → [[module__harness_containment_lane|C11 — the serving lane is the lane the run was dispatched against.]] — """C11 — the serving lane is the lane the run was dispatched against.

Runs **outside**, against the serving layer. The 
- **enforced_by** → [[module__harness_containment_patch_side|C15 — the oracle arriving through the deliverable channel.]] — # Clause 3 not running is not an unverified *premise* in ADR-0007's sense, but it is
- **enforced_by** → [[module__harness_containment_reassert|C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.]] — # ADR-0007 exists to keep visible.
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — """The agent is running in the container at all.

    **Every other executor-premise assertion assumes this and none of 
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """C1–C15 beyond the two probes, each paired with the control that stops it reading green.

**How this suite would be sh
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """ADR-0007 as a single assertion, and it survives O5.

    The holes are answered now, so this resets one and checks th
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """The vacuity demonstration, and the whole argument for the assertion.

    Nothing about this observation is in a cont
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """ADR-0007's admissibility split, and the reason the flag crosses the boundary."""
- **enforced_by** → [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]] — """ADR-0007: an assertion may be executed, passed, and vacuous.

    Not representable in the three-valued outcome, so i
- **enforced_by** → [[module__harness_oracle_fingerprints|Runs INSIDE the oracle image. Emits digests and names, and never the source itself.]] — """Runs INSIDE the oracle image. Emits digests and names, and never the source itself.

Two jobs, both of which need the
- **enforced_by** → [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]] — """Carries oracle values across the boundary as data, and refuses when they are not clean.

The oracle's code never cros
- **enforced_by** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]] — # ADR-0007's third outcome, carried across the boundary rather than left on the probe.
- **enforced_by** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]] — """What the run is for, which decides how an unverified premise is treated.

    ADR-0007: a run whose containment rests
- **enforced_by** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]] — """Refuse to dispatch unless every required assertion is present and passed.

    `admissibility` defaults to `MEASUREME
- **enforced_by** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]] — "merely misnamed (ADR-0007). Admissible for build work, not as a "
- **enforced_by** → [[module__harness_worker_test_port|The Worker port's structural refusals, and the control on the check that enforces them.]] — """A worker that requires nothing has been configured to check nothing, and from
    outside that is indistinguishable f
- **enforced_by** → [[module__policy_oracle-denylist_json|policy/oracle-denylist.json]] — "the vacuity ADR-0007 named. They are now read from importlib.metadata inside the pinned",
- **enforced_by** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]] — """How much of `harness/` the lint gate actually collects, and whether it can go red.

`harness/` is the tree everything
