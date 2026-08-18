---
kind: document
id: "document:tier4/sandbox-specification"
title: "Sandbox Specification"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "4"
written: "full"
review_after: "Phase 2"
source: "docs/tier4/sandbox-specification.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier4]
aliases:
  - "Sandbox Specification"
  - "tier4/sandbox-specification"
generated: true
---

# Sandbox Specification

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier4/sandbox-specification.md:1`

## Falsifies if

> A sandbox boots while a known non-allowlisted connection succeeds, or a credential is found reachable from inside the container, or a run reaches a verdict while any assertion in the containment table below was not executed.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier4/sandbox-specification.md |
| `tier_name` | Security and governance |

**evidence**

> Deny-by-default is asserted by a boot-time canary because a major lab's own evaluation harness was found to have left machines with live internet access despite intended isolation. Allowlisted hosts have been used for exfiltration at CVSS 9.6. The executor-specific assertions (C1–C3, C12) rest on the plan's research notes about OpenHands and are **unverified first-hand** — the executor is not present in this repository and was not fetched; each is written to pass harmlessly if the feature it disables does not exist.

## Binds

- [[tier__tier4|Tier 4 — Security and governance]] **contains** → this
