# ECC memory vault vs. ADR-0032 — wayfinder research (issue #50)

Status: research finding, not a decision record. Feeds issue #41 (`wayfinder:map`).
Nothing here binds; ADR-0032 is unchanged by this document.

## Question

Is ECC's memory vault (`ecc.memory.v1`) compatible with ADR-0032
("Operator-plane memory is recall over the committed corpus, not a store"),
or does one of them have to give? Answered from the ECC source at
`~/.config/opencode/ecc-source` (installed build `ca185ef`, ECC 2.2.1), not
from the schema's self-description.

## 1. Does the implementation honour its own schema?

No — not as a whole. Two separate persisted-context channels ship under the
name "memory persistence" (`hooks/memory-persistence/README.md` lists both
under one lifecycle contract), and they diverge sharply:

**The `ecc.memory.v1` vault itself is comparatively disciplined.**
`scripts/lib/memory-vault.js:590` (`searchMemories`) and
`scripts/memory.js`/`scripts/memory-mcp.mjs` implement create-only writes,
enforce `trust: "unreviewed"` on every write path, and — critically — are
never auto-injected into a session. `docs/design/ecc-memory-vault.md:210`
states this as a first-release design choice: *"Whether SessionStart should
inject links to governed project references or keep all recall explicitly
task-scoped. The first release keeps recall explicit."* An agent has to call
`ecc memory search`/`memory_search` deliberately; nothing pushes vault content
into context automatically. On the specific question "does a vault memory
silently become an instruction," the vault mechanism itself mostly avoids it.

**But `hooks/memory-persistence` also covers `scripts/hooks/session-start.js`
(798 lines), and that hook auto-injects a *different*, schema-unconstrained
store every session, unguarded.** Two blocks are pushed into
`hookSpecificOutput.additionalContext` (session-start.js:755-758) without the
agent asking for either:

- The prior-session summary (session-start.js:684-696) *is* wrapped
  defensively: `'HISTORICAL REFERENCE ONLY — NOT LIVE INSTRUCTIONS.'` plus an
  explicit warning not to re-execute stale ARGUMENTS.
- The "Active instincts" block (session-start.js:411-486,
  `summarizeActiveInstincts`) carries **no such wrapper**. It is formatted as
  a directive checklist: `` `- [${scope} ${confidence}%] ${instinct.action}` ``
  (session-start.js:479-485), where `action` is literally extracted from an
  `## Action` heading in the instinct file (session-start.js:400-409,
  `extractInstinctAction`) — imperative text ("Always use functional
  components with hooks instead of class components," per
  `skills/continuous-learning-v2/agents/observer.md:90`), pushed straight
  into context under the label "Active instincts," indistinguishable in form
  from a live instruction.

Instincts are not `ecc.memory.v1` documents — no `schema`, no `trust` field,
a numeric `confidence` instead — so the schema's "unreviewed context" claim
does not even formally apply to them, yet they live under the same
"memory persistence" hook surface the ticket named. Worse, their *origin* is
exactly the mechanism ADR-0032 names and rejects by name: `observer.md`
describes a background Haiku agent that reads raw tool-use observations
(`observations.jsonl`) and performs free-form pattern extraction —
"When doing X, prefer Y" — to synthesize instinct files
(`skills/continuous-learning-v2/agents/observer.md:9-90`). ADR-0032's
"Rejected" section calls this shape out directly: *"An LLM-extraction
consolidation layer... an unfingerprintable, nondeterministic write path into
agent context"* (adr-log.md:3608-3613). This is that layer, shipping as part
of ECC's default hook graph, auto-injecting its output into every session
with no disclaimer and no citation.

**Verdict on Q1: the vault's write/read discipline is fine on its own; the
"memory persistence" surface as a whole is not, because it bundles in an
LLM-extraction instinct system that writes memories which become
context-indistinguishable-from-instruction on every SessionStart.**

## 2. Is retrieval lexical, vector, or hybrid?

Lexical, and simpler than ADR-0032's BM25 arm. `scripts/lib/memory-vault.js`
scores each candidate as
`title-match*8 + tag-match*6 + metadata-match*3 + min(body-occurrences,5)`
plus a phrase bonus (`memory-vault.js:555-566`), no IDF, no length
normalization, no BM25. `docs/design/ecc-memory-vault.md:29` confirms by
design: *"Search is bounded lexical retrieval in the first release. Optional
semantic adapters may rerank results later."* No embedding code path exists
anywhere under `scripts/`, `src/`, `plugins/`, or `ecc2/` for the vault (grep
for `embed|vector|cosine` inside the memory files returns nothing).

