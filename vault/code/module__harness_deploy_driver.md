---
kind: module
id: "module:harness.deploy.driver"
title: "Build, deploy, roll back. Through `docker compose`, because that is the claim."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/deploy/driver.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Build, deploy, roll back. Through `docker compose`, because that is the claim."
  - "harness.deploy.driver"
generated: true
---

# Build, deploy, roll back. Through `docker compose`, because that is the claim.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/deploy/driver.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/deploy/driver.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_deploy_ledger|What has been released, append-only. Rollback needs a past to roll back to.]]
- [[module__harness_deploy|harness.deploy]] **contains** → this
- [[module__harness_deploy_test_deploy|S8. Deploy and rollback, verified by observation rather than by exit code.]] **imports** → this

## Enforced by (code)

- [[decision__D27|all in Phase 0]] **enforced_by** → this — """Content address of what is being released.

    `git rev-parse HEAD` is deliberately not used on its own: a dirty tre
