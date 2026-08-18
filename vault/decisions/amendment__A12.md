---
kind: amendment
id: "amendment:A12"
title: "Claude Agent SDK contributes zero security properties"
shape: "table-row"
number: "A12"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:186"
extractor: "amendments"
aliases:
  - "A12"
  - "Claude Agent SDK contributes zero security properties"
generated: true
---

# Claude Agent SDK contributes zero security properties

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:186`

## Statement

**Claude Agent SDK contributes zero security properties** and must run as an untrusted process inside Alfred's own containment. Set every isolation option explicitly; add a startup assertion that no user/project settings loaded. Resolve the Docker-vs-Anthropic-sandbox either/or explicitly.

## Fields

**evidence**

> Anthropic states the action "is not designed to be hardened against prompt injection." Python SDK ≤0.1.59 silently treated `setting_sources=[]` as omitted, loading `~/.claude/settings.json` and `CLAUDE.md` into the agent — a control that failed without signalling. Anthropic's sandbox fails **open** unless `sandbox.failIfUnavailable` is true, and "docker is incompatible with the sandbox."
