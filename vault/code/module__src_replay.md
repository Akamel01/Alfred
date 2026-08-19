---
kind: module
id: "module:src.replay"
title: "src.replay"
shape: "package"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/replay:1"
extractor: "code"
aliases:
  - "src.replay"
generated: true
---

# src.replay

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/replay:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | src |

## Binds

- **contains** → [[module__src_replay___init__|The deterministic replay harness. The port is here; the implementation is domain work.]]
- **contains** → [[module__src_replay_harness|The replay harness: load, evaluate, stamp, and produce a digest two runs are compared on.]]
- **contains** → [[module__src_replay_port|The `ReplayHarness` port — determinism stated as a hash, not as an intention.]]
