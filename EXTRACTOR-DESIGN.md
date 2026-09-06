# Extractor design — issue #5 (schema / policy / bench coverage gap)

Ticket: `gh issue view 5`. Orchestrator ruling on scope: design all three, prototype only
`policy`. This document is the contract derivation plus the three designs; `tools/vaultgraph/extract/policy.py`
is the one that ships code.

## 1. The extractor contract, as derived from `tools/vaultgraph/protocol.py` and the existing eleven (now
fourteen) extractors

**Registration.** `tools/vaultgraph/extract/__init__.py` holds `EXTRACTORS: tuple[ExtractorSpec, ...]`, the
only thing `runner.run()` executes. Adding an extractor means: write `extract/<name>.py` exposing a
module-level `SPEC: ExtractorSpec`, import it in `extract/__init__.py`, and add `<name>.SPEC` to the
`EXTRACTORS` tuple at the position its claim ordering requires (see below). `validate_registry()` runs at
*import time* — a malformed spec (no floor, duplicate name, empty `kinds`, `max_nodes < min_nodes`,
negative budget) is an `ImportError` on `python3 -c "import tools.vaultgraph.extract"`, not a runtime
surprise.

**Extraction order is claim order.** The tuple order is the order extractors run in, and later extractors
may assume earlier ones already minted what they name. `documents` and `charter` run first because
nothing points at them; `adrs` runs before `decisions`/`amendments` because an ADR's `Discharges:` field
names an operator item that must already exist; `code` runs before `imports`/`workflows` because those
resolve every endpoint through `ctx.minter.knows(id)`; `references` runs last because it mints nothing and
only relates what everything else already minted.

**An `ExtractorSpec` (`protocol.py:78-93`) is a frozen dataclass with no default on any field:**

| field | meaning |
|---|---|
| `name` | unique string; the extractor's own name in reports and edge `extractor` attribution |
| `kinds` | `NodeKind`s this extractor is responsible for (mints or relates) — never empty |
| `min_nodes` | floor. Exact (`== `) for mirror-derived sources (the input is byte-frozen); a true minimum for repo-derived ones (the input legitimately grows) |
| `max_nodes` | `None` normally; a real ceiling only where the input is byte-frozen and over-matching is itself a defect. `0` is a *required* declaration (not absence) for an extractor that mints no nodes at all — `references` sets `max_nodes=0` explicitly rather than leaving it unset, because an unset floor on both nodes and edges is exactly the hole D57 exists to close |
| `min_edges` | floor on edges, same reasoning |
| `max_unparsed` | budget for the known-irregular residue (`Unparsed` — matched the shape, could not resolve it). Drift upward fails |
| `expect_rejected` | `None`, or an **exact** count checked both directions — `Rejected` is *saw it, deliberately refused it* (prose that wears a decision's clothes but isn't one). Two-sided because a filter that stops firing and a filter that over-tightens are both failures, and only equality catches both |
| `run` | `Callable[[Context], Harvest]` |

