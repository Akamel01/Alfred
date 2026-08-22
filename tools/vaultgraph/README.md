# Domain language

This file is the vault's own vocabulary; it is a reference for the layer it documents.

Terms this repository uses in a specific sense, so a reader — or a later architecture review —
does not have to re-derive them from the code.

This file is **authored**, unlike `vault/`, `graph.json` and `docs-graph.html`, which are
generated and byte-compared. It sits in `tools/vaultgraph/` rather than in `docs/` because
`docs/` is the register: every file there carries a frontmatter contract, an index entry and a
falsification condition, and this is a glossary rather than a claim.

---

## The register and its read model

**Register** — the 63 documents under `docs/`, the ADR log, the plan mirror and the gates. The
authored sources of truth. Everything below is downstream of it.

**Read model** — `vault/`, `graph.json` and `docs-graph.html`. Derived from the register and
authored nowhere. That property is what admits them as long-term memory under D44/D47/D51, and
it is a property only `gen_vault.py --check` can hold: every generated note says *do not edit*,
and without the check that sentence is a wish.

**Live surface** — `http://127.0.0.1:8787`, served by `tools/serve_vault.py`. Re-runs every
extractor against the working tree on each request. This is the page to look at; the committed
`docs-graph.html` exists so `--check` has something to compare, not so anyone opens it.

**Floor** — the minimum an extractor must yield before its result is trusted (D57). Declared as
a constructor argument with no default, so an extractor without one is an import error rather
than a quieter graph. A check with nothing to check reports what a passing check reports.

**Vacuity** — the failure this whole package is shaped against: a regex that stops matching, a
lint that scans zero files, a suite that passes against corrupted fixtures. Paid for four times
already (ADR-0012, ADR-0013).

**Confidence** — how an edge was learned, carried on every edge and drawn twice over, in hue and
in stroke. `structural` is a fixed grammar, `derived` is a mechanical match inside a comment or
docstring span, `prose` is a reading of free text that no one has adjudicated. Flattening the
three would be the graph asserting something it does not know.

---

## Judgements

**Verdict** — the criterion's three-valued judgement on a candidate attempt: `pass`, `fail`
or `indeterminate`. The vocabulary is frozen and every autonomy gate reads it. A worker never
returns one — it returns claims; the deciding belongs downstream of dispatch.

**Assertion outcome** — how a containment control concluded: `passed`, `failed`, or
`not_executed`. Not a verdict and not spelled like one: an unproven control is failed, never
passed. Distinct from a verdict on purpose — one judges the agent's work, the other judges
whether the instrument ran at all.

---

## Relations

**Containment** (`contains`) — an *address*, not a relation. Tier holds document, gate holds
step, package holds module. It is a tree, and drawing a tree as a network was what made the
canvas unreadable: 179 spokes saying "is inside" over the graph that has real structure.

**Runs** (`runs`) — a gate step executes a module, read from the step's `run:` scalar. Closes
the chain `decision → enforced_by → module ← runs ← gate-step ← contains ← gate`: what a
decision claims, which code enforces it, and which CI step actually executes that code.

**Imports** (`imports`) — module depends on module, read with `ast`. The only relation that
answers "what does this depend on"; every other module edge is containment.

**Declined: tests-by-naming-convention.** Pairing `test_foo.py` with `foo.py` would add ~17
edges, and every one would be a filename guess shipping at `prose` confidence. This graph's
value rests on its structural edges being trustworthy, and a cheap edge that dilutes that is
not cheap. Recorded here so a future review does not re-suggest it.

---

## The drawing

**Hull** — a container drawn as a soft outline around its members instead of as one edge per
member. The same claim made once per container. Refused where it would not be compact: an
outline round members the simulation pushed apart encloses everything between them, most of
which it does not hold, and a reader takes an enclosure at face value.

**Nesting** — placing a member whose only edge was containment, rather than simulating it. Such
a node has no forces acting on it — that is what "its only relation is the thing holding it"
means — so a simulation collapses every one of them onto the origin as one blob.

**Relations-only view** — the default. Hides everything related to nothing and everything
related only to what holds it. Two thirds of this graph. Turning it off answers "what is in the
repository"; leaving it on answers "how does it fit together".

**Isolate** — a node with no relation at all, containment excluded. Stated as a rail count that
expands into a kind-grouped list, because 84 unlabelled dots on a ring is not a drawing of a
fact.

**Staleness stamp** — `GET /stamp`, a metadata-only hash of what the extractors read, polled by
the live surface so it can offer a reload. It ignores what the build writes; watching those
would give the signal a trigger that fires whenever it is resolved.

---

## Renderer seams

The published script is composed from four fragments in dependency order. Each owns something
and nothing else touches it.

**`camera`** — where the page is looking. Owns `tx`, `ty`, `scale`; nothing else may write them,
and a test asserts it. Before the split, six places each re-derived the screen-to-world
conversion by hand.

**`layout`** — where the nodes are. Force simulation, settling, nesting, isolate margin, hulls.
Seeded and deterministic, but never stored: `graph.json` carries no coordinates, which is why a
live settling animation costs nothing in byte-determinism.

**`view`** — which nodes are drawn. Five filter dimensions behind one predicate. Hidden sets
record what is *off*, never what is on, so a node kind appearing in a later build is visible by
default rather than silently absent.

`draw` and the rail stay wide on purpose: a canvas painter and a control panel touch every
concept by nature, and pretending otherwise buys nothing.

---

## Status

Generator of the vault read model; CI-gated (integrity self-test + `--check`); D51 read-model
class, not inspector; never feeds a verdict; never enters a dispatch workspace.

---

## The register contract does not apply here

Vault notes carry `kind`/`title`/`generated` frontmatter — an adjacent schema outside `docs/`;
the register contract does not apply below `docs/`. The two glossaries (tier0 = constitutional,
vault = implementation) are disjoint and cross-checked at regeneration.
