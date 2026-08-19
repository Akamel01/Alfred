# Alfred

A reproducibility and audit layer for collision-risk quantification in autonomous
vehicles, built by a supervised software factory whose autonomy is granted per task
class on measured evidence.

The factory and the product are the same project on purpose: the product supplies the
ground truth the factory needs to measure itself.

## Start here

| | |
|---|---|
| **[Reading map](docs/READING-MAP.md)** | **What to read, when, and whether it binds the code you are writing.** Start here for any build work. |
| [Register index](docs/README.md) | What exists: every document by tier, with status and enforcement. |
| [Architecture decisions](docs/tier1/adr-log.md) | The ADR log. Binding on implementation and easy to miss, since they share one file. |
| [Charter and non-goals](docs/tier0/charter-and-non-goals.md) | What this is, what it will not do, and the kill criteria. |

The architecture plan of record lives outside this repository, at
`~/.claude/plans/handoff-autonomous-software-engineering-fizzy-dahl.md`. It carries the
decision history, the measurements, and the phase sequence. The documents here are its
normative form; where they disagree, the documents win.

## The rule everything follows

> Agent autonomy tracks the availability of ground truth the agent did not author and
> cannot retrieve.

Applied mechanically to any proposed task: *what independent thing says this is right?*
No answer means it is not agent work yet.

## Layout

```
docs/            the register — 7 tiers, one file per document (see the reading map)
harness/         OUTSIDE the agent tree; agents may improve the factory, never the inspector
  acs/           ACS-1 canonical serialization, Python + JavaScript + the vector suite
bench/           Phase -1 inference measurements
policy/          machine-readable Tier 4 — network allowlist, oracle denylist
deploy/          release artifacts; the API is the deployable unit
scripts/         register generation and CI gates
src/             the product — domain, metrics, provenance, thresholds, api; ingest and replay land with S5
tests/           product tests; heldout/ and reference/ stay operator-populated
migrations/      one directory per schema — product/, harness/, roles/
projects/        one nested git repository per product Alfred builds (see projects/README.md)
```

## Checks

```bash
python3 scripts/lint_docs.py --check && python3 scripts/gen_reading_map.py --check && python3 scripts/lint_migrations.py && python3 scripts/lint_verdict_boundary.py && python3 -m pytest harness -q && node harness/acs/verify_js.mjs
```

The doc lint enforces the header contract and regenerates the register index. The
reading-map check fails when a document exists with no reading position — a document
nobody is told to read is worse than absent. The migrations lint keeps every schema
evolution additive, and the verdict-boundary lint enforces the verdict boundary and
fails when it has nothing to check. The ACS-1 suites verify that an independent
implementation reproduces every canonical byte and every digest, which is the claim
the audit chain rests on.

## Keeping the map honest

The reading map is generated from a single table in `scripts/gen_reading_map.py`. Adding
a document without giving it a phase, a kind and a one-line reason fails the check.
Update it in the same change that adds or promotes a document — never afterwards.
