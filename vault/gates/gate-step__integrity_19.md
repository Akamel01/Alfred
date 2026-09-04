---
kind: gate-step
id: "gate-step:integrity.19"
title: "ACS-1 vectors regenerate byte-identically"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:167"
extractor: "workflows"
tags: [protected]
aliases:
  - "ACS-1 vectors regenerate byte-identically"
  - "integrity.19"
generated: true
---

# ACS-1 vectors regenerate byte-identically

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:167`

## Statement

set -euo pipefail
before="$(shasum -a 256 harness/acs/vectors.json | cut -d' ' -f1)"
python3 harness/acs/gen_vectors.py > /dev/null
after="$(shasum -a 256 harness/acs/vectors.json | cut -d' ' -f1)"
if [ "$before" != "$after" ]; then
echo "vectors.json is not what gen_vectors.py produces."
echo "  committed:   $before"
echo "  regenerated: $after"
echo "Either the generator changed without regenerating, or the file was hand-edited."
git --no-pager diff --stat -- harness/acs/vectors.json || true
exit 1
fi
echo "byte-identical: $after"

## Fields

| Field | Value |
|---|---|
| `kind` | run |
| `ordinal` | 19 |

**command**

> set -euo pipefail
before="$(shasum -a 256 harness/acs/vectors.json | cut -d' ' -f1)"
python3 harness/acs/gen_vectors.py > /dev/null
after="$(shasum -a 256 harness/acs/vectors.json | cut -d' ' -f1)"
if [ "$before" != "$after" ]; then
echo "vectors.json is not what gen_vectors.py produces."
echo "  committed:   $before"
echo "  regenerated: $after"
echo "Either the generator changed without regenerating, or the file was hand-edited."
git --no-pager diff --stat -- harness/acs/vectors.json || true
exit 1
fi
echo "byte-identical: $after"

## Binds

- **runs** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]]
- **runs** → [[module__harness_acs_vectors_json|harness/acs/vectors.json]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
