---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      A pull-request-opening flow has been used to exfiltrate a token within eight minutes of the PR being opened. Repository-scoped CI caches survive container ephemerality, so ephemerality alone does not contain a leaked secret.
falsifies_if:  Any credential is found reachable from agent context, or a secret is discovered outside the declared inventory.
review_after:  Phase 2
---

# Secrets Management Policy

## The rule

**No secret ever enters the execution plane.** Not scoped, not read-only, not
short-lived. None.

This is stronger than least privilege because the containment argument depends on it: the
worst case from a fully compromised agent must remain a pull request that gets declined.
A single credential inside the container converts that into an exfiltration event.

## Storage

Secrets live in the macOS Keychain, or in `age`/`sops`-encrypted files with per-secret
scope. Never in environment files, never in the repository, never in shell history.

Each secret carries a declared scope, an owner, a rotation date, and the single process
permitted to read it. The inventory is CI-linted: a secret in use without an inventory
entry fails the build.

## Scoping

| Secret | Scope | Held by |
|---|---|---|
| VCS token | fine-grained, PR-open on one repository, no push to protected refs | the patch-validation process only |
| Database credentials | per-role, per-schema | the harness and criterion processes |
| Backup target credentials | write-only to the off-machine target | the backup process |
| Dataset licence credentials | read-only | the ingest process, outside agent reach |

The VCS token is deliberately the narrowest thing that can still do the job. It cannot
push to protected refs, and it never leaves the uncontaminated process.

## Startup assertions

The harness refuses to start a run unless:

- no secret-bearing environment variable exists in the sandbox environment
- the container holds no database credential
- the egress canary confirms Postgres is unreachable from the container
- no user or project settings file has been loaded into the agent's configuration

That last assertion exists because a control of exactly this kind has already failed
silently in a shipped SDK: an empty settings-source list was treated as omitted, and user
configuration loaded anyway.

## CI

Agent branches cannot trigger secret-bearing workflows. `GITHUB_TOKEN` is read-only by
default. Workflows never check out an untrusted head with elevated permissions.
`actions/cache` is disabled on any workflow touching agent branches — caches are
repository-scoped, so ephemerality fails below the container.

## Rotation and incident response

Rotation dates are tracked in the inventory and surfaced as a review-cadence item. Any
suspected exposure triggers immediate rotation before investigation — the investigation
is not on the critical path for containment.

A rotation is recorded in the evidence store like any other event, hash-chained.
