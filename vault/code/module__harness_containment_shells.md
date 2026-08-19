---
kind: module
id: "module:harness.containment.shells"
title: "The executor-premise assertions, and the source read that filled their holes (O5)."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/shells.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The executor-premise assertions, and the source read that filled their holes (O5)."
  - "harness.containment.shells"
generated: true
---

# The executor-premise assertions, and the source read that filled their holes (O5).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/shells.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/shells.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """The agent is running in the container at all.

    **Every other executor-premise assertion assumes this and none of 
- [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]] **enforced_by** → this — """The executor-premise assertions, and the source read that filled their holes (O5).

C1, C2, C3, C5 and C10 rest on th
- [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]] **enforced_by** → this — # and rejected rather than overlooked (ADR-0018).
- [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]] **enforced_by** → this — "resolved 2026-08-18; see ADR-0018"
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **enforced_by** → this — """Persistence configured, and every observed event durable at end of run.

    **The premise inverted at O5.** The rese
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **enforced_by** → this — """The agent is running in the container at all.

    **Every other executor-premise assertion assumes this and none of 
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **enforced_by** → this — """The ingress surface and the launch posture — the half of ADR-0019 nothing covered.

    ADR-0019 recorded four unhard
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **enforced_by** → this — "Not in the specification, and it falsified C1 as written (ADR-0019). It "
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **enforced_by** → this — "ADR-0019; not re-read here, and the citation is what makes that checkable."
- [[decision__D35|hard constraint]] **enforced_by** → this — "put the run on somebody else's machine, which D35 forbids outright. "
- [[decision__D38|Decision 9's named harness (Claude Agent SDK) demoted to provisional]] **enforced_by** → this — # Pinned here only so that a future reader who finds this name in D38 can see it was checked
- [[decision__D38|Decision 9's named harness (Claude Agent SDK) demoted to provisional]] **enforced_by** → this — "D38 names OpenHands/OpenHands. At 1916c904 that repository is 'Agent Canvas', "
- [[decision__D53|Executor containment is fifteen numbered boot assertions, split by placement, and the `Wor]] **enforced_by** → this — """Persistence configured, and every observed event durable at end of run.

    **The premise inverted at O5.** The rese
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """The ingress surface and the launch posture — the half of ADR-0019 nothing covered.

    ADR-0019 recorded four unhard
