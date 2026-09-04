---
kind: decision
id: "decision:D28"
title: "Stage gates are executable where measurable; overriding one requires an immutable waiver ADR"
shape: "table-row"
number: "28"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:72"
extractor: "decisions"
aliases:
  - "D28"
  - "Stage gates are executable where measurable; overriding one requires an immutable waiver A"
generated: true
---

# Stage gates are executable where measurable; overriding one requires an immutable waiver ADR

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:72`

## Statement

**Stage gates are executable where measurable; overriding one requires an immutable waiver ADR** recording gate, threshold, actual value, reason, and the condition that would reverse it.

## Fields

**rationale**

> Every forbidden-advancement condition in this plan is a promise made to a future self who will be under pressure and will want to proceed. A gate that can be waived silently is a note, not a gate — but an unwaivable gate gets bypassed entirely rather than adjusted honestly. Making the override expensive and permanent is the realistic control. Waiver count becomes its own health metric. Note this is the only control in the architecture aimed at the human rather than the agents, and it addresses the failure that actually occurred last time.

## Enforced by (code)

- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — """ADR number claim lint: a branch may not claim a number the base has issued.

The ADR log is append-only in one file, 
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — #: declaration from the body's prose `**D28 waiver**`, which carries no colon.
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — r"\*\*D28 waiver:\*\*\s*(yes|no)\b"
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — #: `**D28 waiver:**` header field. It scopes where an ordinal counts as a *claim*: without
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — "**D28 waiver**"
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — """The paragraphs of a record in which an ordinal counts as a claim.

    Two shapes, and nothing else. A paragraph carr
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — """The ADR numbers declaring `D28 waiver: yes`, in numeric order.

    This list *is* the count the operating principles
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — """The D28 waiver ordinal as a derived value rather than an asserted one.

    Four sites in the log each say the waiver
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — """A planted log whose records carry a `D28 waiver` header and, optionally, an ordinal
    claim and an appended correct
- **enforced_by** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]] — "This is a **D28 waiver** and counts toward the waiver total the operating "
