---
kind: module
id: "module:harness.worker.port"
title: "The `Worker` port. A claim crosses it, or an exception does — never a verdict."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/worker/port.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The `Worker` port. A claim crosses it, or an exception does — never a verdict."
  - "harness.worker.port"
generated: true
---

# The `Worker` port. A claim crosses it, or an exception does — never a verdict.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/worker/port.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/worker/port.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- [[module__harness_worker|harness.worker]] **contains** → this
- [[module__harness_containment_handle|The one crossing from probe vocabulary to handle vocabulary.]] **imports** → this
- [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] **imports** → this
- [[module__harness_containment_test_outcome_binding|The two assertion-outcome enums are bound, though deliberately separate.]] **imports** → this
- [[module__harness_verdicts_test_verdicts|The verdict vocabulary's bindings: every other spelling answers to this module.]] **imports** → this
- [[module__harness_worker_adapters_open_hands|OpenHands adaptor implementing the `Worker` protocol over the pinned SDK.]] **imports** → this
- [[module__harness_worker_adaptor|Alfred OpenHands Adaptor — the Worker implementation for the OpenHands executor.]] **imports** → this
- [[module__harness_worker_fake|The in-memory `Worker`: a scripted stand-in that rehearses the seam's semantics.]] **imports** → this
- [[module__harness_worker_provisioning|Provisioning for the OpenHands adaptor runtime.]] **imports** → this
- [[module__harness_worker_test_fake|Rehearsals of the `Worker` seam against the in-memory adaptor — interface only.]] **imports** → this
- [[module__harness_worker_test_port|The Worker port's structural refusals, and the control on the check that enforces them.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — # ADR-0007's third outcome, carried across the boundary rather than left on the probe.
- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """What the run is for, which decides how an unverified premise is treated.

    ADR-0007: a run whose containment rests
- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """Refuse to dispatch unless every required assertion is present and passed.

    `admissibility` defaults to `MEASUREME
- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — "merely misnamed (ADR-0007). Admissible for build work, not as a "
- [[decision__D26|Context = deterministic seed + free agent search + full read-recording]] **enforced_by** → this — """D26, and it is positive evidence only.

    Derived by the adaptor from the executor's action/observation stream, nev
- [[decision__D45|Caching: three layers, two adopted, one rejected]] **enforced_by** → this — """One layer of the context seed, ordered most-stable-first (D45).

    Prefix order is architecture rather than tuning:
