---
kind: module
id: "module:tests.test_provenance"
title: "Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004)."
shape: "file"
present: "true"
protected: "false"
lint_gated: "true"
source: "tests/test_provenance.py:1"
extractor: "code"
aliases:
  - "Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004)."
  - "tests.test_provenance"
generated: true
---

# Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tests/test_provenance.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tests/test_provenance.py |
| `tree` | tests |

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004)."""
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — """Result stamping and its ACS-1 hashing (ADR-0003, ADR-0004)."""
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # Required, with no default and no null arm (ADR-0006). The fixture uses the
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # The two ADR-0006 additions. `stamp_schema_version` is pinned to 1 by the model,
