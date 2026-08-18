---
kind: amendment
id: "amendment:A2"
title: "No GitHub credential in the agent container"
shape: "table-row"
number: "A2"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:176"
extractor: "amendments"
aliases:
  - "A2"
  - "No GitHub credential in the agent container"
generated: true
---

# No GitHub credential in the agent container

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:176`

## Statement

**No GitHub credential in the agent container.** Container emits a patch file to a mounted volume; a separate uncontaminated process opens the PR. Never `pull_request_target` with head checkout. Disable `actions/cache` on workflows touching agent branches.

## Fields

**evidence**

> Decision 10 was false as written: the deliverable channel and the exfiltration channel were the same channel. AsyncAPI — PR opened 05:08, PAT exfiltrated 05:16, four backdoored npm packages with 3M+ weekly downloads. Actions caches are repository-scoped, so ephemerality fails below the container.
