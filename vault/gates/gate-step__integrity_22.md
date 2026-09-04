---
kind: gate-step
id: "gate-step:integrity.22"
title: "Protected paths append-only (bench/results/, bench/fingerprints/)"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:209"
extractor: "workflows"
tags: [protected]
aliases:
  - "Protected paths append-only (bench/results/, bench/fingerprints/)"
  - "integrity.22"
generated: true
---

# Protected paths append-only (bench/results/, bench/fingerprints/)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:209`

## Statement

set -euo pipefail
modified=$(git diff --name-only HEAD~1 -- bench/results/ bench/fingerprints/ 2>/dev/null || true)
if [ -n "$modified" ]; then
echo "Protected paths modified (not just added):"
echo "$modified"
echo "Only new files (status 'A') are allowed under bench/results/ and bench/fingerprints/ (ADR-0038)."
exit 1
fi
echo "No modifications to append-only protected paths."

## Fields

| Field | Value |
|---|---|
| `kind` | run |
| `ordinal` | 22 |

**command**

> set -euo pipefail
modified=$(git diff --name-only HEAD~1 -- bench/results/ bench/fingerprints/ 2>/dev/null || true)
if [ -n "$modified" ]; then
echo "Protected paths modified (not just added):"
echo "$modified"
echo "Only new files (status 'A') are allowed under bench/results/ and bench/fingerprints/ (ADR-0038)."
exit 1
fi
echo "No modifications to append-only protected paths."

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
