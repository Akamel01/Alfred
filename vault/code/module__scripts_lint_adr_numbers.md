---
kind: module
id: "module:scripts.lint_adr_numbers"
title: "ADR number claim lint: a branch may not claim a number the base has issued."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_adr_numbers.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "ADR number claim lint: a branch may not claim a number the base has issued."
  - "scripts.lint_adr_numbers"
generated: true
---

# ADR number claim lint: a branch may not claim a number the base has issued.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_adr_numbers.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_adr_numbers.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_06|ADR numbers are claimed once]] **runs** → this
- [[gate-step__integrity_07|ADR number lint detects planted collisions]] **runs** → this

## Enforced by (code)

- [[adr__ADR-0040|The structure fence grows to eighteen]] **enforced_by** → this — #: that record's claim. ADR-0052 is the instance — it quotes ADR-0040's line while explaining
- [[adr__ADR-0040|The structure fence grows to eighteen]] **enforced_by** → this — """The record's effective ordinal claim: the **last** one across its claim sites.

    Last, not first, because the log 
- [[adr__ADR-0052|The D28 waiver ordinal becomes derived, and ADR-0040's is corrected in place]] **enforced_by** → this — #: that record's claim. ADR-0052 is the instance — it quotes ADR-0040's line while explaining
- [[adr__ADR-0052|The D28 waiver ordinal becomes derived, and ADR-0040's is corrected in place]] **enforced_by** → this — #     outside a blockquote is not making that claim. ADR-0052 is the live instance,
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — """ADR number claim lint: a branch may not claim a number the base has issued.

The ADR log is append-only in one file, 
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — #: declaration from the body's prose `**D28 waiver**`, which carries no colon.
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — r"\*\*D28 waiver:\*\*\s*(yes|no)\b"
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — #: `**D28 waiver:**` header field. It scopes where an ordinal counts as a *claim*: without
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — "**D28 waiver**"
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — """The paragraphs of a record in which an ordinal counts as a claim.

    Two shapes, and nothing else. A paragraph carr
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — """The ADR numbers declaring `D28 waiver: yes`, in numeric order.

    This list *is* the count the operating principles
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — """The D28 waiver ordinal as a derived value rather than an asserted one.

    Four sites in the log each say the waiver
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — """A planted log whose records carry a `D28 waiver` header and, optionally, an ordinal
    claim and an appended correct
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — "This is a **D28 waiver** and counts toward the waiver total the operating "
