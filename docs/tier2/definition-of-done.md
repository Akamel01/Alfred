---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      Each condition corresponds to a control this architecture depends on. The pre-review scan exists because CI runs before any human sees a pull request, so review is not the first gate.
falsifies_if:  A change merges with any condition below unmet, or a defect reaches merge that one of these conditions would have caught.
review_after:  Phase 2
---

# Definition of Done

The merge gate. Every condition is executable, so "done" is never a judgment call.

## Conditions

A change may merge only when all of the following hold.

**1. Patch validation passed.** The diff touches no protected path, no `.github/`, no
CI configuration, no hooks, and no harness directory. Validation runs on the privileged
side, outside the container, by parsing the diff's file list — not inside the
environment that produced it.

**2. Pre-review scan passed.** No non-ASCII control, zero-width or bidi characters
outside declared string literals, with particular force on agent-instruction files. No
additions of `.pth`, `sitecustomize`, or instruction files. Dependency closure resolves
to pinned hashes.

**3. Static gates green.** `ruff` clean. `pyright --strict` clean with zero
suppressions, or with a suppression carrying a recorded justification.

**4. Visible criterion green**, executed by `CriterionRunner` on a clean checkout
materialized from trusted provenance — never in the agent's tree.

**5. Held-out criterion green.** Materialized at verdict time from the `heldout` schema
by `alfred_criterion`. The agent never saw it and never retried against it.

**6. Property tests green**, including properties over *composed* operations. This is
the load-bearing correctness control, not secondary hardening.

**7. Null-agent floor test still at floor.** A run taking no actions scores what it
should. Above floor means the harness is measuring itself.

**8. Seeded-defect suite still reds.** Deliberately wrong implementations at known
deltas must fail. The inspector's inspector.

**9. Result stamping intact.** Every emitted result carries metric version, code commit,
assumption set, input hash and tolerance.

**10. Evidence written by the harness**, hash-chained, with the run's read log recorded.

**11. Human review complete**, criterion-first. The reviewer checks what the harness
structurally cannot: whether the criterion was the right criterion, whether the agent
solved the stated problem or a nearby easier one, future coupling cost, and whether a
metric's validity envelope is honestly stated.

**12. Deterministic replay verified** for any change touching the replay path —
byte-identical results across runs.

## What is deliberately absent

**Mutation score.** It has no gating role anywhere in Alfred. Mutants are generated from
the possibly-buggy code, and tests failing on the original are excluded — which excludes
precisely the bug-exposing tests. In a bug-detection setting the resulting scores are
meaningless. `mutmut` survives only as regression on the trusted human-built skeleton.

**Any LLM judgment.** The advisory judge may raise an escalation and may flag suspected
reward hacking. It is schema-forbidden from writing any verdict field, and it can only
*add* escalations — it can never be the reason one did not fire.

## Overriding

A merge that skips any condition requires an immutable waiver ADR recording the
condition, the reason, the actual state, and what would reverse it. Waiver count is a
health metric in its own right.
