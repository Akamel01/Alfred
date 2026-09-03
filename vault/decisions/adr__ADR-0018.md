---
kind: adr
id: "adr:ADR-0018"
title: "The executor moved, and eleven of thirteen premises were wrong"
status: "accepted"
shape: "heading"
date: "2026-08-18"
source: "docs/tier1/adr-log.md:1731"
extractor: "adrs"
aliases:
  - "ADR-0018"
  - "The executor moved, and eleven of thirteen premises were wrong"
generated: true
---

# The executor moved, and eleven of thirteen premises were wrong

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1731`

## Statement

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** D38's selection target; the Sandbox Specification's C1, C2, C3, C5 and C10 rows · **Discharges:** O5 · **See also:** ADR-0007 (the vacuity this prevented), ADR-0017 (the shells that held the holes)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **discharges** → [[operator-item__O5|~~Read OpenHands at the pinned SHA~~]]
- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0017|A containment assertion with an unread premise is a hole, and a hole never passes]]
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **amends** → this
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **see_also** → this
- [[adr__ADR-0020|The run fingerprint record, and the two assertions that were waiting on it]] **see_also** → this
- [[adr__ADR-0036|Run Fingerprint Record Schema & Production]] **see_also** → this
- [[adr__ADR-0044|Register drift reconciled]] **see_also** → this
- [[adr__ADR-0045|The ECC coupling is factory scope, ring-fenced, and overrides no gate]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__harness_containment___init__|Containment assertions: what the sandbox must prove before a run starts.]] — """Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion 
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — """The executor-premise assertions, and the source read that filled their holes (O5).

C1, C2, C3, C5 and C10 rest on th
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — # and rejected rather than overlooked (ADR-0018).
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — "resolved 2026-08-18; see ADR-0018"
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """ADR-0018. D38 names the repository that is now Agent Canvas, which is not the executor."""
- **enforced_by** → [[module__harness_fingerprint___init__|The run fingerprint record — the declared configuration a run is measured on.]] — """The run fingerprint record — the declared configuration a run is measured on.

Inspector machinery (D20). `record.py`
- **enforced_by** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]] — """The run fingerprint record: what a run was measured on, stated once and hashed.

Two containment assertions could not
