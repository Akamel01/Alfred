---
kind: module
id: "module:harness.lane.lane_fingerprint"
title: "Fail-closed fingerprint assertion for the inference lane (D19/D40)."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/lane/lane_fingerprint.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Fail-closed fingerprint assertion for the inference lane (D19/D40)."
  - "harness.lane.lane_fingerprint"
generated: true
---

# Fail-closed fingerprint assertion for the inference lane (D19/D40).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/lane/lane_fingerprint.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/lane/lane_fingerprint.py |
| `tree` | harness |

## Binds

- [[module__harness_lane|harness.lane]] **contains** → this

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """Fail-closed fingerprint assertion for the inference lane (D19/D40).

The serving stack auto-unloads an idle model and
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — """Fail-closed fingerprint assertion for the inference lane (D19/D40).

The serving stack auto-unloads an idle model and
