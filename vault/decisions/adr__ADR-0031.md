---
kind: adr
id: "adr:ADR-0031"
title: "The protected set is one file, and the gate protects its own policy"
status: "accepted"
shape: "heading"
date: "2026-08-19"
source: "docs/tier1/adr-log.md:3275"
extractor: "adrs"
aliases:
  - "ADR-0031"
  - "The protected set is one file, and the gate protects its own policy"
generated: true
---

# The protected set is one file, and the gate protects its own policy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:3275`

## Statement

**Date:** 2026-08-19 · **Status:** Accepted · **Supersedes:** nothing; amends one row of the tier4 table

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- [[adr__ADR-0033|The structure fence names every top-level directory, and the vault floors it]] **see_also** → this
- [[adr__ADR-0035|The protected set's single home names its fourth shape as a projection, not a second autho]] **see_also** → this
- [[adr__ADR-0039|Orchestration Canvas: Protected Topology Source & Palette Binding]] **see_also** → this
- [[adr__ADR-0040|The structure fence grows to eighteen]] **see_also** → this
- [[adr__ADR-0046|Registry additions to the register generators are inspector patches, and carry this ADR]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__harness_patch_test_protected_set|The protected set is policy configuration, and the policy is one home (ADR-0031).]] — """The protected set is policy configuration, and the policy is one home (ADR-0031).

Three things must agree: `policy/p
- **enforced_by** → [[module__harness_patch_validate|Validates a patch before anything touches a tree. Runs outside the container.]] — """Validates a patch before anything touches a tree. Runs outside the container.

A2: the container holds no VCS credent
- **enforced_by** → [[module__harness_patch_validate|Validates a patch before anything touches a tree. Runs outside the container.]] — # The protected set as policy configuration (ADR-0031). The file is under `policy/` —
- **enforced_by** → [[module__scripts__lintkit|Shared machinery for the lints in `scripts/`, moved out of their siblings.]] — """Shared machinery for the lints in `scripts/`, moved out of their siblings.

Each piece here ran verbatim, or near eno
