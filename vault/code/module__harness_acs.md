---
kind: module
id: "module:harness.acs"
title: "harness.acs"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/acs:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.acs"
generated: true
---

# harness.acs

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/acs:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | true |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]]
- **contains** → [[module__harness_acs_acs1_mjs|ACS-1 — independent JavaScript implementation (ADR-0003, ADR-0004).]]
- **contains** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]]
- **contains** → [[module__harness_acs_mutate|Mutation control for the ACS-1 conformance suite.]]
- **contains** → [[module__harness_acs_test_acs1|Conformance tests for ACS-1 against the published vector suite.]]
- **contains** → [[module__harness_acs_verify_js_mjs|Verify the JavaScript implementation against the published ACS-1 vector suite.]]
- [[gate-step__inspector_04|ACS-1 — Python conformance]] **runs** → this
