---
kind: decision
id: "decision:D50"
title: "The oracle is absent from the execution plane by assertion, not by convention"
shape: "table-row"
number: "50"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:89"
extractor: "decisions"
aliases:
  - "D50"
  - "The oracle is absent from the execution plane by assertion, not by convention"
generated: true
---

# The oracle is absent from the execution plane by assertion, not by convention

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:89`

## Statement

**The oracle is absent from the execution plane by assertion, not by convention.** `commonroad-crime` and its transitive closure must be **unimportable inside the agent container**, asserted at sandbox boot beside the egress canary, and the assertion is fail-closed: a run that cannot demonstrate the oracle is absent does not start.

## Fields

**rationale**

> A8's rule is ground truth the agent *did not author* **and cannot retrieve**. The retrieval half has an implemented enforcement (held-out values behind a separate DB role) and an **unimplemented** one: the oracle itself. Grep found no occurrence of the oracle in `sandbox-specification.md`, `protected-paths-policy.md` or `definition-of-done.md`, and Phase 0 is specified to use CriMe as its oracle — so the import is coming and nothing in the register stops it landing in the agent tree. If it is importable, a wrapper delegating to `commonroad_crime` passes the published constants, **every P3 resampled perturbation** (the same code produced them) and **every P4/P5 invariance and degeneracy property** — with a clean transcript and no dishonesty anywhere in the loop. Merge rate would then measure delegation. **This blocks every option equally**, including running the 10 strong tasks unchanged, so it is not downstream of the exit-criterion choice — it is upstream of it. **Consequence if the assertion cannot be made to execute: every merge-rate figure measured to that point is void, not suspect.** **Amended 2026-08-15 (see D54) — the assertion is bounded, and the bound is part of the decision.** D50 as written implies the assertion closes retrieval. It closes four paths and leaves five open, named so no merge-rate figure is read as stronger than it is. *Closed:* the oracle as a declared or transitive dependency; the oracle present but unimported; a vendored copy retaining the module name, a stray `.pth`/`sitecustomize`, or a wheel in a resolver cache; acquisition during the run. *Open, and unclosable by this mechanism:* (a) **reconstruction from model weights** — if the oracle's source or published values sit in the lane's training data the agent reproduces them without importing anything, and this probe cannot measure that; (b) a **renamed, reformatted vendored copy** — the checks are name- and hash-based, never semantic, and a semantic check that worked would itself be an unvalidatable judgment inside the evidence plane; (c) **non-Python paths** — a shared object reached through `ctypes`, a subprocess binary, a data file of constants; (d) a **non-enumerable interpreter** — the probe cannot prove its own enumeration was complete, only fail closed when enumeration errors; (e) a **compromised runtime or base image**, already out of scope in the Threat Model and inherited rather than closed. The visible half of every criterion is deliberately outside this control's scope — visible constants are legitimately in agent context, which is why D49 requires ≥1 held-out grading point per task. **The oracle-absence assertion protects the held-out half only.**

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_oracle_absence|C7 — the oracle is absent, asserted rather than assumed.]] — """C7 — the oracle is absent, asserted rather than assumed.

If `commonroad_crime` is importable where agent-authored co
- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — """Compose one verdict, and keep the held-out half out of the environment that runs.

**The structural decision in this 
- **enforced_by** → [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] — """The structural decision, asserted rather than described.

    The harvest command reads every file in its own directo
- **enforced_by** → [[module__harness_oracle_run|Runs the oracle image. Outside the container, and it never imports the oracle.]] — """Runs the oracle image. Outside the container, and it never imports the oracle.

D54's split is that the oracle's outp
- **enforced_by** → [[module__harness_selftest_synthetic|A criterion with no domain in it, and a defect that can be dialled.]] — # beside the code under test is D50's delegation failure (ADR-0011).
- **enforced_by** → [[module__policy_oracle-denylist_json|policy/oracle-denylist.json]] — "D50/D54. Versioned protected policy configuration; the version is a fingerprint field.",
