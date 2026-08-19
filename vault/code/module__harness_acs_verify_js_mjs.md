---
kind: module
id: "module:harness.acs.verify_js.mjs"
title: "Verify the JavaScript implementation against the published ACS-1 vector suite."
shape: "javascript"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/acs/verify_js.mjs:1"
extractor: "code"
tags: [protected]
aliases:
  - "Verify the JavaScript implementation against the published ACS-1 vector suite."
  - "harness.acs.verify_js.mjs"
generated: true
---

# Verify the JavaScript implementation against the published ACS-1 vector suite.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/acs/verify_js.mjs:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/acs/verify_js.mjs |
| `tree` | harness |

## Binds

- [[module__harness_acs|harness.acs]] **contains** → this
- [[gate-step__inspector_05|ACS-1 — JavaScript conformance]] **runs** → this