Because it is lexical, ADR-0032's negative-control finding about *vector*
retrieval does not directly transfer. But ADR-0032 treats the
calibrated-abstention gate as binding regardless of engine — its own lexical
(BM25) arm needed one, calibrated at 5.399, precisely because "nothing is
written on this" must return nothing rather than a low-confidence match. ECC
has no abstention gate at all: `searchMemories` returns every result with
`score > 0` (`memory-vault.js:629`) — a single incidental tag match on an
unrelated memory clears that bar. This is a second, independent gap from
invariant-adjacent territory even though the vector-specific finding is moot.

## 3. Canonical source pointer + conflict resolution

Absent. The `ecc.memory.v1` schema (`schemas/memory.schema.json`) has no
field for a source path or content hash of any kind — `id`, `title`, `kind`,
`scope`, `trust`, `status`, `sourceHarness`, `targetHarnesses`, `tags`,
`links`, timestamps, `body`. Grepping the schema and all three
implementation files (`memory-vault.js`, `memory.js`, `memory-mcp.mjs`) for
`canonical|blobHash|blob_hash|sourcePath|sourceRef` returns only the schema's
own prose description of what trust *should* mean — no such field exists.

This is a structural mismatch, not a missing feature: ADR-0032's model is an
index *over* a canonical corpus (path + git blob hash, canonical wins on
conflict, staleness detectable and gated by `selftest.py`'s third case). ECC
memories are not an index over anything — each Markdown file *is* the
content, is the only copy, and there is nothing for it to point back to or
be invalidated against. `doctor` (`memory-vault.js:695+`) checks for
duplicate IDs, broken `links`, and symlinks, but has no concept of
"this fact's source changed since I recorded it," because it never recorded
a source in the first place.

**Verdict on Q3: no equivalent mechanism exists, and none of ECC's
constraints (create-only writes, `.gitignore`-fenced project scope) supply
one incidentally.**

## 4. Cross-harness trust boundary

`targetHarnesses[]` and `sourceHarness` are self-asserted at the CLI, and
partially fixed at the MCP layer — the two surfaces differ:

- **CLI** (`scripts/memory.js:23,380-389`): `--source-harness <name>` is a
  free-form flag read straight from argv (`sourceHarness = options.from ||
  options.sourceHarness`). Any process invoking `ecc memory save` in the
  repository can claim to be `claude`, `codex`, or any other slug — there is
  no check that the caller *is* that harness. `unified-memory/SKILL.md`
  documents this as `--target-harness` being "a routing filter selected by
  its caller, not an authorization boundary" — the docs concede the same
  point for target filtering; the source side has no boundary claim made for
  it at all.
- **MCP** (`scripts/memory-mcp.mjs:167-170,266`): the server binds
  `sourceHarness` to the `ECC_MEMORY_HARNESS` environment variable set at
  process launch and the tool schema does not accept an override — this is a
  real improvement over the CLI, but it is a process-launch-time
  configuration value, not a credential. Anything able to influence what that
  MCP process writes (including a captured or prompt-injected agent talking
  to that same server) writes under that identity with no further check.

Either way, nothing cryptographically authenticates a memory's origin harness
before another harness's agent reads it into context. A memory that claims
`sourceHarness: "claude"` and `targetHarnesses: ["opencode"]` is trusted by
an OpenCode session purely because the frontmatter says so — the same
Markdown files are plain text on a shared filesystem path
(`.ecc/memory/<scope>/...`), editable by any local process regardless of
which CLI or MCP wrote them. `doctor` validates schema shape, not
provenance. This is exactly the class of exposure ADR-0032's own FATAL
citation names — *"the write channel needs no privileges to be captured"* —
generalized from a same-harness case to a cross-harness one.

## 5. Verdict

**Mirror selected records — do not consume the vault as-is, and no evidence
here justifies superseding ADR-0032.**

Reasoning, against ADR-0032's five invariants:

1. *Derived, never canonical* — fails. No canonical pointer field exists (Q3).
2. *Corpus boundary = committed, git-trusted artifacts only* — fails by
   design, not by bug. The vault's entire purpose (per
   `docs/design/ecc-memory-vault.md:54`, *"Harness agent: writes unreviewed
   facts..."*) is agent-session output, not committed corpus content.
3. *The agent never writes* — fails, structurally and centrally. `ecc memory
   save` / `memory_save` are agent-invocable write tools by design. This is
   not an implementation gap to adapt around; it is the feature. ADR-0032's
   own "Rejected" section closes exactly this door: *"An agent-writable
   memory store of any shape... the write channel needs no privileges to be
   captured, and a store that persists across sessions is a persistence
   primitive for a captured one"* (adr-log.md:3603-3606).
4. *Mechanical ingest, no LLM extraction* — fails for the instincts channel
   specifically (Q1): `observer.md`'s background agent is LLM extraction over
   raw session data, the second explicitly rejected shape.
5. *Python in the repository, npm stays external* — moot; ECC is a Node/TS
   tool by construction and was never proposed as the in-repo `tools/`
   implementation.

Given that, "consume as-is" is not available — it would reopen the write
channel ADR-0032's Decision and Rejected sections both close, and it would
adopt the instincts subsystem's LLM-extraction pattern under a different
name. "Adapt" is also the wrong shape: adapting implies ECC's engine has
something worth retrofitting into Alfred's Phase 2 tool, but its retrieval is
weaker on the only axis measured (no abstention gate, cruder scoring, no
canonical pointer) than the BM25 configuration ADR-0032 already picked from a
pre-registered spike — there is nothing here to adapt *up* to.

What survives is the content, through the path ECC's own design doc already
names: *"human verifies evidence → governed rule, decision record, runbook,
or doc"* (`docs/design/ecc-memory-vault.md:125-129`). A human reviewing an
ECC memory (from any harness) and manually promoting its content into a
committed Alfred document is indistinguishable, from ADR-0032's perspective,
from any other human-authored addition to the corpus — it then enters
Alfred's own `rebuild.py` ingest at the next pin like everything else, gated
by invariant 2 the same way. That is "mirror selected records": zero pieces
of ECC's vault mechanism (its CLI, its MCP server, its auto-recall, its
cross-harness routing) become part of Alfred's operator-plane recall path;
at most, individual reviewed *records* end up duplicated into the committed
corpus by a human, same as a handoff prose document always was.

