---
kind: module
id: "module:harness.lane"
title: "harness.lane"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/lane:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.lane"
generated: true
---

# harness.lane

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/lane:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | true |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_lane_lane_fingerprint|Fail-closed fingerprint assertion for the inference lane (D19/D40).]]
- **contains** → [[module__harness_lane_lane_salvage|Recovery of tool calls the serving layer rendered into the content channel.]]
- **contains** → [[module__harness_lane_test_lane_controls|Tests for the two lane controls, with the negative controls that make them tests.]]
