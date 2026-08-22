---
kind: decision
id: "decision:D39"
title: "structural enforcement of D16/D20 (from gstack, the one idea that stands alone)"
shape: "heading"
number: "39"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:118"
extractor: "decisions"
aliases:
  - "D39"
  - "structural enforcement of D16/D20 (from gstack, the one idea that stands alone)"
generated: true
---

# structural enforcement of D16/D20 (from gstack, the one idea that stands alone)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:118`

## Statement

### Decision 39 — structural enforcement of D16/D20 (from gstack, the one idea that stands alone)

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — D16/D39. LangGraph raises only on *concurrent* unreducered writes, so a
- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — """Sole author of verdicts (D5, D39).

    Holds `alfred_criterion` — the only role with any privilege on `heldout`, and
- **enforced_by** → [[module__harness_db_test_grants|The grant matrix, asserted two ways: by set equality, and by being refused.]] — # The harness may read a verdict and may not write one. D39 makes that physical:
- **enforced_by** → [[module__harness_db_test_grants|The grant matrix, asserted two ways: by set equality, and by being refused.]] — "D39-harness-verdict-insert"
- **enforced_by** → [[module__harness_evidence___init__|The evidence plane's writer.]] — """The evidence plane's writer.

Inspector machinery (D20). Permanently outside what agents may modify, and outside the

- **enforced_by** → [[module__harness_verdicts___init__|The harness's verdict vocabulary: the words, the stamp bridge table, one home.]] — """The harness's verdict vocabulary: the words, the stamp bridge table, one home.

`pass`, `fail`, `indeterminate` — fai
- **enforced_by** → [[module__migrations_harness_evidence_versions_0001_evidence_base|evidence: run records, verdicts, operator actions, artifacts, defect escapes.]] — # Sole author is CriterionRunner (D5, D39), and that is a grant, not a check in
- **enforced_by** → [[module__migrations_roles_002_grants_sql|migrations/roles/002_grants.sql]] — Sole author of verdicts is CriterionRunner (D5, D39). The harness may
- **enforced_by** → [[module__migrations_roles_002_grants_sql|migrations/roles/002_grants.sql]] — read them and may not write them, which is the separation D39 makes
- **enforced_by** → [[module__migrations_roles_grants_yaml|migrations/roles/grants.yaml]] — sole author of verdicts (D5, D39)
- **enforced_by** → [[module__scripts_lint_verdict_boundary|D16/D39: the verdict boundary, enforced structurally rather than by convention.]] — """D16/D39: the verdict boundary, enforced structurally rather than by convention.

**Why this exists as a lint and not 
- **enforced_by** → [[module__src_provenance_verify|The two-stage stamp read, and what a verifier says about a version it does not know.]] — """The two-stage stamp read, and what a verifier says about a version it does not know.

ADR-0006's central property: **