`validate_registry` additionally requires: if `min_nodes <= 0`, the spec must say so honestly —
`max_nodes` must be exactly `0` (mints no nodes, ever) **and** `min_edges` must be `> 0` (or the extractor
declares nothing at all, which is the registry's own vacuity hole).

**`Harvest` (`protocol.py:55-66`) is what `run()` returns:**

```python
Harvest(scanned: int, nodes: list[Node], edges: list[Edge],
        unparsed: list[Unparsed], rejected: list[Rejected], anomalies: list[Anomaly])
```

`scanned` is the input-count gauge — "how many things did you even look at" — independent of how many
nodes came out. It is what distinguishes "read 7 files, minted 7 nodes" from "read 0 files, minted 0
nodes": both look like a clean pass on `nodes`/`edges` alone, and only `scanned == 0` catches the second.

**Node and Edge shapes (`model.py`):**

- `Node(id, kind: NodeKind, title, source: SourceRef, shape="", status="", body="", attrs: Mapping[str,str]={}, tags=(), occurrences=(), extractor="")`.
  `id` is **always** produced by `ctx.minter.mint(kind, local, source)`, never hand-built — the minter
  refuses a duplicate, a case-insensitive collision (macOS/Linux portability), and a character set a
  filename cannot carry.
- `Edge(src, dst, kind: EdgeKind, confidence: Confidence, source: SourceRef, evidence="", extractor="")`.
  `src == dst` raises `EdgeError` at construction — a self-relation states nothing an attribute does not
  say better. `confidence` has no default: `STRUCTURAL` (a dedicated field, table column, or heading with
  fixed grammar), `DERIVED` (a mechanical match inside a constrained span — a comment, a docstring, a
  `_comment` array), or `PROSE` (free text no one has adjudicated). An edge whose endpoint is not a node
  any extractor minted is not rejected outright — `runner.run()` collects all such dangling endpoints into
  one `dangling-edge-endpoint` anomaly after every extractor has run, so a forward reference to a node a
  later-registered extractor mints is visible, not silently dropped.

**Five fatal guards, run per-extractor by `runner._audit()` — never warnings:**

1. `scanned == 0` → `VACUOUS <name>: scanned 0 inputs`
2. `len(nodes) < min_nodes` → `VACUOUS <name>: N nodes, floor is F`
3. `max_nodes is not None and len(nodes) > max_nodes` → `OVERMATCH`
4. `len(edges) < min_edges` → `VACUOUS <name>: N edges, floor is F`
5. `len(unparsed) > max_unparsed` → `UNPARSED <name>: N items, budget is B`
6. `expect_rejected is not None and len(rejected) != expect_rejected` → `REJECTION DRIFT`

`runner.run()` never raises on a single extractor's failure — it collects every failure across every
extractor so one run reports all of them, not just the first. `gen_vault.main()` treats *any* failure as
fatal: `if not result.ok: ... return 1` — no output is written at all, not a partial graph.

**Staleness / `--check` (`gen_vault.py` + `serialize.compare_tree`).** A normal build (`gen_vault.py`) runs
every extractor, builds the whole output tree in memory (`graph.json` plus, unless `--graph-only`, every
`vault/**` note and `docs-graph.html`), and only then writes it. `--check` builds the same tree and calls
`serialize.compare_tree(ROOT, tree, managed=("vault",))`, which diffs the planned tree against the
committed one three ways: a path the plan wants that differs on disk (stale or hand-edited), a path on
disk under a *managed* directory (`vault/`) that the plan does not want (an orphan — created outside the
generator), and a path the plan wants that is missing entirely (deleted). Any of the three is a `--check`
failure; zero problems is `OK vault current (N nodes, E edges, M notes)`.

**Adding a `NodeKind`.** `model.NodeKind` is a `StrEnum`; a new member is a one-line addition. Two render
maps key off it — `render/html.py:KIND_COLOURS` (canvas colour) and `render/vault.py:FOLDERS` (which
`vault/<folder>/` a note lands in) — but neither is exhaustive today (`LAYOUT`, `PROCESS`, `EFFECT` are
already absent from `KIND_COLOURS`), so a missing entry degrades gracefully (`FOLDERS.get(kind, "other")`)
rather than breaking the build. Filling them in is good practice, not a hard requirement.

## 2. Design: `policy` (prototyped — see `tools/vaultgraph/extract/policy.py`)

**What's a node.** One `NodeKind.POLICY` node per `policy/*.json` file (7 today: `model-routing`,
`network-allowlist`, `node-palette`, `oracle-denylist`, `oracle-source-hashes`, `protected-paths`,
`role-bindings`). `policy/CONTEXT.md` is prose and is excluded by the `*.json` glob, the same way
`documents.py` excludes `docs/**/CONTEXT.md`.

**Why file granularity, not entry granularity.** Minting a node per protected-path prefix (11) or per
role-binding (8) was considered and rejected. Most protected prefixes name a *directory*
(`harness/`, `src/provenance/`, `docs/tier0/`, ...), and `code.py`'s `module_id()` only mints per-file
module ids — an edge from a prefix node to "the module it protects" would be dangling by construction on
nearly every entry, which is a claim the graph cannot check pointing at a claim the graph cannot check.
File granularity is the level at which every claim this extractor makes is actually checkable.

