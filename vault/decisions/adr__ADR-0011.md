---
kind: adr
id: "adr:ADR-0011"
title: "The criterion subprocess computes; the runner compares"
status: "accepted"
shape: "heading"
date: "2026-08-17"
source: "docs/tier1/adr-log.md:1047"
extractor: "adrs"
aliases:
  - "ADR-0011"
  - "The criterion subprocess computes; the runner compares"
generated: true
---

# The criterion subprocess computes; the runner compares

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1047`

## Statement

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- [[adr__ADR-0015|A missing candidate file is the candidate's failure, not the harness's fault]] **amends** → this

## Enforced by (code)

- **enforced_by** → [[module__harness_selftest_synthetic|A criterion with no domain in it, and a defect that can be dialled.]] — # beside the code under test is D50's delegation failure (ADR-0011).
