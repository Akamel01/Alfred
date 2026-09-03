---
status:        provisional
owner:         human
enforcement:   none
evidence:      A single install performed 2026-09-02 on one machine, with a pre-install inventory captured by hash and a dry-run diffed before apply. Nothing here is measured across machines or across ECC versions.
falsifies_if:  A second install of the same profile and commit produces a different operation set, or ECC hook runtime appears under ~/.claude without an explicit consent decision recorded.
review_after:  the harness-portability decision
---

# ECC install for Claude Code — what was done and what it changed

Resolves [Install ECC natively for Claude Code](https://github.com/Akamel01/Alfred/issues/49),
a child of [wayfinder:map — Alfred × ECC: one factory](https://github.com/Akamel01/Alfred/issues/41).

This is a **task** record, not a decision. It states what was done and the facts later
tickets depend on. It changes nothing inside the Alfred repository.

## What was installed

| | |
|---|---|
| Target | `claude` → `~/.claude/` (installer's default home target) |
| Profile | `minimal` |
| Source | ECC 2.2.1, commit `ca185ef5f7667078a1e70a763bd3a9c71c48acf0` |
| Install state | `~/.claude/ecc/install-state.json` (`schemaVersion: ecc.install.v1`) |
| Modules | `rules-core`, `agents-core`, `commands-core`, `platform-configs`, `skill-unified-memory`, `workflow-quality` |
| Operations | 488, all `copy-file` |

`minimal` was chosen because the manifest describes it as the low-context Claude Code
setup "**but no hook runtime**" (`manifests/install-profiles.json`). It is the only
profile that targets Claude Code and excludes `hooks-runtime`; every other Claude-facing
profile (`core`, `developer`, `security`, `research`) includes it. The profile name was
read from the manifest, not guessed.

`skill-unified-memory` was pulled in as a dependency of the requested set — it was not
requested explicitly and was not in the profile's declared module list.

## Pre-install inventory — the three lists

Captured by SHA-256 of each `SKILL.md` against ECC upstream **before** the install, because
that state is unrecoverable afterwards. 286 upstream skills, 179 local skill directories.

| List | Count | Contents |
|---|---|---|
| (a) ECC upstream, unmodified | **0** | — |
| (b) ECC upstream, locally modified | **1** | `design-system` |
| (c) Purely local, not in ECC upstream | **178** | everything else |

**This corrects a claim made while charting the map.** The map's ECC-install decision line
asserts that a visible subset of `~/.claude/skills` was already ECC-derived, naming
`caveman`, `ponytail`, `wayfinder`, `grill-with-docs`, `triage`, and `icm-architect`. That
is wrong: ECC upstream contains none of those six. They come from the caveman/ponytail
plugins and from a separately-installed skill set. The two skill populations were very
nearly **disjoint**, not overlapping — collision surface was exactly one skill.

`design-system` was **not overwritten**: the `minimal` profile does not carry it, so the
one possible collision never arose. The local version is byte-identical to its pre-install
state.

## Safety verification

A dry-run was captured and diffed against the filesystem before applying.

- **Operations that would overwrite an existing file: 0.** Every one of the 488 copies
  landed on a path that did not previously exist.
- **`settings.json`: untouched by the installer.** It did change during the session, by
  one line (`includeCoAuthoredBy: false`), written by the Claude Code harness itself and
  unrelated to ECC. `settings.local.json` unchanged.
- **No hook runtime installed.** `~/.claude/hooks` does not exist. No `session-start.js`
  and no `hooks.json` anywhere under `~/.claude`.
- **No skills removed.** 179 → 227 directories; 48 added, 0 deleted.
- The 42 dry-run destinations matching `hook` are all `rules/ecc/<language>/hooks.md` —
  documentation about framework lifecycle hooks, not runtime hook configuration.

### The instincts gate

The memory-boundary research ([issue #50](https://github.com/Akamel01/Alfred/issues/50))
found the highest-severity risk in this coupling: an "instincts" system that auto-injects
self-scored, agent-authored, directive-shaped `## Action` text into every new session's
context, gated only by a confidence float the writing agent influences.

The `workflow-quality` module **does** install the instinct authoring surface —
`skills/continuous-learning-v2/scripts/instinct-cli.py`, `lib/homunculus-dir.sh`,
`migrate-homunculus.sh`. The **injection** path is `scripts/hooks/session-start.js`, which
lives in `hooks-runtime` and was not selected.

So the posture is: **authoring capability present, injection path absent.** Verified — no
`session-start.js` exists under `~/.claude`. This is the concrete reason hooks stay off,
and it is why any future decision to enable `hooks-runtime` on this target is a security
decision, not a convenience one.

**One gap worth naming:** the install state records `"hookConsent": null`, not
`"declined"`. Consent was never *asked*, because `minimal` excludes the module rather than
prompting. Functionally hooks are absent; the record does not say they were refused. A
later reader of `install-state.json` cannot distinguish "declined" from "never asked".

## What is now portable across both harnesses

| Surface | OpenCode (`~/.config/opencode`) | Claude Code (`~/.claude`) |
|---|---|---|
| Profile | `opencode` | `minimal` |
| Modules | 4 | 6 |
| ECC skills | 56 | 48 added (227 total dirs) |
| ECC agents | 11 | 68 |
| ECC commands | 113 | 110 |
| `rules/ecc` | — | 122 files |
| Hook runtime | absent (`hookConsent: declined`) | absent (`hookConsent: null`) |

Both targets now run the same ECC commit with recorded install state, so **drift between
them is detectable** — which is the property §27 of the brief asks for and which did not
exist before this install.

The two module sets are **not** identical (`rules-core` and `agents-core` are Claude-only;
both carry `workflow-quality` and `skill-unified-memory`). A skill id present on one target
is not automatically present on the other. Portability is now *measurable*, not *achieved*.

## Reversibility

A full pre-install backup of `~/.claude/skills`, `settings.json`, `settings.local.json`,
`CLAUDE.md`, and the inventory JSON is at
`~/.claude/_ecc-preinstall-backup-20260902-215034` (17 MB). It is machine-local and is not
part of any repository.

## Facts later tickets depend on

- ECC agents are now resolvable as Claude Code subagent types (68 of them). This is a real
  behaviour change to every session on this machine, and it is what makes
  [Role bindings](https://github.com/Akamel01/Alfred/issues/43) actionable.
- The capability audit's finding stands and is reinforced: what landed is **prompt text and
  agent definitions**, plus a small number of helper scripts. No runtime, no daemon, no
  control plane. `ALFRED-ADAPTER` still has no target.
- Enabling `hooks-runtime` on either target is an open security decision, not a default.
