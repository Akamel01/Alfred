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

Per emitted product result: the ten-key result stamp (ADR-0006) — `stamp_schema_version`,
metric id and version, code commit, assumption set, input hash, tolerance, reason-codebook
version, ACS-1 version, and the `upstream` toolchain arm.

**The upstream configuration is committed by digest and retrieved by reference, and both
halves are obligations.** The `simulated` arm's `config_digest` proves the configuration was
not altered; only `config_ref` lets anyone reproduce anything. So: **a `config_ref`'s
preimage remains retrievable for as long as the stamp that names it is live.** A digest whose
preimage has been garbage-collected is a stamp that verifies while discharging nothing, and
the buyer's duty under EU 2022/1426 Annex III Part 4 is traceability from output back to
setup, not a hash of a setup nobody can produce. `config_ref` is optional in the schema and
**required by this policy wherever re-derivation is claimed**.

An `upstream` arm of `unknown` is recorded, never suppressed. It means there *was* an
upstream toolchain and Alfred could not determine it, so the stamp does not discharge the
storage duty; `discharges_storage_duty` is `False` and a count of such stamps is a defect
count rather than a rounding error.

Per human action on a held-out artifact: who read it and when. Reading held-out material
is legitimate and must be visible.

## Backup and restore

Continuous WAL archiving plus periodic base backups of Postgres **and** the artifact
store, to an off-machine target.

**The restore drill is an executable check.** "Restore verified" is a Phase 0 exit
criterion sitting beside "deploy and rollback verified". A backup that has never been
restored is a belief, not a control.

**The drill includes a stamp case, and it is a two-part assertion.** For a restored result:
its stamp verifies through the two-stage read — `verify_stamp` returns `VERIFIED`, not
`UNVERIFIABLE` — **and** every `config_ref` it names is still retrievable from the restored
target. Restoring the digest without the preimage restores the claim and loses the
reproduction, which is the half a green exit code does not notice. A drill asserting only the
first half passes on a backup that has quietly dropped every upstream configuration.

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