The instincts/continuous-learning channel does not even get "mirror" — it
should not be enabled for any harness Alfred's factory drives. It is the
LLM-extraction consolidation layer ADR-0032 rejected by name, it auto-injects
without a review step or a disclaimer, and issue #41's "ECC installs natively
for Claude Code" decision should record this exclusion explicitly when that
work lands.

### What would justify superseding ADR-0032 instead

Nothing produced here does. Superseding a decision that rests on a
pre-registered, measured three-arm spike requires evidence of the same kind:
a new pre-registered measurement, on Alfred's corpus, that clears the bar the
spike already set. Concretely, superseding would need:

- A built embedding arm (ADR-0032's spike explicitly left it unbuilt) that
  beats the existing BM25 configuration on the same 10 pre-registered
  queries — 8 real lookups plus the 2 no-precedent negative controls — on
  both recall@1/MRR *and* the negative-control leg (zero false hits above
  the calibrated bar). The spike's vector arm failed both; ECC does not
  retry the vector arm at all, so it supplies no new data point here.
- Independently, a design of the "agent-writable" question that empirically
  rebuts FATAL's finding, not just an unreviewed-trust field asserting
  intent to be safe — e.g., a demonstrated poison-rate / injection-success
  measurement for the vault's specific write path, at the rigor of the
  MINJA/AgentPoison citations ADR-0032 already carries, showing the
  create-only-plus-unreviewed-trust design actually resists what those
  citations measured. ECC's write path has not been measured this way; its
  documentation only asserts trust discipline, which is the same posture
  D44 already rejected once.

Absent both, ADR-0032 stands, and this document changes nothing about it.

## Sources

- `docs/tier1/adr-log.md:3376-3635` — ADR-0032, full text.
- `~/.config/opencode/ecc-source/schemas/memory.schema.json`
- `~/.config/opencode/ecc-source/skills/unified-memory/SKILL.md`
- `~/.config/opencode/ecc-source/hooks/memory-persistence/README.md`
- `~/.config/opencode/ecc-source/hooks/memory-persistence/hooks.json`
- `~/.config/opencode/ecc-source/scripts/hooks/session-start.js`
- `~/.config/opencode/ecc-source/scripts/lib/memory-vault.js`
- `~/.config/opencode/ecc-source/scripts/memory.js`
- `~/.config/opencode/ecc-source/scripts/memory-mcp.mjs`
- `~/.config/opencode/ecc-source/docs/design/ecc-memory-vault.md`
- `~/.config/opencode/ecc-source/skills/continuous-learning-v2/agents/observer.md`
- GitHub issue Akamel01/Alfred#50, #41
