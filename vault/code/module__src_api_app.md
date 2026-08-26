---
kind: module
id: "module:src.api.app"
title: "Health and identity. The identity is the load-bearing half."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/api/app.py:1"
extractor: "code"
aliases:
  - "Health and identity. The identity is the load-bearing half."
  - "src.api.app"
generated: true
---

# Health and identity. The identity is the load-bearing half.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/api/app.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/api/app.py |
| `tree` | src |

## Binds

- [[module__src_api|src.api]] **contains** → this
- [[module__harness_deploy_test_deploy|S8. Deploy and rollback, verified by observation rather than by exit code.]] **imports** → this
- [[module__src_api___init__|The deployable unit. Deliberately almost empty.]] **imports** → this
- [[module__tests_api_test_routes|API route tests using TestClient with build_identity injection.]] **imports** → this
