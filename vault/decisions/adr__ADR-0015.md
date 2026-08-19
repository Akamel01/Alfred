---
kind: adr
id: "adr:ADR-0015"
title: "A missing candidate file is the candidate's failure, not the harness's fault"
status: "accepted"
shape: "heading"
date: "2026-08-18"
source: "docs/tier1/adr-log.md:1442"
extractor: "adrs"
aliases:
  - "A missing candidate file is the candidate's failure, not the harness's fault"
  - "ADR-0015"
generated: true
---

# A missing candidate file is the candidate's failure, not the harness's fault

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1442`

## Statement

**Date:** 2026-08-18 · **Status:** accepted · **Supersedes:** nothing · **Amends:** ADR-0011

## Fields

| Field | Value |
|---|---|
| `status_raw` | accepted |

## Binds

- **amends** → [[adr__ADR-0011|The criterion subprocess computes; the runner compares]]

## Enforced by (code)

- **enforced_by** → [[module__harness_criterion_test_materialize|A1, asserted as an architectural claim rather than as a list of blocked filenames.]] — """Fail closed on a typo in the harness's own declaration.

    A trusted declaration naming a path that is not there ma
- **enforced_by** → [[module__harness_criterion_test_materialize|A1, asserted as an architectural claim rather than as a list of blocked filenames.]] — """The candidate did not write it. That is an outcome, not a harness fault.

    Raising here surfaces to the caller as 
- **enforced_by** → [[module__harness_selftest_test_selftest|S4. The inspector's inspector, and the controls that stop it reading green for free.]] — """The defect this suite found on its first run. `materialize` used to raise on an
    absent candidate path, which a ca
