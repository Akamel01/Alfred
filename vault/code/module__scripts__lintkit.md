---
kind: module
id: "module:scripts._lintkit"
title: "Shared machinery for the lints in `scripts/`, moved out of their siblings."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/_lintkit.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Shared machinery for the lints in `scripts/`, moved out of their siblings."
  - "scripts._lintkit"
generated: true
---

# Shared machinery for the lints in `scripts/`, moved out of their siblings.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/_lintkit.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/_lintkit.py |
| `tree` | scripts |

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """D57. A scan that saw nothing writes its VACUOUS line and fails; returns True then.

    A guard that could pass for f
- [[adr__ADR-0031|The protected set is one file, and the gate protects its own policy]] **enforced_by** → this — """Shared machinery for the lints in `scripts/`, moved out of their siblings.

Each piece here ran verbatim, or near eno
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """Shared machinery for the lints in `scripts/`, moved out of their siblings.

Each piece here ran verbatim, or near eno
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — #: its own copy for the D20 reason above), so a heading one reader cannot parse is a
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Shared machinery for the lints in `scripts/`, moved out of their siblings.

Each piece here ran verbatim, or near eno
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """D57. A scan that saw nothing writes its VACUOUS line and fails; returns True then.

    A guard that could pass for f
