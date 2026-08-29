# Alfred

A reproducibility and audit layer for collision-risk quantification in autonomous
vehicles, built by a supervised software factory. This file routes; it does not
explain. For what Alfred is and will not do, read the
[charter](docs/tier0/charter-and-non-goals.md).

## Where do I go?

| If you are… | Start at |
|---|---|
| **building** (any stage S0–S9) | the [reading map](docs/READING-MAP.md) — what to read, when, and whether it binds — then the [execution order](docs/tier2/execution-order.md) for where the stage stands |
| **understanding** the system | the [vault overview](vault/Overview.md) — the generated system map — and the [register](docs/README.md) for what exists and what binds |
| **deciding** (a design question) | the [ADR log](docs/tier1/adr-log.md) — append-only. `plan/` is decision *history*; where they disagree, the register wins |
| **inspecting** a layer | its home: [tools/vaultgraph/README.md](tools/vaultgraph/README.md) for the vault's vocabulary, `plan/` for the plan mirror's authority, [projects/README.md](projects/README.md) for the product convention |
| **measuring** | `bench/` — immutable per-seed records; the plan cites them, and they are the evidence |

## Rules

- **The canonical branch is `main`.** Work happens on branches; `main` is the tree.
  Parked worktrees and unmerged branches are not the state of record.
- **The plan of record is history, not instruction.** It is mirrored at `plan/`
  (sha256-pinned by its manifest; CI verifies the hash on every runner) and is
  excluded from factory dispatch workspaces and seeds. Where it disagrees with
  `docs/`, the register wins.
- **The protected set is `policy/protected-paths.json`** — what an agent may never
  write, and what enforces it. Changing it is a registered decision (an ADR) plus
  line-by-line review, never a convenience edit.
- **The vault is generated.** Never hand-edit `vault/`, `graph.json` or
  `docs-graph.html`. Change the source, then run `python3 tools/gen_vault.py`;
  `--check` fails on a hand edit.

This file is operator-authored. Agents may read it; they do not edit it.
