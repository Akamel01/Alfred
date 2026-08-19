---
kind: adr
id: "adr:ADR-0019"
title: "D38's sandbox rationale, verified: true of one configuration, false of the default"
status: "accepted"
shape: "heading"
date: "2026-08-18"
source: "docs/tier1/adr-log.md:1844"
extractor: "adrs"
aliases:
  - "ADR-0019"
  - "D38's sandbox rationale, verified: true of one configuration, false of the default"
generated: true
---

# D38's sandbox rationale, verified: true of one configuration, false of the default

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1844`

## Statement

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** D38's sandbox rationale; ADR-0018's outstanding list · **See also:** ADR-0018 (which recorded this as unverified), ADR-0017 (the shells), ADR-0007 (the vacuity being avoided)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]]
- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0017|A containment assertion with an unread premise is a hole, and a hole never passes]]
- **see_also** → [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]]
- [[adr__ADR-0020|The run fingerprint record, and the two assertions that were waiting on it]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — """Persistence configured, and every observed event durable at end of run.

    **The premise inverted at O5.** The rese
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — """The agent is running in the container at all.

    **Every other executor-premise assertion assumes this and none of 
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — """The ingress surface and the launch posture — the half of ADR-0019 nothing covered.

    ADR-0019 recorded four unhard
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — "Not in the specification, and it falsified C1 as written (ADR-0019). It "
- **enforced_by** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] — "ADR-0019; not re-read here, and the citation is what makes that checkable."
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — """ADR-0019. The default removes the conversation directory; C1 was reading it after."""
- **enforced_by** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] — # ADR-0019 point 1: the default is an empty list, and empty means unsecured.
- **enforced_by** → [[module__harness_fingerprint___init__|The run fingerprint record — the declared configuration a run is measured on.]] — """The run fingerprint record — the declared configuration a run is measured on.

Inspector machinery (D20). `record.py`
- **enforced_by** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]] — """The run fingerprint record: what a run was measured on, stated once and hashed.

Two containment assertions could not
