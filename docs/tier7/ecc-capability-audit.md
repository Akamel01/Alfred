---
status:        provisional
owner:         human
enforcement:   none
evidence:      A read of ECC 2.2.1 at commit ca185ef (286 skills, 68 agents, 11 JSON schemas, the ecc2 Rust control plane, the AutoForge workspace) against Alfred's register as of 2026-09-02. Classification is from what the source does, never from what its documentation claims.
falsifies_if:  A capability classified ECC-NATIVE turns out to require an Alfred-side adapter to be usable, or a capability classified REMOVE/REPLACE is found to be load-bearing for something Alfred already depends on.
review_after:  the ECC2 reuse boundary decision
---

# ECC capability classification

Research audit for [issue #48](https://github.com/Akamel01/Alfred/issues/48), a child of the
`wayfinder:map` effort ([issue #41](https://github.com/Akamel01/Alfred/issues/41)). Classifies
every meaningful ECC 2.2.1 (`ca185ef`) capability against Alfred's own infrastructure, using the
seven buckets fixed by the map issue.

**Scope note on the ticket's counts.** Issue #48 asks for "Agents (11)". The actual source at
`~/.config/opencode/ecc-source/agents/` contains **68** agent definitions (`ls
~/.config/opencode/ecc-source/agents/ | wc -l` → 68), and `AGENTS.md:3` states "68 specialized
agents, 286 skills, 94 commands" directly. There is no manifest, file, or directory anywhere in
the source that enumerates exactly 11 agents — `agent.yaml` (the gitagent export manifest) lists
skills, not agents, and carries no agent count at all. This audit classifies the real population
(68 agents, 286 skills, 56 installed on this machine) rather than the ticket's stale figure, and
flags the discrepancy for whoever owns the map issue.

Every claim below cites a file the author read directly with the Read/grep tools, from
`~/.config/opencode/ecc-source` (ECC source, "ECC-SRC"), `~/.config/opencode` (this machine's
installed subset, "ECC-INSTALLED"), or the Alfred worktree ("ALFRED", paths relative to repo
root). No README prose or skill-frontmatter description is cited as evidence of behavior —
only implementation files (scripts, schemas, hook payloads, harness/provenance source).

---

## 1. Agents (68 total, 0 installed as Claude Code subagents on this machine)

None of ECC's 68 `agents/*.md` definitions are installed under `~/.config/opencode` — the
install state (`ECC-INSTALLED:ecc-install-state.json:16-21`) resolved to modules
`commands-core, platform-configs, skill-unified-memory, workflow-quality` only; no
`agents-*` module was selected. So today, on this machine, ECC's agent roster is inert.

Reading the definitions themselves (`ECC-SRC:agents/security-reviewer.md:1-6`,
`ECC-SRC:agents/tdd-guide.md:1-6`, `ECC-SRC:agents/planner.md:1-6`): each is a Markdown file with
YAML frontmatter (`name`, `description`, `tools`, `model`) plus a fixed "Prompt Defense Baseline"
block repeated verbatim across agents, then free-text role instructions. `tools:` is a flat
comma list (e.g. `security-reviewer` → `Read, Grep, Glob, Bash`; `tdd-guide` →
`Read, Write, Edit, Bash, Grep`), and `model:` is a single static string (`sonnet`, `opus`) — there
is no per-task routing logic, just a hardcoded default per agent file. This is the entirety of
ECC's "agent" concept: a prompt template plus a tool allowlist string, interpreted by whatever
harness loads it (Claude Code's own subagent loader). There is no scheduler, no dependency graph,
no state machine in the agent files themselves.

**Classification: ECC-NATIVE, consult only.** Alfred's palette (`policy/node-palette.json`,
ADR-0039) is the type system for what may run as a graph node, and the map issue is explicit that
ECC agents "become implementations bound to palette kinds" — not new authority. Since these are
static prompt+tool-list files with no runtime behavior of their own, adopting one means copying
its prompt text into an Alfred-authored agent binding under the palette, not depending on the ECC
file at runtime. None of the 68 need an adapter; they need, at most, a palette-kind mapping
table (a docs artifact, not code) that says "our `security-reviewer` node draws its prompt from
ECC's `security-reviewer.md`, version-pinned at `ca185ef`."

Individually notable:
- **`planner.md`** (`model: opus`, `tools: Read, Grep, Glob` — read-only) overlaps with Alfred's
  own planning surface (`plan/`, ADR log). **REMOVE/REPLACE for Alfred's use** — Alfred's plan of
  record is sealed and mirrored (`tools/vaultgraph/mirror.py:1-20`); an ECC planner agent writing
  plan-shaped output would create a second, un-pinned planning artifact.
- **`silent-failure-hunter.md`, `type-design-analyzer.md`, `refactor-cleaner.md`** are genuinely
  narrow static-analysis roles with no Alfred equivalent — **ECC-NATIVE**, safe to consult
  as-is for ad hoc review, no contract needed since they produce advisory text, not committed
  artifacts.
- The ~30 language/framework build-error-resolver and `*-reviewer` agents (`go-reviewer.md`,
  `rust-reviewer.md`, `django-reviewer.md`, etc.) are **ECC-NATIVE**, and irrelevant to Alfred's
  actual stack (Python/Pydantic per `pyproject.toml`) except `python-reviewer.md`.

---

## 2. Skills — 286 total in source, 56 installed here

`agent.yaml:9-15` lists the skills ECC's own gitagent export manifest advertises, but the actual
skill population is enumerated by directories: `ls ECC-SRC:skills | wc -l` → 286. Installed:
`ls ECC-INSTALLED:skills | wc -l` → 56 (confirmed by directory listing;
`ECC-INSTALLED:ecc-install-state.json` resolution names only 4 *modules*, one of which,
`skill-unified-memory`, and one, `workflow-quality`, account for most of the 56).

A material finding, grounded in direct reads of representative skills across the brief's §5
categories: **most ECC skills are prompt-only markdown with no executable logic.** Confirmed by
listing files under each skill directory:

| Skill | Files | Verdict |
|---|---|---|
| `architecture-decision-records` | `SKILL.md` only (180 lines) | prompt-only |
| `unified-memory` | `SKILL.md` only | prompt-only |
| `browser-qa` | `SKILL.md` only | prompt-only |
| `repo-scan` | `SKILL.md` only | prompt-only |
| `codehealth-mcp` | `SKILL.md` only | prompt-only, despite the "mcp" name it wires to no MCP server in-repo |
| `verification-loop` | `SKILL.md` only (129 lines) | prompt-only |
| `continuous-learning` | `SKILL.md` + `config.json` + `evaluate-session.sh` | **has real logic** |
| `delivery-gate` | `SKILL.md` + `hooks/quality-gate.py` (220 lines) | **has real logic** |

(Verified with `find ECC-SRC/skills/<name> -type f` for each row.)

### 2.1 By brief §5 category

- **Architecture / codebase design** (`architecture-decision-records`, `blueprint`,
  `contract-first`): prompt-only guidance for capturing decisions
  (`ECC-SRC:skills/architecture-decision-records/SKILL.md:1-9`, `metadata.origin: ECC`, triggers
  on phrases like "let's record this decision"). No numbering discipline, no immutability
  enforcement, no supersession tracking beyond a suggested Markdown template. Alfred's own ADR
  log (`docs/tier1/adr-log.md:1-13`) is `status: frozen`, has explicit non-revision rules
  ("Historical claims are never revised, only superseded... Numbering is sequential and never
  reused") and is cross-checked by tooling. **Classification: REMOVE/REPLACE** — do not adopt
  ECC's ADR skill; Alfred's is stricter and already the register.

- **TDD** (`tdd-guide` agent, `tdd-workflow` installed skill, `django-tdd`): red-green-refactor
  prompting only; no coverage gate is enforced by the skill itself, only textual instruction
  ("Ensure 80%+ test coverage" is a sentence in `agents/tdd-guide.md`, not code that measures it).
  Alfred's own held-out seeded-defect suite (`tests/heldout/`, protected) and harness
  (`harness/criterion`, `harness/selftest`) execute real tests against real criteria.
  **Classification: ALFRED-NATIVE** — Alfred's verification is executable and gated; ECC's is
  advisory prose.

- **Verification / delivery gates** (`verification-loop`, `delivery-gate`,
  `production-audit`, `eval-harness`): `delivery-gate`'s `quality-gate.py`
  (`ECC-SRC:skills/delivery-gate/hooks/quality-gate.py:1-8, 20-25`) is a **Stop-hook** script that
  regex-scans the session transcript for rationalization phrases ("this is a pre-existing
  issue", "skipping tests for now") and blocks Claude from ending the session if the transcript
  looks incomplete or a "complex" task (heuristic: `COMPLEX_THRESHOLD = 3`, line 34) didn't write
  to a learning log. This is real, but it is a **string-pattern heuristic over the agent's own
  prose**, not an execution-based check — it cannot catch a task that silently skipped tests
  without saying so in words that match one of the four regexes (`RATRIONALIZE` list, lines
  22-27). It also depends on the `Stop` hook actually firing, which on this machine it does not
  (§3, `hookConsent: declined`). Alfred's harness gates run the code (`harness/criterion`,
  `harness/oracle`, `harness/selftest`) and evaluate verdicts against declared thresholds
  (`src/thresholds/`, protected, never agent-authored). **Classification: REMOVE/REPLACE** for the
  gate role itself (Alfred's harness is strictly stronger and already the verdict authority) —
  but see §5(b) below, `quality-gate.py`'s narrow "did the agent say the word 'skip'" detector is
  a genuinely different, complementary signal Alfred's harness doesn't currently produce, which is
  a real gap worth a look (kept out of REMOVE/REPLACE's blanket verdict, flagged separately).

- **Security** (`security-reviewer` agent, `django-security`, `llm-trading-agent-security`):
  `agents/security-reviewer.md:20-30` lists `npm audit`, `eslint-plugin-security` as its analysis
  commands — Node/JS-specific, not applicable to Alfred's Python stack out of the box. Advisory
  text only; no SAST execution wired into ECC itself (it invokes external tools the operator
  must already have). **Classification: ECC-NATIVE, consult only** — useful prompt scaffold for
  ad hoc review, not something Alfred adopts as a gate.

- **Debugging / testing** (`agent-introspection-debugging`, `e2e-testing`, `windows-desktop-e2e`,
  `ai-regression-testing` — all installed): all confirmed prompt-only via `find <dir> -type f`
  returning a single `SKILL.md`. **ALFRED-NATIVE or ECC-NATIVE-consult**, no logic to wrap.

- **Context management / memory / continuous learning** (`unified-memory`, `context-budget`,
  `continuous-learning`, `continuous-learning-v2`, `strategic-compact` — all installed): see §4
  for the memory schema. `continuous-learning`'s `evaluate-session.sh`
  (`ECC-SRC:skills/continuous-learning/evaluate-session.sh:1-24`) is a real bash script triggered
  by a `Stop` hook that extracts "reusable patterns" into `~/.claude/skills/learned/`, gated by
  `config.json`'s `min_session_length: 10` and `auto_approve: false`
  (`ECC-SRC:skills/continuous-learning/config.json:1-6`). This writes new *skills* into the
  harness's own skill directory from unreviewed session transcripts — exactly the kind of
  write-your-own-instructions loop Alfred's charter would treat with suspicion, and it's gated by
  `trust: "unreviewed"` being the *only* legal value in `memory.schema.json:57-60`
  ("Vault memories remain unreviewed context. Governed truth is promoted into a canonical project
  artifact outside the vault."). **Classification: SHARED CONTRACT candidate for the schema only**
  (§4), **REMOVE/REPLACE for the auto-write-skills behavior** — Alfred has no equivalent and
  should not acquire one that self-modifies the harness's instruction set from unreviewed
  transcripts.

- **Documentation** (`living-docs-governance`, `growth-log`, `code-tour` — installed): prompt-only
  guidance for keeping docs in sync; Alfred's vault (`tools/vaultgraph/`) is a generated,
  hash-verified artifact (`--check` fails on hand edits, per repo `CLAUDE.md`). **ALFRED-NATIVE.**

- **Browser QA** (`browser-qa`, `click-path-audit` — installed): prompt-only
  (`find ECC-SRC/skills/browser-qa -type f` → `SKILL.md` alone). No Playwright/Puppeteer driver
  code in the skill itself. **Classification: ECC-NATIVE, consult only** if Alfred ever needs
  browser QA prompts; no code to adapt.

- **Repo onboarding / git workflow** (`codebase-onboarding`, `repo-scan`, `git-workflow` —
  installed): prompt-only. Alfred's onboarding is `docs/READING-MAP.md` plus
  `docs/tier7/onboarding-guide.md`, hand-authored and already tuned to the register/vault split.
  **ALFRED-NATIVE.**

- **Autonomous operation / model orchestration / agent introspection** (`continuous-agent-loop`,
  `autonomous-loops` (source-only), `agent-introspection-debugging`,
  `agent-self-evaluation` — installed): prompt-only prose describing loop patterns; no scheduler,
  no state machine. Alfred's actual orchestration topology is hand-authored JSON
  (`orchestration/topology.json`, protected, operator-only per ADR-0039) with a generator and
  lint (`tools/vaultgraph` neighbors, referenced in repo `CLAUDE.md`). **ALFRED-NATIVE** for the
  orchestration substrate; ECC's loop-pattern prose is **ECC-NATIVE, consult only** for informing
  prompt design inside Alfred-owned nodes.

- **Production audit / code health** (`production-audit`, `plankton-code-quality`,
  `codehealth-mcp` — installed): prompt-only (confirmed above for `codehealth-mcp`).
  **ECC-NATIVE, consult only.**

---

## 3. Hooks — event vocabulary and the consent blocker

`ECC-SRC:hooks/hooks.json` top-level keys (read via Python `json.load`, not grep, to get the
real key set): **`PreToolUse`, `PreCompact`, `SessionStart`, `PostToolUse`, `PostToolUseFailure`,
`Stop`, `SessionEnd`** — seven Claude Code hook events. Matchers observed include
`Bash`, `Write`, `Edit|Write`, `Bash|Write|Edit|MultiEdit`, `Skill`, and the wildcard `.*`
(`ECC-SRC:hooks/hooks.json:6,17,28,52,64,176` and others). Each hook shells out through a
`resolveEccRoot()` bootstrap that locates the plugin install directory before dispatching to a
named script under `scripts/hooks/` (e.g. `pre-bash-dispatcher.js`, `governance-capture.js`,
`gateguard-fact-force.js`, `doc-file-warning.js`) — this is real dispatch machinery, not prompt
text.

**`hookConsent: "declined"` is confirmed on this machine**
(`ECC-INSTALLED:ecc-install-state.json:18`, `"request": {..., "hookConsent": "declined"}`). This
**is a blocker** for every hook-dependent capability listed above: `delivery-gate`'s
`quality-gate.py` (a `Stop` hook), `continuous-learning`'s `evaluate-session.sh` (also `Stop`),
and the governance-capture / config-protection / fact-force hooks in `hooks.json` all require
hooks to be wired into `~/.claude/settings.json`, and there is no such file on this machine
registering them (checked: `.claude/settings.json` does not exist in the Alfred worktree
either — confirmed by `cat` returning "No such file or directory"). So today, none of ECC's hook
surface fires for either the ECC install or inside Alfred.

**Classification: TEMPORARY COMPATIBILITY at best, more likely REMOVE/REPLACE.** If Alfred wants
any of this behavior (session-end learning capture, rationalization detection), it needs its own
hook wiring decision — inheriting ECC's declined-by-default consent state is not something to
build on. The **event vocabulary itself** (`PreToolUse`/`PostToolUse`/`Stop`/`SessionStart`/
`SessionEnd`/`PreCompact`/`PostToolUseFailure`) is a Claude Code platform contract, not an ECC
invention — **SHARED CONTRACT is the wrong bucket for it** (nobody owns it; it's upstream Claude
Code's), so this audit does not classify the vocabulary itself, only ECC's scripts riding on it,
which are REMOVE/REPLACE (dead in the current install) or ECC-NATIVE-consult (design reference
for what an Alfred-owned Stop hook could look like).

---

## 4. Schemas (11) — SHARED CONTRACT candidates

Read all 11 files under `ECC-SRC:schemas/`. Findings for the four the ticket flags as
load-bearing:

- **`memory.schema.json`** (`ECC-SRC:schemas/memory.schema.json:1-60`): `$id: "ecc.memory.v1"`,
  required fields include `schema, id, title, kind, scope, trust, status, sourceHarness,
  targetHarnesses, tags, links, createdAt, updatedAt, body`. `trust` is an enum with **exactly one
  legal value, `"unreviewed"`** (line 58-60) — the schema itself asserts vault memories can never
  be marked reviewed/trusted; promotion out of the vault is described as an out-of-band process
  ("Governed truth is promoted into a canonical project artifact outside the vault," line 57),
  not something this schema models. **Classification: SHARED CONTRACT candidate, but narrow** —
  useful only for the "unreviewed scratch memory" tier; it cannot represent Alfred's ADR log or
  provenance stamps (those are governed, reviewed, and this schema structurally forbids
  representing that state).

- **`provenance.schema.json`** (`ECC-SRC:schemas/provenance.schema.json:1-27`): title "Skill
  Provenance" — `source, created_at, confidence (0-1), author`, required for
  `~/.claude/skills/learned/*` and `~/.claude/skills/imported/*`. **This is a name collision, not
  a shared concept.** Alfred's `src/provenance/` (protected path) is a cryptographic,
  versioned result-stamping system for AV metric results — reading `src/provenance/stamp.py:1-13`:
  "Cannot be retrofitted... there is no way, afterwards, to say which formula version and which
  assumptions produced it"; stamps are read via `provenance.verify` with explicit
  version-dispatch (`stamp_schema_version`) and old schema modules are "never edited — the same
  discipline as the ADR log." ECC's `provenance.schema.json` is a 4-field skill-attribution note
  with a fuzzy `confidence` float, no hashing, no versioning discipline, no content-addressing.
  **Classification: REMOVE/REPLACE (do not conflate) — the two "provenance" concepts must never
  share a name or a contract inside Alfred; this is exactly the kind of undocumented-internal
  collision §27 warns about.** If ECC's skill-attribution metadata is wanted at all, it needs its
  own field name inside Alfred's docs (e.g. `skill_origin`), never `provenance`.

- **`state-store.schema.json`** (`ECC-SRC:schemas/state-store.schema.json:1-35`): top-level
  arrays `sessions, skillRuns, skillVersions, decisions, installState, governanceEvents,
  workItems` — this is ECC's own local install/session bookkeeping (skill install tracking,
  governance event log), not a task/graph state machine. **Classification: DERIVED READ MODEL at
  most** — Alfred could read this file (if ECC ever runs alongside it) to show "what ECC skills
  fired in this session" in Mission Control, but it is not something Alfred should write to or
  treat as its own state authority (Alfred already has one: Postgres + evidence store, per the
  map issue's out-of-scope list).

- **`hooks.schema.json`** (`ECC-SRC:schemas/hooks.schema.json:1-40`): this is a schema *for
  Claude Code's own settings.json hooks block* ("Configuration for Claude Code hooks... Supports
  current Claude Code hook events"), not an ECC-specific contract. **Not classifiable as an
  ECC capability at all** — it documents the upstream platform surface ECC happens to also
  target. Excluded from the seven-bucket classification for the same reason as the hook event
  vocabulary in §3.

The remaining 7 schemas (`ecc-install-config`, `install-components`, `install-modules`,
`install-profiles`, `install-state`, `package-manager`, `plugin`) are ECC's own installer/plugin
bookkeeping — **ECC-NATIVE**, irrelevant to Alfred unless Alfred formally adopts the ECC installer
as its skill-install mechanism, which is a separate, not-yet-made decision.

---

## 5. Adversarial findings (both lists required non-empty and specific)

### (a) Where ECC is genuinely stronger — real gaps in Alfred

1. **Language/framework-specific build-error-resolution agents.** ECC ships ~15 dedicated
   `*-build-resolver` agents (`ECC-SRC:agents/rust-build-resolver.md`, `go-build-resolver.md`,
   `python...` via `pytorch-build-resolver.md`, etc.) with narrow, tuned prompts per toolchain.
   Alfred has no equivalent prompt library for "diagnose and fix this specific compiler/linker
   error class." This is a real, if narrow, gap — worth adopting as ECC-NATIVE-consult prompt
   scaffolding, version-pinned, never as running code.
2. **`delivery-gate`'s rationalization-phrase detector** (`ECC-SRC:skills/delivery-gate/hooks/
   quality-gate.py:22-27`) catches a failure mode Alfred's harness does not: an agent *saying in
   its own output* that it skipped or excused failing work, independent of whether the harness
   criteria caught the underlying defect. Alfred's verification is execution-based (did the test
   pass) and has no equivalent check on the agent's own natural-language self-report. This is a
   real, specific gap — a lightweight Stop-hook regex scan over agent transcripts is a genuinely
   different signal than a criterion-runner verdict, and Alfred has nothing in this class today.
3. **`continuous-learning`'s session-pattern extraction loop** (`ECC-SRC:skills/
   continuous-learning/evaluate-session.sh` + `config.json`) is a working (if crude) mechanism for
   turning repeated debugging patterns into reusable skill files automatically. Alfred's memory
   story (per the map issue's "Not yet specified" list) has no automated pattern-capture
   mechanism at all today — everything is hand-authored (ADRs, plan). The *mechanism* (not the
   unreviewed-trust output) is a legitimate gap.

### (b) Where Alfred is genuinely stronger — real ECC weaknesses found by reading its code

1. **Provenance: Alfred's is cryptographically load-bearing; ECC's is a soft float.** ECC's
   `provenance.schema.json` provenance is a `confidence: 0-1` number with no hashing and no
   version-dispatch discipline — a skill's "provenance" can be edited freely since it's just
   metadata attached to a markdown file. Alfred's `src/provenance/stamp.py` explicitly forbids
   retrofitting, requires reading `stamp_schema_version` before validating, and forbids editing
   old schema modules once frozen (`stamp.py:8-13`). ECC's model cannot detect a doctored or
   backdated provenance claim; Alfred's is designed so that it structurally cannot be forged
   without changing the hash.
2. **Memory trust model: ECC's is a dead end by design; Alfred has a graduation path.**
   `memory.schema.json`'s `trust` enum has exactly one legal value, `"unreviewed"`
   (`memory.schema.json:57-60`) — there is no schema-level way to mark a memory reviewed or
   governed; the schema's own comment says promotion happens "outside the vault," i.e., outside
   the system this schema describes. Alfred's ADR log has an explicit, enforced state machine
   (`accepted → superseded`, sequential numbering, frozen text) that *is* the governance
   mechanism, not an escape hatch from one.
3. **Verification: ECC's delivery gate is a string-match heuristic; Alfred's harness executes
   real tests against declared, versioned thresholds.** `quality-gate.py`'s `RATIONALIZE` regex
   list (lines 22-27) is four hand-written patterns matching English phrases like "skipping tests
   for now" — it is defeated by any rephrasing, and it says nothing about whether the code
   actually works. Alfred's `tests/heldout/` (composed and perturbed held-out criteria, "never in
   agent context" per `policy/protected-paths.json`) plus `src/thresholds/` (declared, cited,
   versioned, never agent-authored) test actual behavior against actual numeric criteria. ECC has
   no equivalent to a held-out, perturbation-resistant test suite anywhere in the skills or agents
   read for this audit.
4. **Orchestration state: ECC's "autonomous-loops"/"continuous-agent-loop" skills are prose;
   Alfred's topology is a hand-authored, generator-lintable JSON artifact.** No file under
   `skills/continuous-agent-loop/` or `skills/autonomous-loops/` contains anything beyond
   `SKILL.md` prose (confirmed by directory listing) — there is no scheduler, dependency graph, or
   state persistence in ECC's own source for this category. Alfred's `orchestration/topology.json`
   is a real, protected, versioned artifact with its own render pipeline
   (`orchestration/orchestration-canvas.html`, `orchestration/orchestration-graph.svg`).
5. **ECC2's worktree/session Rust module is a second control plane, not a stronger one.**
   `ecc2/src/worktree/mod.rs` is 2,677 lines of real Rust implementing its own git-worktree
   lifecycle and session management (`ecc2/src/session/{runtime,store,manager,daemon,output}.rs`).
   This is substantial working code, but adopting it as Alfred's runtime would be exactly the
   "second control plane" the map issue rules out ("Alfred already has one (Postgres, evidence
   store, gates)... Adopting ECC2 as runtime would be the second control plane §26 forbids").
   Alfred's worktree/land-or-delete and Gate E discipline (referenced in the map issue's "Not yet
   specified" list) is the one that must survive; ECC2's is not weaker in isolation, but adopting
   it would violate the stated architectural boundary, which functionally makes Alfred's approach
   the only admissible one here.

---

## 6. Classification summary

Counting the units discussed above (agent roster as one line-item family, each schema
individually, each skill-category group individually, hooks as one line-item, plus the
individually-called-out entries):

| Bucket | Count | Representative entries |
|---|---|---|
| ALFRED-NATIVE | 7 | TDD/verification execution, docs/vault generation, browser QA & repo onboarding categories (ECC prompt-only vs. Alfred's generated artifacts), orchestration topology, ADR log, debugging/testing categories |
| ECC-NATIVE (consult only, no runtime) | 8 | 68-agent roster as a whole, security-reviewer category, build-error-resolvers, autonomous-loop prompt patterns, browser-qa/repo-scan/codehealth-mcp prompt skills, production-audit category, non-Python language reviewers, installer/plugin schemas (7 of the 11) |
| ALFRED-ADAPTER | 0 | none found — every ECC capability examined is either pure prompt text (no adapter target) or structurally incompatible (would need REMOVE/REPLACE, not a wrapper) |
| SHARED CONTRACT | 2 | `memory.schema.json` (narrow, unreviewed-tier only), `state-store.schema.json` (read-only) |
| DERIVED READ MODEL | 1 | `state-store.schema.json`'s session/skillRun/governanceEvent data, if ECC ever runs alongside Alfred |
| TEMPORARY COMPATIBILITY | 1 | ECC's hook scripts, contingent on a future explicit hook-consent decision — currently inert (`hookConsent: declined`) |
| REMOVE/REPLACE | 5 | `architecture-decision-records` skill, `provenance.schema.json` (name/concept collision), `delivery-gate`'s gate role (not its detector signal, see 5a-2), `continuous-learning`'s auto-write-skills behavior, ECC2's worktree/session Rust module as a runtime |

(Note: `hooks.schema.json` and the seven-event hook vocabulary are explicitly *not* classified —
they document upstream Claude Code platform surface, not an ECC capability; see §3 and §4.)

## 7. Surprises

- The ticket's "Agents (11)" figure does not match anything found in the source; the real count
  is 68, and none are installed on this machine at all (0 of 68).
- `codehealth-mcp` — despite the name implying an MCP server integration — is a single
  prompt-only `SKILL.md` with no MCP wiring in the source tree.
- ECC's own hooks are inert on this machine right now (`hookConsent: declined`), which means any
  ADR or design work that assumes ECC's Stop/PreToolUse hooks are "available today" is describing
  a capability that has to be turned on first, not one that already runs.
- The two systems both use the word "provenance" for structurally unrelated concepts (a soft
  confidence float on a learned skill vs. a cryptographically-versioned metric-result stamp) —
  this is exactly the kind of undocumented-internal-dependency risk §27 warns about, and it means
  the word "provenance" cannot be used unqualified in any future ADR that touches both systems.
