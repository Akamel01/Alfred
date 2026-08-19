---
kind: module
id: "module:harness.deploy"
title: "harness.deploy"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/deploy:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.deploy"
generated: true
---

# harness.deploy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/deploy:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_deploy___init__|harness/deploy/__init__.py]]
- **contains** → [[module__harness_deploy_driver|Build, deploy, roll back. Through `docker compose`, because that is the claim.]]
- **contains** → [[module__harness_deploy_ledger|What has been released, append-only. Rollback needs a past to roll back to.]]
- **contains** → [[module__harness_deploy_test_deploy|S8. Deploy and rollback, verified by observation rather than by exit code.]]
- [[gate-step__inspector_11|Deploy and rollback (ledger, identity, refusals)]] **runs** → this
