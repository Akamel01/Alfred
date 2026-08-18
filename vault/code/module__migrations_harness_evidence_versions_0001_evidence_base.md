---
kind: module
id: "module:migrations.harness.evidence.versions.0001_evidence_base"
title: "evidence: run records, verdicts, operator actions, artifacts, defect escapes."
shape: "file"
present: "true"
protected: "false"
lint_gated: "false"
source: "migrations/harness/evidence/versions/0001_evidence_base.py:1"
extractor: "code"
aliases:
  - "evidence: run records, verdicts, operator actions, artifacts, defect escapes."
  - "migrations.harness.evidence.versions.0001_evidence_base"
generated: true
---

# evidence: run records, verdicts, operator actions, artifacts, defect escapes.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/harness/evidence/versions/0001_evidence_base.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | migrations/harness/evidence/versions/0001_evidence_base.py |
| `tree` | migrations |

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — # hash, over ACS-1, and ADR-0003 treats them as two different problems.
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — # Sole author is CriterionRunner (D5, D39), and that is a grant, not a check in
- [[decision__D5|The harness executes checks, never the agent]] **enforced_by** → this — # Sole author is CriterionRunner (D5, D39), and that is a grant, not a check in
- [[decision__D51|Mission control exists, it is split, and every operator action is an evidence row]] **enforced_by** → this — # D51. The one actor who can override every gate becomes an audited writer.
- [[decision__D56|Defect-escape recording starts at the first merge, not at Phase 4]] **enforced_by** → this — # `defect_escape` is here because D56 starts it at the first merge, and because nothing
