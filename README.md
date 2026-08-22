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

The canonical layout is the structure fence in [coding standards](docs/tier2/coding-standards.md):
every top-level directory, one line each. The vault's layout extractor floors it — a
directory the fence forgets to name surfaces as an anomaly. This block is a pointer,
not a second list: one home per fact.

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
