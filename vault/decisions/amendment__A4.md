---
kind: amendment
id: "amendment:A4"
title: "Delete mutmut from the adversary role"
shape: "table-row"
number: "A4"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:178"
extractor: "amendments"
aliases:
  - "A4"
  - "Delete mutmut from the adversary role"
generated: true
---

# Delete mutmut from the adversary role

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:178`

## Statement

**Delete mutmut from the adversary role.** Retain only as regression on the already-trusted human-built skeleton. Never gate on mutation score in a bug-detection setting.

## Fields

**evidence**

> ISSTA 2026 replication: mutants are generated from the possibly-buggy code and tests failing on the original are excluded, which excludes precisely the bug-exposing tests — "rendering the resulting mutation scores meaningless." Rated **fatal**.
