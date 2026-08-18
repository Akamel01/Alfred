---
kind: module
id: "module:src.domain.trajectory"
title: "Trajectory schemas — the load-bearing abstraction everything downstream reads."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/domain/trajectory.py:1"
extractor: "code"
aliases:
  - "Trajectory schemas — the load-bearing abstraction everything downstream reads."
  - "src.domain.trajectory"
generated: true
---

# Trajectory schemas — the load-bearing abstraction everything downstream reads.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/domain/trajectory.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/domain/trajectory.py |
| `tree` | src |

## Binds

- [[module__src_domain|src.domain]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """Trajectory schemas — the load-bearing abstraction everything downstream reads.

One `AgentTrack` per observed road us
