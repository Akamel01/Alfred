---
status:        provisional
owner:         human
enforcement:   none
evidence:      A read of the frozen task specification standard, the Worker port contract's WorkerSpec, the handoff contract stub, and AutoForge's spawn-contract.md, against the FactoryFingerprint added in this effort. No task has been dispatched through the contracts named here; the seam is read off documents that already bind, not off an observed dispatch.
falsifies_if:  A third document is found describing what an agent is handed; or a factory run is found crossing the Worker port, meaning D2 drew the boundary in the wrong place.
review_after:  Phase 2
---

# Ticket #44 — the canonical task contract

Resolves [issue #44](https://github.com/Akamel01/Alfred/issues/44). Five decisions.

## The reframe

The ticket says *"four partial answers exist and none is canonical."* Half of that is wrong,
and the half that is wrong is the important half. **Two of the four are canonical and binding
today**, and they already cut the seam §10 asks for.

## D1 — Two contracts, and both homes are already occupied

| Object | Home | Status |
|---|---|---|
| **Task** — what the work *is* | `docs/tier2/task-specification-standard.md` § *Required fields* | frozen, `enforcement: schema` |
| **Session** — what a runtime invocation is *handed* | `docs/tier1/worker-port-contract.md` → `WorkerSpec` | full, `enforcement: schema` |

`WorkerSpec` carries `run_id`, `task_id`, `attempt_id`, `attempt_index`, `fingerprint`, `seed`,
`seed_layers`, `read_mounts`, `write_mount`, `tools`, `budget`, `timeouts`, `schema_version`.

**No new home for either.** AutoForge's `spawn-contract.md` is a prose template with no schema;
every one of its ten fields maps onto a field one of these two already carries.

## D2 — Factory runs do not cross the Worker port

`WorkerSpec.fingerprint` is typed `RunFingerprint`. This effort added `FactoryFingerprint`
(`harness/fingerprint/factory.py`) because `RunFingerprint` cannot describe an API-served agent —
its lane and D40 groups are self-hosted-inference fields. **So a factory agent cannot construct a
valid `WorkerSpec` today.** The collision is real and this effort created it.

**Decision: the Worker port stays exactly as it is, and factory runs use a different path.**

The port's own text is the argument:

> There is no `credentials` field, no `network` field and no `env` field. **Their absence is the
> contract.**

That contract exists to run untrusted candidate code against a held-out oracle, under mounts, an
egress canary and SQL-grant isolation. An agent editing this repository is a different activity,
and forcing it through would either weaken the door or produce a second door wearing its name.

**Rejected: widen the field to a union.** Every consumer then branches, and a sealed boundary
with a case split in it has two ways to get it wrong.

**Rejected: extract a shared protocol.** Technically clean — the D19 group is already shared
verbatim and mechanically asserted by `d19_is_shared()` — and it still makes one door serve two
activities with different threat models. Kept on the record as the fallback if D2 proves wrong.

**The honest cost.** Factory work has no sandbox. It runs against the real repository with the
protected set and Gate D as its only containment. That is the existing situation, not a new
exposure, but D2 is the first record that says so out loud.

## D3 — Pydantic in the control plane, no JSON Schema twin

`task-specification-standard.md` already says *"Enforced by Pydantic validation in the control
plane, not by review"*, and `WorkerSpec` is already dataclasses under `harness/`. A JSON-Schema
mirror would be a second authority for one shape, and the register's rule is one home per fact.

**Is the contract hashed into the evidence chain?** It already is, sufficiently and indirectly:
`attempt_start` carries `fingerprint_sha256` and `tree_sha256`, and `control.work` carries
`capability_id` set at dispatch. Hashing the contract itself would add a third identity for one
dispatch.

## D4 — Acceptance criteria are executable, and there is no override

Nothing to decide. The frozen standard already forecloses it:

> **A task is only schedulable if it carries an executable acceptance criterion.** Prose-only
> tasks are not tasks. They fail validation, are marked unschedulable, and escalate to a human
> for criterion authoring. **There is no override.**

Free text is not an option the register leaves open. `CriterionRunner` executes the criterion
outside the agent's tree, from trusted provenance.

## D5 — `handoff-contract-standard.md` graduates, narrowly, as the third contract

It describes neither the task nor the session. Its purpose line names a third object: *"What
passes between nodes: content-addressed evidence refs, never agent-authored summaries."* That is
the **phase boundary**, which #42 and #45 have now defined.

Its falsification condition — *"A handoff carries prose the successor relies on without reading
the underlying artifact"* — is already mechanically impossible: `phase_end.artifact_ref` is a
hash, never a path (I3). The document is being written to describe an enforcement that exists,
which is the opposite of the stub policy's hazard.

**Stated plainly: this graduates a document whose own header says `review_after: Phase 3`.** The
justification is that the evidence it was waiting for arrived early, from #42 and #45. If that
reads as impatience rather than readiness, the alternative costs nothing — `phase_end.artifact_ref`
enforces the rule whether the document is written or not.

## Consequences

Three contracts, three homes, no overlap:

```
task    → docs/tier2/task-specification-standard.md   what the work is
session → docs/tier1/worker-port-contract.md          what a run is handed
handoff → docs/tier3/handoff-contract-standard.md     what crosses a phase
```

D2 leaves the Worker port untouched, so nothing that exists today changes behaviour.
