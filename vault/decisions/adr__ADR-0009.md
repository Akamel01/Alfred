---
kind: adr
id: "adr:ADR-0009"
title: "The grant matrix is asserted by set equality, and converging by REVOKE strips ownership"
status: "accepted"
shape: "heading"
date: "2026-08-17"
source: "docs/tier1/adr-log.md:856"
extractor: "adrs"
aliases:
  - "ADR-0009"
  - "The grant matrix is asserted by set equality, and converging by REVOKE strips ownership"
generated: true
---

# The grant matrix is asserted by set equality, and converging by REVOKE strips ownership

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:856`

## Statement

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Enforced by (code)

- **enforced_by** → [[module__harness_patch_test_protected_set|The protected set is policy configuration, and the policy is one home (ADR-0031).]] — """The protected set is policy configuration, and the policy is one home (ADR-0031).

Three things must agree: `policy/p
