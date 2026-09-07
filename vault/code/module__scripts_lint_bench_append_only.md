---
kind: module
id: "module:scripts.lint_bench_append_only"
title: "`bench/results/` and `bench/fingerprints/` are append-only. This is what says so."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/lint_bench_append_only.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "`bench/results/` and `bench/fingerprints/` are append-only. This is what says so."
  - "scripts.lint_bench_append_only"
generated: true
---

# `bench/results/` and `bench/fingerprints/` are append-only. This is what says so.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/lint_bench_append_only.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/lint_bench_append_only.py |
| `tree` | scripts |

## Binds

- [[gate-step__integrity_22|Bench append-only lint checks its own vacuity]] **runs** → this
- [[gate-step__integrity_23|Bench records are append-only (bench/results/, bench/fingerprints/)]] **runs** → this

## Enforced by (code)

- [[adr__ADR-0038|bench Immutability: Convention → Git-Level Control]] **enforced_by** → this — """`bench/results/` and `bench/fingerprints/` are append-only. This is what says so.

ADR-0038 decided *harden* and name
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """`bench/results/` and `bench/fingerprints/` are append-only. This is what says so.

ADR-0038 decided *harden* and name
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Tracked file count under the append-only prefixes, and the per-prefix report.

    The count is what D57 is applied t
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — "modification behind a later commit each fire; an empty corpus trips D57; a "
