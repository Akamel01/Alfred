---
kind: module
id: "module:migrations.harness.control.versions.0001_control_base"
title: "control: work items, fingerprints, protected paths, thresholds."
shape: "file"
present: "true"
protected: "false"
lint_gated: "false"
source: "migrations/harness/control/versions/0001_control_base.py:1"
extractor: "code"
aliases:
  - "control: work items, fingerprints, protected paths, thresholds."
  - "migrations.harness.control.versions.0001_control_base"
generated: true
---

# control: work items, fingerprints, protected paths, thresholds.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/harness/control/versions/0001_control_base.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | migrations/harness/control/versions/0001_control_base.py |
| `tree` | migrations |

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # changed*. D19's tiered requalification is a decision about which component moved,
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # D19.
- [[decision__D23|Escalation triggers are structural, not agent-judged]] **enforced_by** → this — # The caps the attempt inherits (D23). A task with no retry budget is not
- [[decision__D34|Thresholds are declared, cited, versioned configuration inputs]] **enforced_by** → this — # D34: thresholds are declared, cited, versioned configuration inputs — never
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — # D40. The quantization *artifact* hash, never the quant name: imatrix variants
- [[decision__D49|A grading point is admitted by the provenance of its authorship, not by whether the oracle]] **enforced_by** → this — # Set at authoring time, on the criterion rather than on the run. P1…P5 per D49.
