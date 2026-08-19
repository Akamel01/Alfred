---
kind: adr
id: "adr:ADR-0017"
title: "A containment assertion with an unread premise is a hole, and a hole never passes"
status: "accepted"
shape: "heading"
date: "2026-08-18"
source: "docs/tier1/adr-log.md:1611"
extractor: "adrs"
aliases:
  - "A containment assertion with an unread premise is a hole, and a hole never passes"
  - "ADR-0017"
generated: true
---

# A containment assertion with an unread premise is a hole, and a hole never passes

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1611`

## Statement

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** ADR-0007 (which names the third outcome and does not say how it is represented or acted on) · **See also:** the Sandbox Specification's containment table, whose C1–C3 paragraph this contradicts and which is amended by this record

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]] **see_also** → this
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **see_also** → this
- [[adr__ADR-0020|The run fingerprint record, and the two assertions that were waiting on it]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__harness_containment___init__|Containment assertions: what the sandbox must prove before a run starts.]] — """Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion 
- **enforced_by** → [[module__harness_containment_lane|C11 — the serving lane is the lane the run was dispatched against.]] — """C11 — the serving lane is the lane the run was dispatched against.

Runs **outside**, against the serving layer. The 
