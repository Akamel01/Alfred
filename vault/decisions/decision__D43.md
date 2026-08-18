---
kind: decision
id: "decision:D43"
title: "Evidence durability and tamper evidence"
shape: "bold-paragraph"
number: "43"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:422"
extractor: "decisions"
aliases:
  - "D43"
  - "Evidence durability and tamper evidence"
generated: true
---

# Evidence durability and tamper evidence

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:422`

## Statement

**Decision 43 — Evidence durability and tamper evidence.** Append-only is an integrity property against the agent; it does nothing against SSD failure on a 24/7 consumer machine, kernel-panic corruption (a failure mode this plan itself documents), or a bad migration — and hardware loss and total evidence loss are currently the same event. Fix, added to cross-stage invariants: continuous WAL archiving + periodic base backups of Postgres and the artifact store to an **off-machine** target; a **restore drill** as an executable check, with "restore verified" a Phase 0 exit criterion beside "deploy

## Enforced by (code)

- **enforced_by** → [[module__harness_evidence_anchor|The chain head, recorded off-machine, and derived by the implementation that is not Python]] — """The chain head, recorded off-machine, and derived by the implementation that is not Python.

D43 anchors the chain he
