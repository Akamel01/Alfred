---
kind: module
id: "module:harness.deploy.test_deploy"
title: "S8. Deploy and rollback, verified by observation rather than by exit code."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/deploy/test_deploy.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "S8. Deploy and rollback, verified by observation rather than by exit code."
  - "harness.deploy.test_deploy"
generated: true
---

# S8. Deploy and rollback, verified by observation rather than by exit code.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/deploy/test_deploy.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/deploy/test_deploy.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_deploy_driver|Build, deploy, roll back. Through `docker compose`, because that is the claim.]]
- **imports** → [[module__harness_deploy_ledger|What has been released, append-only. Rollback needs a past to roll back to.]]
- **imports** → [[module__src_api_app|Health and identity. The identity is the load-bearing half.]]
- [[module__harness_deploy|harness.deploy]] **contains** → this
