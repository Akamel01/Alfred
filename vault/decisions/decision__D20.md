---
kind: decision
id: "decision:D20"
title: "Agents may improve the factory, never the inspector"
shape: "table-row"
number: "20"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:64"
extractor: "decisions"
aliases:
  - "Agents may improve the factory, never the inspector"
  - "D20"
generated: true
---

# Agents may improve the factory, never the inspector

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:64`

## Statement

**Agents may improve the factory, never the inspector.** Permanently protected: `CriterionRunner`, `EvidenceStore`, `PolicyEngine`, `AutonomyGate`, protected-path config, sandbox spec, fingerprint tracker.

## Fields

**rationale**

> Every safeguard here assumes the judge is independent of the worker. An agent editing the judge collapses all of them at once, silently, with tests green — because the tests are downstream of the edit. This is ordinary optimization pressure, not malice: "make the criterion runner faster" that quietly loosens a tolerance looks like success at every layer of observation available.

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — machinery (D20): agents may not edit it.
- **enforced_by** → [[module__harness_containment___init__|Containment assertions: what the sandbox must prove before a run starts.]] — """Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion 
- **enforced_by** → [[module__harness_criterion___init__|The criterion plane: materialize from trusted provenance, execute, produce a verdict.]] — """The criterion plane: materialize from trusted provenance, execute, produce a verdict.

Inspector machinery (D20). Run
- **enforced_by** → [[module__harness_evidence___init__|The evidence plane's writer.]] — """The evidence plane's writer.

Inspector machinery (D20). Permanently outside what agents may modify, and outside the
