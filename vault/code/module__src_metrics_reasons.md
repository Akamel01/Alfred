---
kind: module
id: "module:src.metrics.reasons"
title: "The global reason codebook (ADR-0001 consequences, ADR-0002)."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/metrics/reasons.py:1"
extractor: "code"
aliases:
  - "The global reason codebook (ADR-0001 consequences, ADR-0002)."
  - "src.metrics.reasons"
generated: true
---

# The global reason codebook (ADR-0001 consequences, ADR-0002).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/metrics/reasons.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/metrics/reasons.py |
| `tree` | src |

## Binds

- [[module__src_metrics|src.metrics]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """The global reason codebook (ADR-0001 consequences, ADR-0002).

One enum for the whole system. Codes enumerate *kinds 
- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """Decode a stored integer. Unrecognized codes become `UNKNOWN_CODE`, never `DEFINED`.

    This is the single most impo
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """The global reason codebook (ADR-0001 consequences, ADR-0002).

One enum for the whole system. Codes enumerate *kinds 
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — # The build fails here rather than at 254 (ADR-0002). A ceiling discovered at
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """The codebook violates an ADR-0002 invariant. Fails the build, not a run."""
- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """Assert every ADR-0002 invariant. Raises `CodebookError` on the first breach.

    Both mappings are arguments so the 
