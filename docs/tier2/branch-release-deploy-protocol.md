---
status:        provisional
owner:         executable
enforcement:   ci-gate
evidence:      S8, 2026-08-18. Two releases built, deployed and rolled back through `docker compose` on this machine, each transition verified by reading `/version` from the running service rather than by the exit code of the command that caused it. The branch and release halves rest on no observation: no agent branch has ever been opened, so everything below about patch flow is written against A2/D10 and Phase 1 is its first test.
falsifies_if:  A deploy occurs by any path other than CI on merge; or a rollback is reported successful without the served release identity having been read back and matched; or a release is deployed whose identity is not baked into its artifact; or `harness/deploy/` records a ledger entry for a transition that did not take.
review_after:  Phase 2
---

# Branch, Release and Deploy Protocol

## What a release is

A release is an **image tagged with an identity that is baked into it**. Not a commit, not
a branch, not a directory of files: an artifact that can be asked what it is and answers
from inside itself.

`deploy/api.Dockerfile` promotes two build arguments to environment variables —
`ALFRED_RELEASE_ID` and `ALFRED_RELEASE_DIGEST` — and `/version` reads those and nothing
else. No repository, no mounted file, no `git` call at request time.

**This is the single load-bearing decision in the whole protocol.** If the served identity
were read from anything outside the artifact, a rollback would report the old release while
the new code kept serving, and the verifier would agree with it. The check would pass in
precisely the situation it exists to detect. An image built without an identity fails at
import rather than serving anonymously.

The digest is `git rev-parse HEAD` with `+dirty` appended when the tree is not clean. A
release identified by a commit whose bytes it does not match is the provenance defect D27
exists to prevent, occurring inside the deploy path.

## Deploy

Through `docker compose`, not around it. Phase 0's exit criterion is "`docker compose up`
serves the API; deploy and rollback both execute and are verified", so the mechanism is
verified on the path the operator actually uses — a mechanism verified on some other path
has verified some other mechanism.

The compose service selects its image by tag from `ALFRED_API_IMAGE` and **has no default**.
`docker compose up api` with nothing selected fails rather than quietly serving whatever
`alfred-api:latest` happens to be; a floating tag is the thing the supply-chain policy
exists to forbid.

Order of operations, and it matters:

1. Build and tag the release, stamping its identity.
2. Bring the service up against that tag.
3. Read `/version` from the running service.
4. **Only if the served release equals the intended release**, append to the ledger.

Recording first would leave a history claiming a deploy that never took — and the rollback
target is chosen from that history, so one unverified entry corrupts every rollback after it.

## Rollback

The same code path as deploy, aimed at an earlier target. A rollback that ran different
code from a deploy would be a path exercised for the first time during an incident.

The target is **the last recorded release that is not the one currently serving**, found by
scanning for a different `release_id` rather than by taking the second-to-last row. A
positional rule oscillates: after deploy r1, deploy r2, rollback to r1, the second-to-last
row is r2, so the next rollback returns to r2, then to r1, forever, reporting success at
every step while converging on nothing.

Two states are failures rather than no-ops:

- **No release has ever been deployed.** There is nothing to roll back to. Reported as a
  failure because a rollback that succeeds against an empty history is the check passing
  with nothing to check.
- **Every recorded release is the one serving.** A rollback would deploy what is already
  running and report success without changing anything.

## What "verified" means here

Verified means **the service was asked which release it is, and answered with the intended
one**. It does not mean the command exited zero, and it does not mean a container with the
right tag is running — "the new container is up" and "the new code is serving" are
different claims, and the gap between them is where a failed rollback lives.

The compose healthcheck asks `/health` for a `release_id` rather than merely checking that
something is listening. A healthcheck that cannot tell two releases apart reports "up"
across a failed rollback, which is the one moment anybody consults it.

## The ledger

`harness/deploy/ledger.py`, append-only, one JSON object per line: release id, image ref,
source digest, action, timestamp. Append-only for the same reason evidence is (D43) — a
deploy history that can be rewritten cannot answer "what was serving when that number was
computed", which is the question a D27 recall actually asks.

The timestamp is supplied by the caller rather than read inside the ledger, so a test can
be deterministic without the ledger owning a clock.

## Branch and patch flow

**Unobserved. Written against A2 and D10; Phase 1 is its first test.**

The agent container holds no VCS credential. It emits a patch file to a mounted volume; a
separate uncontaminated process validates the patch and opens the pull request. The
deliverable channel and the exfiltration channel must not be the same channel — AsyncAPI is
the worked example, where a PR opened at 05:08 was followed by a token exfiltrated at 05:16.

Validation on the privileged side hard-rejects any hunk touching `.github/`, `harness/`,
`policy/`, `migrations/roles/` or protected-path configuration, and runs the A10 scan for
non-ASCII control, zero-width and bidi characters. `pull_request_target` with a head
checkout is never used, and `actions/cache` is disabled on workflows touching agent
branches, because Actions caches are repository-scoped and ephemerality fails below the
container.

Deploy stays CI-triggered on merge. A deploy by any other path falsifies this document.

## What is not built

Continuous delivery to anything but this machine; a registry; signed images; blue/green or
canary rollout. None are required by Phase 0's exit criterion, and each would be a contract
written before the thing it describes.

Also absent: any rollback of the **database**. The deploy mechanism here returns an
application artifact to a previous version and says nothing about schema. Evidence
migrations are additive-only and their downgrade raises, so an application rollback across
a migration is not symmetric — the artifact goes back and the schema does not. Phase 0 does
not hit this because the API holds no database credential; S7's point-in-time recovery is
where it gets answered, and it is outstanding.
