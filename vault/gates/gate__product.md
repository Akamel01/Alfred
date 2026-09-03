---
kind: gate
id: "gate:product"
title: "product (lint, types, tests)"
shape: "job"
job: "product"
source: ".github/workflows/gates.yml:234"
extractor: "workflows"
tags: [protected]
aliases:
  - "product"
  - "product (lint, types, tests)"
generated: true
---

# product (lint, types, tests)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:234`

## Fields

| Field | Value |
|---|---|
| `ordinal` | 2 |

## Binds

- **contains** → [[gate-step__product_01|Install uv]]
- **contains** → [[gate-step__product_02|Set up Python]]
- **contains** → [[gate-step__product_03|Sync dependencies from the lockfile]]
- **contains** → [[gate-step__product_04|ruff]]
- **contains** → [[gate-step__product_05|pyright --strict]]
- **contains** → [[gate-step__product_06|pytest — product]]
- **needs** → [[gate__integrity|integrity (fixtures and register)]]
