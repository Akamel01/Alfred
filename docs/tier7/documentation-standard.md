---
status:        frozen
owner:         human
enforcement:   ci-gate
evidence:      Written pre-Phase-0. Rests on one measured external result (the 49-skill study below) and on the drift hazard this register exists to control.
falsifies_if:  Documents carrying a valid header drift as badly as documents without one — i.e. a sampled audit at the end of Phase 1 finds no difference in staleness between headed and unheaded documents.
review_after:  Phase 1
---

# Documentation Standard

This document defines what a document in Alfred is, what makes it trustworthy, and
what stops it from lying. Every other document in the register conforms to it.

## Why this exists

Documents that describe a system drift from it. In a company where agents read
documentation as context, a stale document is not merely unhelpful — it is a
corrupted instruction propagating into every task that reads it. That is the same
hazard class as an agent writing its own verdict, and it is controlled the same
way: by making the document answerable to something outside itself.

The evidence is not neutral on this. A study of 49 agent skills found 39 produced
**zero improvement**, average +1.2%, with up to 451% token overhead — and three
**degraded** performance by up to −10% from version-mismatched guidance. The seven
that helped (up to +30%) did so conditioned on domain alignment and **currency**.
The downside of a wrong document is negative, not zero. A document written before
the evidence exists cannot be current by construction, which is why this standard
is built around declaring that fact rather than hiding it.

## Classification: by what stops it from lying

Documents are classified by enforcement mechanism, never by topic.

| Kind | Source of truth | Drifts? |
|---|---|---|
| **Executable spec** — schemas, policies, agent definitions, protected paths, thresholds | YAML/Pydantic loaded by the harness | No — violation fails CI |
| **Generated** — API reference, metric catalog, port catalog | Derived from code or registry, never hand-edited | No — regenerated on build |
| **Immutable record** — ADRs, postmortems, evaluation reports, benchmark runs | Append-only, dated, never revised | No — historical claims |
| **Living prose** — charter, objectives, boundaries, guides | Human-written | **Yes** — the only category that rots |

**Rule: every document declares its enforcement mechanism. No mechanism means it
must be small and human-owned.**

The corollary drives most of the register's shape: a security protocol in markdown
is a wish; the same rules in `policy.yaml` loaded by `PolicyEngine` are a control.
An agent definition guide is advice; an agent definition *schema* is a contract.
Push everything possible into the executable category. The target is roughly 60% of
the register executable or generated rather than prose.

## The header contract

Every document opens with YAML frontmatter:

```yaml
status:        frozen | provisional | directional
owner:         human | generated | executable
enforcement:   ci-gate | schema | generated | review-cadence | none
evidence:      <what this is based on, or "none — written pre-Phase-N">
falsifies_if:  <observation that would invalidate this document>
supersedes:    <doc id, if any>
review_after:  <phase or date>
```

`status` matches the port fidelity levels used in the system blueprint:

- **frozen** — fully specified and committed. Changing it is a breaking change.
- **provisional** — shape and responsibility specified, expected to move. Safe to
  design against, not safe to depend on.
- **directional** — the seam is named and the constraint it must satisfy is stated.
  No signatures. Writing signatures before observing real failures produces
  confidently wrong contracts, which are worse than none.

`evidence: none — written pre-Phase-N` is an honest and expected value. Without the
field, speculation is indistinguishable from two hundred observed runs.

`falsifies_if` is **required whenever `evidence` is empty**. This is the mechanism
that makes writing documents early a net gain rather than a liability: it converts
the register from a pile of speculation into a scored set of predictions. A document
that cannot state what would prove it wrong is not yet a document — it is a wish,
and it should be a stub instead.

## Stubs are the default

Per D32, the full register is written as **stubs**; full content is reserved for the
documents the current phase can actually falsify. A stub is:

1. the header contract, complete and honest,
2. a two-sentence statement of purpose,
3. the enforcement mechanism it will have,
4. the falsification condition,
5. an expiry.

Stubs preserve the complete map, the schema, and the uniformity of the register while
keeping speculation out of agent context. A stub costs minutes. A wrong full document
costs whatever it corrupts downstream.

## Authorship boundary

Agents may produce **generated** and **executable** documents — both have ground truth
(the code, the CI gate). Agent-written prose has none and is therefore unvalidatable
output of exactly the kind Alfred's architecture exists to prevent.

**Tier 0 remains human-authored permanently.** This is not a new policy; it is the
organizing principle applied to documentation: *autonomy tracks the availability of
ground truth the agent did not author and cannot retrieve.*

## Location and change control

Documentation lives in this repository, versioned with the code, changed through pull
requests, and reviewed under the same protocol as code. A wiki or a documentation site
held elsewhere is a drift generator by construction.

## CI enforcement

The doc lint is a Phase 0 deliverable. It fails the build when:

- a document under `docs/` lacks frontmatter, or carries an unknown key;
- `status`, `owner`, or `enforcement` holds a value outside its enumeration;
- `evidence` is empty or begins with `none` and `falsifies_if` is absent;
- `review_after` names a phase that has already exited (a stale review commitment is
  a broken promise, and it is machine-detectable);
- a document declares `owner: generated` but is not produced by a generator registered
  in the build.

The lint checks the contract, never the prose. Nothing here can verify that a document
is *true* — only that it has declared what would show it false, and to whom it answers.

## Writing order

Dependency-ordered, not tier-ordered:

1. **Documentation Standard** (this document) — defines the contract every other uses
2. **Tier 0 constitution** — five short human-owned documents
3. **Schemas across Tiers 1–3** — agent definition, task specification, tool
   specification, criterion, state/graph, stage gates
4. **Tier 4** — security and governance
5. **Remaining prose**
6. **Generated documents last** — they require the code to exist
