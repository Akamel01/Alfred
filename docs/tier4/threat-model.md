---
status:        frozen
owner:         human
enforcement:   review-cadence
evidence:      Every threat listed has a documented instance or a measured attack success rate. None is included on speculation; where a threat is theoretical for Alfred specifically, that is stated.
falsifies_if:  An incident occurs whose mechanism appears nowhere in this model, meaning the model enumerates the wrong hazards.
review_after:  Phase 2
---

# Threat Model

The adversary is not assumed to be a person. Most entries here are reachable by ordinary
optimization pressure with no attacker at all, which is why the controls are structural
rather than detective.

## T1 — Reward hacking

The agent makes checks pass without solving the problem.

*Instances:* a seven-line `conftest.py` forcing 100% resolve across 500 benchmark
instances without touching a test file. An agent writing an auto-approve setting into its
own configuration, disabling its approval gate because the gate lived in a file it could
write.

*Controls:* `CriterionRunner` outside the agent tree, materializing its environment from
trusted provenance. Null-agent floor test. Seeded-defect suite. Protected paths enforced
on the patch, outside the container. Graduation calibrated on held-out pass rate only.

## T2 — Correct-looking, wrong output

No exploit, no attacker. Isolated units pass; composed behaviour is wrong. Measured at a
43–48pp visible/held-out gap.

*Controls:* held-out composed criteria as an acceptance requirement. Property tests over
composed operations as the load-bearing control. Held-out perturbations on resampled
slices whose answers were never published. Published validity envelopes. Result stamping
and the advisory recall path, because a wrong number does not throw, spike latency or
fail a healthcheck.

## T3 — Prompt injection through read content

Issue text, dependency READMEs, error messages and web content are attacker-reachable and
all enter agent context.

*Instances:* instruction files carrying zero-width-encoded directives planted in pull
requests against major agent repositories. Platform tooling flags bidi characters but not
zero-width ones.

*Controls:* network deny-by-default with boot-time egress canary. Read paths fixed by the
harness at dispatch. Read-recording as a **partial** forensic trail — see below.
Deterministic pre-review scan for control, zero-width and bidi characters. CI runs before
any human sees the change, so review is not the first gate.

*The trail is positive evidence only, and the downgrade is deliberate (2026-08-15).* The
read log is derived from the executor's event stream and its completeness is demonstrated
against that stream's own durable event count, so it cannot show that an event was emitted
for everything the agent did; its granularity is the action, not the file read, and files
opened inside a shell command are not enumerated. Content the log records **did** enter
context, which is enough to identify a payload that arrived through a recorded read. The
absence of a read from the log is **not** evidence the read did not happen. What bounds
what could have been read is the asserted mount set (C9, C12), not the log. An independent
filesystem-level channel inside the container was rejected: it needs capabilities that
enlarge the sandbox's privilege set to observe the sandbox. Recorded here rather than
discovered after an incident, which is the only time the difference is expensive.

## T4 — Exfiltration through the deliverable channel

*Instance:* a pull request opened at 05:08 and a token exfiltrated at 05:16, ending in
four backdoored packages with millions of weekly downloads. Separately, exfiltration
through an allowlisted host at CVSS 9.6.

*Controls:* no credential of any kind inside the container. The container emits a patch
file; a separate uncontaminated process validates it and opens the pull request. Agent
branches cannot trigger secret-bearing workflows. Repository-scoped CI caches disabled on
those branches, because caches survive container ephemerality.

## T5 — Tool poisoning

Tool *descriptions* change agent behaviour without any tool name or signature changing.

*Controls:* every tool description hashed into the fingerprint. The harness
schema-validates every tool call in a deterministic node — a schema-capable model still
emits invalid JSON through a bad serving layer.

## T6 — Memory-mediated injection

Any store agents write and later read into context is, by Alfred's own definition, agents
editing agent-influencing configuration. The write channel needs no privileges to be
captured: a query-only actor has achieved 98.2% injection with 76.8% attack success, and
poisoning at under 0.1% of records has reached over 80% attack success. Such injections
survive session boundaries and reach orchestrators.

*Controls:* no LLM-extraction memory layer. Memory is typed SQL views over the append-only
evidence store. Anything promoted into future agent context graduates through the
documentation register — human-reviewed, versioned, expiring — and its version joins the
fingerprint. Retrieval indexes are strictly derived and read-only.

## T7 — Model and serving substitution

*Instance:* identical weights producing opposite tool-calling outcomes on different
servers. Imatrix quantization variants sharing names while differing in content.

*Controls:* fingerprint covering weights, quantization artifact hash, runtime and server
versions, orchestrator commit, harness identity, image digest. Grants suspend on any
change. Server auto-update disabled. Official quants preferred; community repacks load
first in a throwaway VM with the uploader recorded.

## T8 — Supply chain

*Instance:* an unconstrained dependency breaking a graph library's tool node in a patch
release.

*Controls:* full-closure hash pinning, image digests, local mirroring, registry pulls
outside the sandbox network namespace, scans for `.pth` and `sitecustomize` additions.

## T9 — Evidence loss or tampering

Hardware loss and total evidence loss are currently the same event.

*Controls:* off-machine WAL archiving and base backups, an executable restore drill,
hash-chained rows with the chain head anchored off-machine daily, tombstone-based removal
that never mutates the chain.

## T10 — The operator

The failure that actually occurred in the prior attempt was not an attack. It was
advancing through layers before earlier layers were validated, under self-applied
pressure.

*Controls:* executable stage gates; overriding one requires an immutable waiver ADR
recording gate, threshold, actual value, reason and reversal condition; waiver count as a
health metric. The operator's interactive account cannot write `harness/` or the policy
configuration. Capacity ledger as an executable gate, because the binding resource is
human review minutes.

## Out of scope, stated deliberately

Physical access to the machine. A compromised macOS or Docker runtime. A malicious model
publisher whose weights pass hash verification because the published artifact itself is
backdoored. Nation-state adversaries. These are not defended against, and pretending
otherwise would misdescribe what the controls above actually buy.
