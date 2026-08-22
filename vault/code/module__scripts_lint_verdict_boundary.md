---
kind: module
id: "module:scripts.lint_verdict_boundary"
title: "D16/D39: the verdict boundary, enforced structurally rather than by convention."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_verdict_boundary.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "D16/D39: the verdict boundary, enforced structurally rather than by convention."
  - "scripts.lint_verdict_boundary"
generated: true
---

# D16/D39: the verdict boundary, enforced structurally rather than by convention.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_verdict_boundary.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_verdict_boundary.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_09|Verdict boundary holds]] **runs** → this
- [[gate-step__integrity_10|Verdict boundary lint detects planted violations]] **runs** → this

## Enforced by (code)

- [[decision__D16|Verdict fields are owned by deterministic nodes]] **enforced_by** → this — """D16/D39: the verdict boundary, enforced structurally rather than by convention.

**Why this exists as a lint and not 
- [[decision__D16|Verdict fields are owned by deterministic nodes]] **enforced_by** → this — # The vocabulary D16 forbids an agent-invoking node from naming. Deliberately short:
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — """D16/D39: the verdict boundary, enforced structurally rather than by convention.

**Why this exists as a lint and not 
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — """Plant each violation and require the check to fire; then require it to stay quiet.

    Written as a committed mode r
