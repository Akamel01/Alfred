---
kind: module
id: "module:harness.containment.patch_side"
title: "C15 — the oracle arriving through the deliverable channel."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/patch_side.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "C15 — the oracle arriving through the deliverable channel."
  - "harness.containment.patch_side"
generated: true
---

# C15 — the oracle arriving through the deliverable channel.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/patch_side.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/patch_side.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **imports** → [[module__harness_containment_denylist|Load the oracle denylist and give it a digest the fingerprint can carry.]]
- **imports** → [[module__harness_containment_source_hashes|The register C15 clause 3 compares against, and the reason it had nothing to compare.]]
- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — # Clause 3 not running is not an unverified *premise* in ADR-0007's sense, but it is
