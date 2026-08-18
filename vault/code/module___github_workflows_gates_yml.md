---
kind: module
id: "module:.github.workflows.gates.yml"
title: ".github/workflows/gates.yml"
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: ".github/workflows/gates.yml:1"
extractor: "code"
tags: [protected]
aliases:
  - ".github.workflows.gates.yml"
  - ".github/workflows/gates.yml"
generated: true
---

# .github/workflows/gates.yml

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | .github/workflows/gates.yml |
| `tree` | .github |

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — digests without running Alfred's code (ADR-0003). It runs on stock Node with
- [[adr__ADR-0004|The ACS-1 float presentation grammar]] **enforced_by** → this — ACS-1 test vectors are the published specification (ADR-0004), so a
- [[decision__D16|Verdict fields are owned by deterministic nodes]] **enforced_by** → this — D16/D39. LangGraph raises only on *concurrent* unreducered writes, so a
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — machinery (D20): agents may not edit it.
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — D16/D39. LangGraph raises only on *concurrent* unreducered writes, so a
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — Pinned. A gate whose toolchain floats is not a gate — the same argument D40 makes
