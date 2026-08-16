---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      Append-only defends against the agent and not against hardware failure, kernel-panic corruption, or a bad migration. For an audit-layer product, an unchained audit log is rewritable by anyone holding one login.
falsifies_if:  A restore drill fails, a chain-head anchor is missing for any day, or an evidence row is found whose hash does not match its predecessor link.
review_after:  Phase 2
---

# Audit and Retention Policy

The product sells reproducibility. Its own records therefore have to be the most
trustworthy thing it owns.

## Append-only

Evidence and state transitions are append-only. No destructive updates, no deletes.
Evidence migrations are additive-only — never `ALTER` or `UPDATE` of existing rows —
CI-linted.

Replay, provenance and audit cannot be added later. They must be inherent, and retrofit
is a rewrite.

## Hash chaining

Each evidence row carries `prev_sha256` and its own `sha256`, computed over its content
plus its predecessor's hash. The chain head is **anchored off-machine daily**.

Append-only is an integrity property against the agent. The chain is what survives an
operator-level compromise, a bad migration, or corruption — anything that can write to
the database directly. Without it, the audit log of an audit product is silently
rewritable by anyone with one login, undetectable by construction.

A memoization hit is recorded as an event in the chain, so replay stays faithful: a
verdict reused from an exact-fingerprint match must be distinguishable from a verdict
freshly computed.

## What is recorded

Per run: task, resolved context, prompt and its version, every file read and search
issued, tool-call trace, diff, check output, wall-clock, latency, turn count, token
spend, verdict, and the full fingerprint.

Per emitted product result: metric version, code commit, assumption set, input hash,
tolerance.

Per human action on a held-out artifact: who read it and when. Reading held-out material
is legitimate and must be visible.

## Backup and restore

Continuous WAL archiving plus periodic base backups of Postgres **and** the artifact
store, to an off-machine target.

**The restore drill is an executable check.** "Restore verified" is a Phase 0 exit
criterion sitting beside "deploy and rollback verified". A backup that has never been
restored is a belief, not a control.

Single-machine risk carries a recovery objective and a trigger in the Risk Register:
first paying customer or first autonomy grant moves the control plane off the inference
host.

## Retention

Evidence is retained indefinitely — it is the substrate for replay, autonomy grants, and
any future audit claim. Artifacts are content-addressed and deduplicated, so retention
cost grows with distinct content rather than with run count.

Anything that must eventually be removed for legal reasons is removed by **tombstone plus
artifact deletion**, never by mutating the chain. The chain records that a removal
occurred, so the audit trail remains verifiable across it.

## Recall

A defect in an emitted result triggers a versioned advisory naming affected metric
versions and date ranges. Because result stamping is complete, affected results are
identifiable from a version and date range alone — which is what makes the advisory model
work without holding customer data, and therefore compatible with a
customer-deployed product.

A synthetic recall exercise — identifying affected results from a version and date range
— is part of Phase 0 verification. If the exercise cannot be performed, stamping is
incomplete, and stamping cannot be retrofitted: results computed before it exists are
permanently unrecallable.

Customer-deployed delivery additionally requires signed images, a machine-readable
advisory feed or contractual notification with quarterly version-manifest return, and a
contractual clause obliging customers to apply correctness advisories. Without those, the
recall protocol is hollow in exactly the deployment mode that justifies it.
