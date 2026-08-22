# projects/

One directory per product Alfred builds. **Each is its own git repository, and none of
them is a submodule of this one.**

Nothing lives here yet. In the single-product era (Phase 0–1) the first product — the
collision-risk quantification product (D1, D2), which Phase 0 hand-builds — is built *inside
this repository* (`src/`, `tests/`, `bench/`), in the plan of record's "Files and structure"
form. The blast-radius separation a separate repository would give is held *in place* by
physical controls instead: the dispatch mount, the protected set, and the patch gate (D20/A1
— boundaries, not convention). At the dated trigger — the first customer-container build that
must exclude factory code, or the second product (D21) — extraction proceeds per
["Adding a project"](#adding-a-project) below, and this directory gains its first entry.

## Why separate repositories rather than a monorepo

The blast-radius separation this architecture rests on is not a policy, it is a set of
physical boundaries — a container, a throwaway database, a patch file, a DB role. A
monorepo puts the factory and the thing the factory builds inside one checkout, and
then every one of those boundaries has to be re-established by convention inside it.
Specifically:

- **The agent's checkout would contain the inspector.** D20 permanently protects
  `CriterionRunner`, `EvidenceStore`, `PolicyEngine`, `AutonomyGate`, the protected-path
  config, the sandbox spec and the fingerprint tracker. In a monorepo those files are in
  the tree the agent is working in, and the protection becomes a path check rather than
  an absence. The documented instance of this failure — an agent writing
  `"chat.tools.autoApprove": true` into a settings file — happened because the gate
  lived in a file the agent could write.
- **A patch would span the factory and the product.** The `Worker` contract is that the
  container emits a patch file for one repository. A patch touching both is either
  rejected (so the monorepo bought nothing) or accepted (so the boundary is gone).
- **Per-project CI, licences and release cadence collide.** Alfred's gates run on
  Alfred's register and harness; a product's gates run on the product. One workflow
  file serving both fails for reasons the other cannot fix.
- **A customer-delivered container ships the product, not the factory.** D48 delivers a
  container the customer runs on their own data. A monorepo makes "what is in the
  image" a filtering decision made at build time, repeatedly, by whoever is building.

## Layout

```
projects/
  README.md              this file — tracked in the Alfred repository
  <project-name>/        its own git repository; ignored by Alfred's .gitignore
```

`.gitignore` excludes every subdirectory here. That is deliberate rather than
incidental: without it, `git add -A` in the Alfred repository would either swallow a
nested repository's working tree or leave a broken gitlink, and both fail quietly.

## What Alfred records about a project, and where

The project repository holds the product's code, tests and history. It does **not**
hold the factory's record of building it — that lives in the evidence store, keyed by
`org_id` and `project_id` (the tenancy columns every table carries from day one,
precisely so this stays possible with one tenant).

So: a project's git history answers *what the code is*. Alfred's evidence store answers
*which task produced it, under which criterion, on which fingerprint, with which
verdict, reviewed by whom, in how many attended minutes*. Those are different questions
and putting the second inside the first would make the audit trail editable by the
thing being audited.

## Adding a project

1. Create the repository — its own remote, its own gates.
2. Clone it into `projects/<name>/`.
3. Register it in the control plane with an `org_id`/`project_id` pair. Per-product
   policy is configuration (protected paths, permissions, thresholds), never code.

No second product until the first has paying users (D21). The gate is revenue rather
than readiness, because "the platform is ready for a second product" is a judgment the
platform will always make in its own favour.
