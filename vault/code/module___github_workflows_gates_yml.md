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
- [[adr__ADR-0012|The verdict boundary is a lint, and the lint fails when it has nothing to check]] **enforced_by** → this — would pass. That is the failure this project has paid for four times (ADR-0012,
- [[adr__ADR-0013|Containment probes, and the control that stops each one reading green]] **enforced_by** → this — ADR-0013), arriving through a new door.
- [[decision__D16|Verdict fields are owned by deterministic nodes]] **enforced_by** → this — D16/D39. LangGraph raises only on *concurrent* unreducered writes, so a
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — machinery (D20): agents may not edit it.
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — D16/D39. LangGraph raises only on *concurrent* unreducered writes, so a
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — Pinned. A gate whose toolchain floats is not a gate — the same argument D40 makes
- [[decision__D44|The evidence store IS the memory; typed views + gated promotion. No extraction pipeline]] **enforced_by** → this — nowhere. That property is what admits them as a read model under D44/D47/D51 rather
- [[decision__D47|Read-only retrieval index, settled by measurement in Phase 2]] **enforced_by** → this — nowhere. That property is what admits them as a read model under D44/D47/D51 rather
- [[decision__D51|Mission control exists, it is split, and every operator action is an evidence row]] **enforced_by** → this — nowhere. That property is what admits them as a read model under D44/D47/D51 rather