**What's an edge.** `EdgeKind.REFERENCES`, `Confidence.DERIVED`, mined by regexing each file's own
`authority` / `notes` / `_comment` string fields for `policy/[\w-]+\.json` substrings that name a
*different* policy file. Today that yields exactly 2 edges — `model-routing.json` names
`role-bindings.json` as the source of its routing key (`capability_id`), and `role-bindings.json` names
`model-routing.json` right back. `DERIVED` rather than `STRUCTURAL`: this is a mechanical match inside
prose fields, not a dedicated relation field with a fixed grammar (unlike the ADR log's `Discharges:`).

**The floor, and why that number.** `min_nodes=7` (a true minimum — a new policy file must not red the
build, same reasoning as `documents`'s 71-of-77). `min_edges=2` (the two cross-references verified against
the real files today). `max_unparsed=0` — every file on disk today is a well-formed JSON object; any file
that stops being one is worth stopping the build over. `expect_rejected=None` — nothing in `policy/` wears
a lookalike shape the way the plan's eight commentary spans wear a decision row's.

**The honesty requirement the ticket names.** `policy/role-bindings.json` carries 24 D19 version fields
(`prompt_version`, `tool_version`, `context_strategy_version` × 8 bindings) whose value is the literal
string `"unset"`. The extractor counts every `"unset"` string leaf anywhere in a file's JSON, recursively
and generically (it does not know those three field names — it knows the placeholder), and carries the
result as `attrs["unset_field_count"]`. It never appears in a node's `title`, and nothing about the node
implies these are live values. `test_policy_never_claims_a_live_value_for_unset_version_fields` in
`tools/tests/test_vaultgraph.py` pins this at 24 and asserts the word never leaks into the title.

**What becomes answerable that wasn't.** Before: "what does editing `policy/role-bindings.json` touch"
had no graph answer at all — `references.py` only sees `_comment`/prose *D-number and ADR-number*
mentions inside `policy/*.json`, which is orthogonal to policy files referencing each other. After: the
vault has a `policy/` shelf (`vault/policy/*.md`, via the new `FOLDERS` entry) holding all seven files with
their own shape (version, per-key entry counts, unset-field count) and the two known cross-file
dependencies as first-class edges a reader (or `docs-graph.html`) can traverse without opening seven JSON
files by hand.

**Verified counts (this run).** 7 nodes, 2 edges, 0 unparsed, 0 rejected, `scanned=7`. Whole-graph totals
moved from 603 nodes / 1099 edges to **610 nodes / 1101 edges**; `gen_vault.py --self-test` now reports
"14 extractors declare floors" (was 13); `--check` passes clean at 610/1101/616 notes.

## 3. Design: `schema` (over `migrations/`) — design only, not built

**What's a node.** `NodeKind.SCHEMA` already exists in `model.NodeKind` and is currently unused by any
extractor (`code.py` mints `MODULE` nodes for `migrations/**/*.py`, but nothing represents a *migration
revision* or a *schema* as its own concept). Proposed: one `SCHEMA` node per Alembic revision file
(`migrations/{product,harness/control,harness/evidence,harness/heldout}/versions/*.py`) — 5 files on disk
today — parsed for its module-level `revision`, `down_revision`, and the schema name it declares (the
`SCHEMA = "product"`-style constant, or the directory it lives under as a fallback). A second, coarser
node — one per schema *directory* (`product`, `harness/control`, `harness/evidence`, `harness/heldout`,
4 total) — groups the chain.

**What's an edge.** `EdgeKind` needs one addition (`REVISES` or reuse `references`-style `EdgeKind`) from
each revision to its `down_revision` (structural — parsed straight out of the `down_revision: str | None`
assignment, a dedicated field with fixed grammar), forming the migration chain per schema, plus a
`CONTAINS` edge from each schema-directory node to its revisions (matching how `documents.py` relates
`TIER` to `DOCUMENT`).

**The floor, and why that number.** `min_nodes = 5 (revisions) + 4 (schemas) = 9`, a true minimum — new
revisions are the expected, healthy growth mode named in `migrations/product/versions/0001_product_base.py`'s
own docstring ("the product schema is agent-writable ... ordinary schema evolution here is expected").
`min_edges`: 1 per revision with a non-null `down_revision` (today, 1 — `0002_fingerprint_run_fields.py`
revises `0001_control_base`) plus 5 `CONTAINS` edges (one per revision, into its schema) = a floor of 6.
`max_unparsed=0`: a `.py` revision file that does not parse (no `revision =` assignment findable) is a
migrations-tooling defect worth stopping the build over, not silently absorbing.

**The honesty question to escalate, not guess at.** `migrations/roles/` (`001_roles.sql`, `002_grants.sql`,
`grants.yaml`) is `.sql`/`.yaml`, not Alembic Python, and **is itself a protected prefix**
(`migrations/roles/` is in `policy/protected-paths.json`, "the role and grant definitions" — never
agent-authored). A `schema` extractor reading it is fine (reading protected content is explicitly allowed
by this ticket's own ground rules); the open question is whether *modelling* it as a `SCHEMA` node next to
the agent-writable `product` schema would blur a distinction the protected-paths policy exists to hold —
i.e. whether the node needs a `status`/`attrs` field asserting "human-owned, never agent-migrated" the same
way `policy.py`'s `unset_field_count` exists so a reader cannot mistake it for something it is not. This is
exactly the kind of design question the ticket says to escalate rather than resolve unilaterally, and it is
why `schema` was not the smallest-and-best-specified candidate for this pass.

**What becomes answerable that wasn't.** "If I add a column to `product`, what other revisions in that
chain does it sit on top of, and does `harness/control`'s fingerprint-field migration (`0002`) depend on
anything in `product` at all (it doesn't — separate chains, which the graph would now say explicitly
instead of a reader having to open both `env.py` files to confirm)."

## 4. Design: `bench` (over `bench/`) — design only, not built

**What's a node.** `bench/results/*.json` and `bench/fingerprints/*.json` are the evidence
(`bench/CONTEXT.md`: "immutable per-seed evidence the plan cites, never mutated"; both directories are
protected prefixes under D38/`policy/protected-paths.json`). One node per result file is the natural unit
— but `bench/results/` today holds a mix of shapes (`agentic-*-seed<N>.json`, `agentic-*-rollup.json`,
`prefixcache-*-ctx<N>-par<N>.json`, plain `*.json` named only by model, plus non-JSON `.log` files) with no
declared schema to parse against, unlike `migrations/`'s Alembic convention or `policy/`'s hand-authored
`authority`/`version` fields. A `NodeKind.EFFECT`-style "evidence card" — one node per result file, `attrs`
holding whatever top-level keys the JSON happens to carry (mirroring `policy.py`'s generic
`_top_level_counts`, since there is no fixed schema to assume) — is the safer starting shape than trying to
model "a seed" or "a benchmark run" as first-class concepts before one exists in the data itself.

**What's an edge.** The `bench/fingerprints/` side (mentioned in `bench/CONTEXT.md` and D38, referenced in
`docs/tier1/adr-log.md`) links a result to the `RunFingerprint` (27 fields, ACS-1 per
`harness/fingerprint/record.py`) that certifies it — if a result file's own JSON carries a
`fingerprint_sha256` or equivalent key, an edge from the result node to a matching fingerprint node
(`EdgeKind.REFERENCES`, `STRUCTURAL` if the key is a fixed field) is the one relation worth drawing. No
other cross-file relation is evident from the file names alone without reading the harness fingerprinting
code more closely than this design pass covers — a second escalation point.

**The floor, and why that number.** `bench/results/` holds roughly 18 `.json` files and several `.log`
files today (verify at build time — not hand-counted precisely here, which is itself the reason this was
not chosen as the prototype: a "best-specified" extractor should not open with an approximate count).
`min_nodes` would be a true minimum pinned to whatever `path.rglob("*.json")` returns at design time, with
`.log` files explicitly out of scope (unstructured; `bench_infer.py`/`probe_agentic.py`'s own stdout, not
evidence records) — a decision that itself needs stating as a `Rejected`-shaped call, similar to the
`tests-by-naming-convention` declined pattern this repo's README already records for `references.py`.

**The honesty question to escalate.** Every file under `bench/results/` and `bench/fingerprints/` is
append-only, D38-immutable evidence. An extractor reading it is fine (again, reading is not writing), but
minting a node whose `title`/`attrs` look authoritative risks a reader treating the *vault's summary* of a
bench result as equivalent to the evidence file itself — the opposite failure direction from
`policy.py`'s "don't imply a live value," but the same family: a read-model node must not read as more
certain than its source. Whether that needs a dedicated `attrs["derived_from"]` pointer-back convention
(so `vault/bench/*.md` always says "see `bench/results/<file>` for the record") is a question worth putting
to the orchestrator before writing `bench.py`, not resolving by assumption — which is also why `bench`,
not `policy`, was the extractor left unbuilt this pass along with `schema`.

**What becomes answerable that wasn't.** "Which benchmark evidence files exist for `qwen3-next-80b`, and
does every `agentic-*-seed<N>.json` file have a corresponding fingerprint record" — today only answerable
by listing the directory by hand; with a `bench` extractor and the fingerprint edge, a missing fingerprint
for a result file becomes a graph anomaly (`dangling-edge-endpoint` or a dedicated
`bench-result-without-fingerprint` anomaly) instead of something a reviewer has to notice by eye.
