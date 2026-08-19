---
kind: module
id: "module:src.provenance.upstream"
title: "`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006)."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/provenance/upstream.py:1"
extractor: "code"
aliases:
  - "`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006)."
  - "src.provenance.upstream"
generated: true
---

# `UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/provenance/upstream.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/provenance/upstream.py |
| `tree` | src |

## Binds

- [[module__src_provenance|src.provenance]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0002|Reason-code width, and what the integer is allowed to be]] **enforced_by** → this — """Why the upstream toolchain could not be determined.

    A small closed set of **names**. ADR-0002's discipline: name
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).

The stamp names *Alfred's* `metr
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # The domain-separation tag allocated by ADR-0006 for the canonicalized upstream
- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — """There *was* an upstream toolchain and Alfred could not determine it.

    A defect-grade state: a stamp carrying this
- [[decision__D30|The product is a re-derivability layer for computed criticality metrics]] **enforced_by** → this — """`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).

The stamp names *Alfred's* `metr
- [[decision__D48|Alfred's buyer is the AV developer's own simulation/V&V function, not a regulator and not ]] **enforced_by** → this — """`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).

The stamp names *Alfred's* `metr
