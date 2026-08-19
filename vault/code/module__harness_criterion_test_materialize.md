---
kind: module
id: "module:harness.criterion.test_materialize"
title: "A1, asserted as an architectural claim rather than as a list of blocked filenames."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/criterion/test_materialize.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "A1, asserted as an architectural claim rather than as a list of blocked filenames."
  - "harness.criterion.test_materialize"
generated: true
---

# A1, asserted as an architectural claim rather than as a list of blocked filenames.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/criterion/test_materialize.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/criterion/test_materialize.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_criterion_materialize|Build the criterion environment from an allowlist, never from the candidate tree.]]
- [[module__harness_criterion|harness.criterion]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0015|A missing candidate file is the candidate's failure, not the harness's fault]] **enforced_by** → this — """Fail closed on a typo in the harness's own declaration.

    A trusted declaration naming a path that is not there ma
- [[adr__ADR-0015|A missing candidate file is the candidate's failure, not the harness's fault]] **enforced_by** → this — """The candidate did not write it. That is an outcome, not a harness fault.

    Raising here surfaces to the caller as 
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """A1, asserted as an architectural claim rather than as a list of blocked filenames.

**How this suite would be shown v
