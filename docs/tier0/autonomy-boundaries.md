---
status:        provisional
owner:         human
enforcement:   ci-gate
evidence:      Boundary placement derives from the organizing principle and from measured task-class stratification. The specific thresholds are unset — they require Phase 1-2 data that does not exist.
falsifies_if:  A task class inside the boundary shows a defect-escape rate materially above a class outside it, meaning the boundary is drawn on the wrong property.
review_after:  Phase 4
---

# Autonomy Boundaries

What agents may do, what they may never do, and what governs movement between the two.

## The test

For any candidate task: **what independent thing says this is right?**

An answer that is external, pre-existing, and unretrievable by the agent means the task is
inside the boundary. No answer means it is human work — not yet, and possibly never.

## Permanently outside the boundary

No measurement moves these. They are not "not yet"; they are structural.

| Area | Why |
|---|---|
| The inspector — `CriterionRunner`, `EvidenceStore`, `PolicyEngine`, `AutonomyGate`, fingerprint tracker, protected-path config, sandbox spec | Every safeguard assumes the judge is independent of the worker. An agent editing the judge collapses all of them at once, silently, with tests green — because the tests are downstream of the edit. |
| Evidence, verdict and policy migrations | Same boundary, expressed in schema. Evidence tables are additive-only; never `ALTER` or `UPDATE` of existing rows. |
| Threshold selection | Contested judgment with no standard. Only threshold *application* is checkable. |
| The proprietary risk formulation and its calibration | No external check exists. A wrong number here does not crash, spike latency, or fail a healthcheck — it looks fine. |
| Tier 0 documentation | Prose with no ground truth. Unvalidatable output of exactly the kind this architecture exists to prevent. |
| Production credentials, deploy authority, VCS credentials | Blast-radius containment. The worst case from a fully compromised agent must remain a pull request that gets declined. |

## Inside the boundary today (Phase 1 class)

**"Implement surrogate safety metric M per its published specification, matching reference
values on dataset D."** External spec, external verification, bounded scope.

This class qualifies because the specification pre-exists the agent, the reference values were
computed by someone else, and the agent can neither author nor retrieve them at verdict time.

## The containment model

```
control plane (Postgres, deterministic)
      │ dispatches
execution plane (ephemeral container, untrusted, network deny-by-default)
      │ emits a patch file to a mounted volume
gate: patch validation → criteria on clean checkout → held-out → human review → merge
```

Non-negotiable properties:

- **No VCS credential inside the container.** The container emits a patch; a separate,
  uncontaminated process validates it and opens the pull request. The deliverable channel and
  the exfiltration channel must not be the same channel.
- **Network deny-by-default with an allowlist**, enforced by `nftables` default-drop, not by
  environment-variable proxy configuration. An egress canary attempts a known non-allowlisted
  connection on every sandbox boot; the run refuses to start unless it fails.
- **Read paths fixed by the harness at dispatch** and enforced by the filesystem mount — never
  chosen by the agent mid-run.
- **No production credential and no secret-bearing environment variable** in the sandbox,
  asserted at startup.

## Graduation

Movement into unattended operation is per task-class, never per category. "Tests are safe" is a
category judgment and is forbidden as a basis.

A grant requires all three, on a recorded fingerprint:

1. measured **per-task merge rate** after the bounded retry budget,
2. **held-out composed criterion pass rate**,
3. measured **defect-escape rate**.

An autonomy grant therefore reads: *"X% merge, Y wall-clock per success, on fingerprint Z."*

## Revocation

Grants are suspended automatically on any fingerprint change, tiered by what changed:

- prompt or context strategy → smoke subset
- serving stack or lockfile → smoke subset plus tool-calling probes
- weights, quantization, or orchestrator → full golden set

An **orchestrator change is a criterion-set epoch boundary**: prior grants invalidate and
historical cost-per-merged-task becomes incomparable.

Grants also expire. A criterion set carries a version *and* an expiry, because criterion sets rot
— two professionally maintained ones went stale within six months.

## Known exposure, accepted

Agents may create subtasks freely, each receiving its own budget allocation. This makes budget
ceilings advisory: an agent approaching its cap can split into subtasks that each receive fresh
budget. No malice is required — it is the locally rational move under a constraint.

A global tree cap would have preserved the same freedom while bounding total spend. Its absence is
a deliberate trade for throughput. Recorded in the Risk Register with a revisit trigger: the first
observed decomposition tree exceeding expected spend by 5×.
