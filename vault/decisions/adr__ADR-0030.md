---
kind: adr
id: "adr:ADR-0030"
title: "Two containment controls that existed and did not run, and two that still do not"
shape: "heading"
source: "docs/tier1/adr-log.md:3085"
extractor: "adrs"
aliases:
  - "ADR-0030"
  - "Two containment controls that existed and did not run, and two that still do not"
generated: true
---

# Two containment controls that existed and did not run, and two that still do not

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:3085`

## Statement

**Date** 2026-08-19 · **Status** Accepted · **Supersedes** nothing · **Amends** ADR-0023's

## Enforced by (code)

- **enforced_by** → [[module__harness_containment___init__|Containment assertions: what the sandbox must prove before a run starts.]] — """Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion 
