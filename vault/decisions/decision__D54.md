---
kind: decision
id: "decision:D54"
title: "D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross the boundary as data, its code never crosses at all"
shape: "table-row"
number: "54"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:97"
extractor: "decisions"
aliases:
  - "D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross "
  - "D54"
generated: true
---

# D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross the boundary as data, its code never crosses at all

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:97`

## Statement

**D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross the boundary as data, its code never crosses at all.** The oracle lives in one offline environment, pinned by commit SHA, that never executes agent-authored code; its values reach the `heldout` schema as data and reach `CriterionRunner` at verdict time. **The criterion environment runs the same absence probe as the agent container**, because it is agent-authored code that executes there. The denylist is versioned protected policy configuration whose version is a fingerprint field, splitting the oracle's closure by hand into *denied* (anything computing a measure in the schedulable class) and *permitted substrate* (anything carrying no measure implementation). The probe is four layers: closure check at image build (outside); `find_spec` import probe over every reachable interpreter at boot (inside, before the agent process starts, **never `import`**); path scan for module names, dist-info, `.pth`, archives and caches (inside); and acquisition closure from egress denial plus read-only interpreter paths plus an end-of-run re-assertion. Every failure path is fail-closed, the probe erroring included.

## Fields

**rationale**

> **Asserting absence only in the agent container leaves the delegation path open at verdict time** — which would have made the control look complete while the hole stayed open in the environment that actually decides the verdict. The denylist cannot be "everything the oracle imports" (that bans numpy) nor "its own distribution name" (that misses the packages shipping the same computation for the reachable-set measure), so the classification is a recorded human judgment re-run whenever the closure changes. `find_spec` rather than `import`, because importing a module to learn whether it is importable executes its module-level code inside the sandbox.

## Enforced by (code)

- **enforced_by** → [[module__harness_containment_denylist|Load the oracle denylist and give it a digest the fingerprint can carry.]] — """Load the oracle denylist and give it a digest the fingerprint can carry.

The denylist is versioned protected policy 
- **enforced_by** → [[module__harness_containment_source_hashes|The register C15 clause 3 compares against, and the reason it had nothing to compare.]] — """The register C15 clause 3 compares against, and the reason it had nothing to compare.

Clause 3 catches the vendoring
- **enforced_by** → [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]] — """A silent reclassification changes the fingerprint.

    The reasons are the recorded human judgement D54 asks for. If
- **enforced_by** → [[module__harness_oracle_fingerprints|Runs INSIDE the oracle image. Emits digests and names, and never the source itself.]] — """Runs INSIDE the oracle image. Emits digests and names, and never the source itself.

Two jobs, both of which need the
- **enforced_by** → [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]] — """Carries oracle values across the boundary as data, and refuses when they are not clean.

The oracle's code never cros
- **enforced_by** → [[module__harness_oracle_normalization_vectors_json|harness/oracle/normalization_vectors.json]] — "oracle image, where it must, because D54 forbids the oracle's source crossing the",
- **enforced_by** → [[module__harness_oracle_pins|What the oracle environment is pinned to, and the platform finding that forced it.]] — """What the oracle environment is pinned to, and the platform finding that forced it.

D54: the oracle lives in one offl
- **enforced_by** → [[module__harness_oracle_run|Runs the oracle image. Outside the container, and it never imports the oracle.]] — """Runs the oracle image. Outside the container, and it never imports the oracle.

D54's split is that the oracle's outp
- **enforced_by** → [[module__harness_oracle_run|Runs the oracle image. Outside the container, and it never imports the oracle.]] — """Run the fingerprint emitter and refuse a run whose normalization disagrees with ours.

    Same posture as `run_oracl
- **enforced_by** → [[module__policy_oracle-denylist_json|policy/oracle-denylist.json]] — "D50/D54. Versioned protected policy configuration; the version is a fingerprint field.",
- **enforced_by** → [[module__policy_oracle-source-hashes_json|policy/oracle-source-hashes.json]] — "Only digests cross the boundary. D54 says the oracle's outputs cross as data and its code",
