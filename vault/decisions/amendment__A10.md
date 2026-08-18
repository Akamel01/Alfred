---
kind: amendment
id: "amendment:A10"
title: "Deterministic pre-review gate"
shape: "table-row"
number: "A10"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:184"
extractor: "amendments"
aliases:
  - "A10"
  - "Deterministic pre-review gate"
generated: true
---

# Deterministic pre-review gate

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:184`

## Statement

**Deterministic pre-review gate** rejecting any diff introducing non-ASCII control, zero-width or bidi characters outside declared string literals — with particular force on agent-instruction files. Hash-lock the full dependency closure; scan for `.pth`, `sitecustomize` and instruction-file additions.

## Fields

| Field | Value |
|---|---|
| `evidence` | TrapDoor planted `CLAUDE.md` and `.cursorrules` with zero-width-encoded instructions and opened PRs against LangChain, MetaGPT and OpenHands. GitHub flags bidi but not zero-width. Also: CI runs before any human sees the PR, so review is not the first gate. |
