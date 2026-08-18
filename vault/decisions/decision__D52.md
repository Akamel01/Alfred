---
kind: decision
id: "decision:D52"
title: "The `Worker` port returns a claim or raises; it never returns a verdict, and it never returns `indeterminate`"
shape: "table-row"
number: "52"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:93"
extractor: "decisions"
aliases:
  - "D52"
  - "The `Worker` port returns a claim or raises; it never returns a verdict, and it never retu"
generated: true
---

# The `Worker` port returns a claim or raises; it never returns a verdict, and it never returns `indeterminate`

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:93`

## Statement

**The `Worker` port returns a claim or raises; it never returns a verdict, and it never returns `indeterminate`.** Agent-attributed terminations (`agent_stopped`, `budget_exhausted`, `policy_violation`, `aborted`) are claim values; every executor- or harness-attributed termination is an exception (`ContainmentFailure`, `WorkerFault`, `ClaimIncomplete`) whose class determines the verdict. The claim type and its transitive closure are lint-forbidden from declaring any verdict-vocabulary field name. `dispatch` takes a `SandboxHandle` carrying an assertion report and refuses when any required assertion is absent or not `passed` — **`not_executed` is a failure, never a pass.** Read recording (D26) is an obligation on the adaptor, derived from the executor's event stream, with completeness demonstrated by the durable event count. An adaptor is admitted only on four demonstrations: assertion coverage, instrumentation completeness against a scripted-agent suite, fault fidelity under injected faults, and a declared epoch boundary.

## Fields

| Field | Value |
|---|---|
| `rationale` | The architecture's central claim is that the harness produces facts and the agent produces claims; that survives only if a worker which could not be shown to have run says so instead of returning something verdict-shaped. **The most likely defect in any adaptor is reporting a killed executor as an agent failure**, which silently moves harness flakiness into the numerator of the only number the aut |
