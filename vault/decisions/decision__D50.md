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

| Field | Value |
|---|---|
| `rationale` | A8's rule is ground truth the agent *did not author* **and cannot retrieve**. The retrieval half has an implemented enforcement (held-out values behind a separate DB role) and an **unimplemented** one: the oracle itself. Grep found no occurrence of the oracle in `sandbox-specification.md`, `protected-paths-policy.md` or `definition-of-done.md`, and Phase 0 is specified to use CriMe as its oracle — |

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_oracle_absence|C7 — the oracle is absent, asserted rather than assumed.]] — """C7 — the oracle is absent, asserted rather than assumed.

If `commonroad_crime` is importable where agent-authored co
- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — """Compose one verdict, and keep the held-out half out of the environment that runs.

**The structural decision in this 
- **enforced_by** → [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] — """The structural decision, asserted rather than described.

    The harvest command reads every file in its own directo
- **enforced_by** → [[module__policy_oracle-denylist_json|policy/oracle-denylist.json]] — "D50/D54. Versioned protected policy configuration; the version is a fingerprint field.",
