---
kind: decision
id: "decision:D32"
title: "All 55 documents written as stubs; full content only for the ~12–15 Phase 0 can falsify"
shape: "table-row"
number: "32"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:76"
extractor: "decisions"
aliases:
  - "All 55 documents written as stubs; full content only for the ~12–15 Phase 0 can falsify"
  - "D32"
generated: true
---

# All 55 documents written as stubs; full content only for the ~12–15 Phase 0 can falsify

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:76`

## Statement

**All 55 documents written as stubs; full content only for the ~12–15 Phase 0 can falsify.** A stub is header contract, two-sentence purpose, enforcement mechanism, falsification condition, expiry.

## Fields

**rationale**

> Supersedes decision 17. No study exists on whether a pre-code register helps. The adjacent evidence is actively unfavourable: of 49 agent skills, 39 produced zero improvement, average +1.2%, up to 451% token overhead, and three **degraded** performance up to −10% from version-mismatched guidance — while the seven that gained (up to +30%) did so conditioned on domain alignment and **currency**. A document written before Phase 0 produces evidence cannot be current by construction, so the register's measured benefit depends on a property it cannot yet have, and the downside is negative rather than zero for anything wrong. Stubs preserve the complete map, the schema and the uniformity while keeping speculation out of agent context.

## Enforced by (code)

- **enforced_by** → [[module__harness_patch_validate|Validates a patch before anything touches a tree. Runs outside the container.]] — "content here is read as instructions by a later agent; it is the D32 "
- **enforced_by** → [[module__scripts_gen_doc_stubs|Generate the Alfred documentation register as stubs (D32).]] — """Generate the Alfred documentation register as stubs (D32).

A stub is header contract + two-sentence purpose + enforc
- **enforced_by** → [[module__scripts_gen_doc_stubs|Generate the Alfred documentation register as stubs (D32).]] — """---
status:        {status}
owner:         {owner}
enforcement:   {enforcement}
evidence:      none — written pre-Pha

## Stated in prose — unverified

- **supersedes** → [[decision__D17|The full ~55-document register is written before Phase 0 code]] — Supersedes decision 17
