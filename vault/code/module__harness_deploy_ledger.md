---
kind: module
id: "module:harness.deploy.ledger"
title: "What has been released, append-only. Rollback needs a past to roll back to."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/deploy/ledger.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "What has been released, append-only. Rollback needs a past to roll back to."
  - "harness.deploy.ledger"
generated: true
---

# What has been released, append-only. Rollback needs a past to roll back to.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/deploy/ledger.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/deploy/ledger.py |
| `tree` | harness |

## Binds

- [[module__harness_deploy|harness.deploy]] **contains** → this
- [[module__harness_deploy_driver|Build, deploy, roll back. Through `docker compose`, because that is the claim.]] **imports** → this
- [[module__harness_deploy_test_deploy|S8. Deploy and rollback, verified by observation rather than by exit code.]] **imports** → this

## Enforced by (code)

- [[decision__D27|all in Phase 0]] **enforced_by** → this — """What has been released, append-only. Rollback needs a past to roll back to.

A rollback is only meaningful against a 
- [[decision__D43|Evidence durability and tamper evidence]] **enforced_by** → this — """What has been released, append-only. Rollback needs a past to roll back to.

A rollback is only meaningful against a 
