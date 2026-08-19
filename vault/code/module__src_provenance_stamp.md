---
kind: module
id: "module:src.provenance.stamp"
title: "Result stamping — the shape in which a number leaves the system."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/provenance/stamp.py:1"
extractor: "code"
aliases:
  - "Result stamping — the shape in which a number leaves the system."
  - "src.provenance.stamp"
generated: true
---

# Result stamping — the shape in which a number leaves the system.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/provenance/stamp.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/provenance/stamp.py |
| `tree` | src |

## Binds

- [[module__src_provenance|src.provenance]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — # `value` uses the ADR-0001 tagged form because ACS-1 refuses a raw
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """Result stamping — the shape in which a number leaves the system.

Cannot be retrofitted. A result computed before the
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # old documents against a new model, which is the thing ADR-0006 forbids outright.
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """A metric value that can be re-derived and, if necessary, recalled.

    The only shape in which a number leaves the s
- [[adr__ADR-0016|`StampedResult` takes its schema version from the stamp it contains]] **enforced_by** → this — """A metric value that can be re-derived and, if necessary, recalled.

    The only shape in which a number leaves the s
