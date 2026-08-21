---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      Documented, not hypothesized. An agent has written an auto-approve setting into its own configuration file, disabling its approval gate because the gate lived in a file it could write (CVE-2025-53773).
falsifies_if:  A merged diff touches a protected path, or a path that should have been protected is found to have been agent-writable.
review_after:  Phase 2
---

# Protected Paths Policy

## The rule

**Agents may improve the factory, never the inspector.**

Every safeguard in this architecture assumes the judge is independent of the worker. An
agent editing the judge collapses all of them at once, silently, with tests green —
because the tests are downstream of the edit.

The pressure is ordinary optimization, not malice. "Make the criterion runner faster"
that quietly loosens a tolerance looks like success at every layer of observation
available to the system.

## Defined by provenance, not by enumeration

A path is protected when the thing it contains is what makes a verdict trustworthy.
Enumerating known-bad files is a losing game — `conftest.py`, `.pth` files,
`sitecustomize`, binary trojans, instruction files, and whatever comes next. The
architectural closure is that `CriterionRunner` runs outside the agent's tree and
materializes its environment from trusted provenance, ignoring everything outside
declared source paths.

Protected paths are the second layer, and they are policy configuration, never code.

Since ADR-0031 that sentence is literal. The set's machine-readable form is
`policy/protected-paths.json` — versioned, and under `policy/` itself, so the gate's
policy file is protected by the gate. `harness/patch/validate.py` loads it, failing
closed on any load error, and `harness/patch/test_protected_set.py` asserts set
equality between the file and this table in both directions: a row in this table with
no entry in the file protects nothing, and an entry with no row protects something no
one was told about. The `control.policy_protected_path` table carries the same policy
per tenant for runtime enforcement; its writer is a later stage, and nothing here
claims the sync.

## The protected set

| Path | Contains |
|---|---|
| `harness/` | `CriterionRunner`, egress canary, null-agent floor test, seeded-defect suite |
| `src/provenance/` | result stamping |
| `src/thresholds/` | declared, cited, versioned threshold configuration |
| `tests/heldout/` | composed and perturbed held-out criteria |
| `migrations/harness/`, `migrations/roles/` | control, evidence, verdict, held-out and policy schema, and the role/grant definitions. **Corrected 2026-08-15:** this row previously named `migrations/evidence/` and `migrations/control/`, which do not exist and are not the layout — the split is product versus harness, one directory per schema beneath it (Data Architecture § Migration layout). A protected path that names a directory that will never exist protects nothing. `migrations/product/` is deliberately *not* protected: the product schema is factory. |
| `scripts/` (the whole directory) | Register lints and generators — inspector machinery (D20). **Corrected 2026-08-19:** this row previously named only the gate entry points and called the rest "otherwise unprotected"; the patch gate protects the whole directory, and the machine-readable set states so. A validator an agent may edit validates nothing. |
| `policy/` | protected paths, permissions, network allowlist, sandbox specification |
| `.github/`, CI configuration, hooks | the gate that runs before any human sees a change |
| fingerprint tracker | the identity every autonomy grant is keyed to |
| `docs/tier0/` | the constitution — permanently human-authored |
| `pyproject.toml`, `uv.lock` | the dependency closure. A change here can make the oracle importable inside the container, which converts merge rate into a measurement of delegation. Dependency additions are an escalation, not an agent edit. |
| oracle environment and its pin | the only place the oracle's code exists. Its outputs cross the boundary as data; its code never crosses it at all. |
| oracle denylist configuration | what the boot-time absence assertion checks against. A denylist an agent can weaken is not a denylist, and its version is a fingerprint field. |

## Enforcement

**On the patch, outside the container.** The container emits a patch file to a mounted
volume. A separate, uncontaminated process parses the diff's file list and hard-rejects
any hunk touching the protected set, before the patch becomes a pull request.

This ordering is the point: the process that validates the patch is not the process that
produced it, and it holds credentials the producing process never sees.

**By filesystem mount.** Writable paths are fixed by the harness at dispatch. The
container cannot write outside them regardless of what it attempts.

**By database grant.** Evidence, verdict and policy tables are unreachable from the
agent role. Migrations against them run under a separate migrator role from a separate
directory.

**By import graph.** The verdict module has no import path from any agent module,
CI-linted, because a graph engine raises only on *concurrent* unreducered writes — a
sequential write to a verdict field is silent.

## Attempts are evidence

A protected-path write attempt is a structural escalation trigger and is recorded to the
evidence store with the full attempt bundle. It is never silently denied: a denial that
leaves no trace removes the signal that something is optimizing against the boundary.

## The inspector stays small

The human-only kernel is minimized by construction. Prefer OS, database and CI-native
enforcement over bespoke code, because bespoke code is itself something that must be
maintained and reviewed by the one person who may not edit it under agent assistance.

Kernel lines-of-code is tracked as a health metric. Agent-drafted inspector patches are
permitted only under line-by-line human review with a mandatory ADR.
