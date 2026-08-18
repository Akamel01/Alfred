---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      Deny-by-default is asserted by a boot-time canary because a major lab's own evaluation harness was found to have left machines with live internet access despite intended isolation. Allowlisted hosts have been used for exfiltration at CVSS 9.6. The executor-specific assertions (C1–C3, C5, C10) rest on OpenHands' own vocabulary and are **unverified first-hand** — the executor is not present in this repository and was not fetched. Each is implemented as a shell whose unread holes yield `not_executed`, never `passed` (ADR-0017); the earlier "written to pass harmlessly" position is withdrawn, because it holds for an absent feature and fails for a misnamed one.
falsifies_if:  A sandbox boots while a known non-allowlisted connection succeeds, or a credential is found reachable from inside the container, or a run reaches a verdict while any assertion in the containment table below was not executed.
review_after:  Phase 2
---

# Sandbox Specification

The execution plane is isolated, disposable and untrusted. Everything here is a
contract the harness asserts at boot, not a configuration anyone is trusted to have set.

## What the container is

An Alfred-owned Docker container holding a repo checkout, the toolchain, and the worker
process. Pinned by commit SHA; the runtime image pinned by digest and mirrored locally.
Disposable — a fresh container per task, a throwaway database built from migrations.

**The executor supplies no security properties.** Whatever harness runs inside it is
treated as an untrusted process inside Alfred's own containment, with every isolation
option set explicitly. A vendor statement that a tool "does not sandbox the agent" or
that its permissions are "not designed to provide security isolation" is taken at face
value: those are observability features, not enforcement.

## Network

**Deny-by-default with an allowlist**, enforced by `nftables` default-drop plus
`REDIRECT`. Environment-variable proxy configuration is advisory and bypassable, and is
never the control.

Everything the agent reads — issue text, dependency READMEs, error messages, web content
— is attacker-reachable and enters its context. Egress control caps the damage even when
injection succeeds.

**Egress canary.** On every sandbox boot, the harness attempts a known non-allowlisted
connection. **The run refuses to start unless that attempt fails.** The canary also
asserts that Postgres is unreachable from inside the container.

Allowlisting is not sufficient by itself — exfiltration through an allowlisted host is a
demonstrated technique — so the allowlist is kept minimal and reviewed as policy, and
registry pulls happen outside the sandbox network namespace so no registry ever appears
in the in-sandbox allowlist.

## Filesystem

Readable paths are fixed by the harness at dispatch and enforced by the mount. They are
never chosen by the agent mid-run: read-side judgment calls are a documented failure
mode, not a hypothetical.

Writable paths exclude the protected set entirely. The output channel is a single mounted
volume where the patch file is written.

## Credentials

**None.** No VCS credential, no database credential, no production credential, no
secret-bearing environment variable. Asserted at startup — a control that fails without
signalling has already happened in this ecosystem, where an SDK silently treated an empty
settings-source list as "unset" and loaded user configuration anyway.

The container emits a patch file. A separate uncontaminated process validates it and
opens the pull request. **The deliverable channel and the exfiltration channel must not
be the same channel** — a real incident ran from pull request opened to token exfiltrated
in eight minutes, ending in four backdoored packages with millions of weekly downloads.

## Persistence and recording

Per-event persistence is asserted enabled at startup and **verified by end-of-run event
count**, not by trusting a flag. Every file read and every search issued is recorded to
the evidence store as the run's observed context.

Recording is what makes nondeterministic retrieval compatible with a fingerprint:
reproducibility comes from the evidence store, not from constraining what the agent may
look at. It is also the forensic trail after an injection incident.

## Compaction

Any built-in compaction or summarization the executor ships is **asserted off**. A
summary upstream of a verdict node means the verdict is computed on someone's
interpretation. This must be checked explicitly, because executors ship such features
enabled and Alfred would otherwise inherit them silently.

## Executor containment

The executor is the third-party agent loop running inside the container. It supplies no
security properties, so every property Alfred depends on is asserted rather than
configured. The assertions below are numbered because the `Worker` port refuses to
dispatch against a handle whose boot report does not carry all of them as `passed`.

**Placement rule, and it decides most of the table.** An assertion whose subject is *what
the container is* runs **inside** it: the import path, the mount set, the environment,
the listening sockets and the loaded configuration are properties of the running
namespace and are invisible from the image manifest — a `PYTHONPATH` set by an
entrypoint, or a mount that shadows a directory, exists nowhere else. An assertion whose
subject is *the container's own account of itself* runs **outside** it: image identity,
the configuration that was sent, the count of durable event records, and the content of
the emitted patch. A container asked to count its own event files is being asked to
attest to its own record.

An inside assertion runs in a separate process, before the agent process starts, and its
result is written by the supervising process outside. It is not a boundary against a
compromised runtime — the Threat Model puts that out of scope — it is a control against
misconfiguration and against ordinary optimization pressure, which is what the two
documented failures in this class actually were.

| # | Assertion | Runs | Catches | On failure |
|---|---|---|---|---|
| C1 | Per-event persistence enabled, **and** the durable event count at end of run is ≥ the count the adaptor observed, with every observed event id present on disk | config outside; count outside, on the mounted volume | persistence silently off (it is opt-in), partial flush, a truncated read log | claim rejected, `indeterminate` |
| C2 | No compaction: every condenser and summarizer disabled in configuration, **and** zero condensation-class events in the end-of-run stream | config outside; stream check outside | a summary upstream of a verdict, inherited from the executor rather than authored by Alfred (I16) | `indeterminate` |
| C3 | No second approval surface: the executor's own frontend is not served, no listening socket exposes it, its confirmation/approval mode is disabled, **and** zero approval-class events appear in the stream | socket scan inside; config outside; stream check outside | an operator approving work inside the execution plane, where the approval lands in the executor's event stream and never in Alfred's evidence chain | run does not start; a stream-side hit rejects the claim |
| C4 | Runtime image digest equals `runtime_image_digest` in the fingerprint; image mirrored locally; pulled outside the sandbox network namespace | outside | tag drift, silent rebuild, a registry appearing in the in-sandbox allowlist | run does not start |
| C5 | Executor pinned by commit SHA resolved **through** the canonical-path redirect, not to it | build time, outside | a redirecting canonical path and a repository with no tags to pin to | build fails |
| C6 | Egress canary fires; Postgres unreachable; no registry host in the allowlist | inside | live network, held-out reachability | run does not start |
| C7 | Oracle absence — see below | inside probe + outside closure check | a run that measures delegation instead of implementation | run does not start |
| C8 | No credential and no secret-bearing environment variable | inside | the deliverable channel becoming the exfiltration channel | run does not start |
| C9 | Mount set enumerated inside the container equals the dispatch spec exactly, mode for mode | inside | agent-chosen read paths (A9), an over-broad harness mount | run does not start |
| C10 | Loaded configuration hash equals the harness-supplied configuration; no user-level or project-level configuration file exists at any path the executor searches | inside | config hoisting — an SDK in this ecosystem silently treated an empty settings-source list as "unset" and loaded user configuration anyway | run does not start |
| C11 | Lane fingerprint asserted: `loaded_context_length`, parallel slot count, model id, quantization | outside, against the serving layer | a lane that reconfigured itself unobserved | run does not start |
| C12 | Writable set is exactly the repo tree and the patch output volume; every interpreter path outside the repo tree is mounted read-only | inside | a mid-run install into site-packages | run does not start |
| C13 | No package archives or resolver caches: no `.whl`, `.tar.gz`, `.zip`, no `pip`/`uv` cache directory, under any mount | inside | an offline install of something egress control already blocks downloading | run does not start |
| C14 | End-of-run re-assertion of C7, C9, C12, C13 | inside, after the agent stops, before the claim is accepted | anything that appeared during the run | claim rejected, `indeterminate` |
| C15 | Patch-side check: the diff adds no dependency, no import of a denied module, and no file whose normalized content hash matches a denied source file | outside, privileged, on the patch | the oracle arriving through the deliverable channel | patch rejected |

C1, C2, C3, C5 and C10 rest on the selected executor's own vocabulary — configuration keys,
event class names, configuration search paths — none of which is in this repository and
none of which has been read first-hand.

> **Amended by ADR-0017.** This paragraph previously argued that each was written to pass
> harmlessly if the feature did not exist, on the grounds that *"an assertion that
> harmlessly passes on a feature that does not exist costs nothing."* **That argument is
> withdrawn.** It holds for an *absent* feature and fails for a *misnamed* one, and C2's two
> conjuncts and C3's three are not independent — each rests on the same vocabulary, so one
> wrong name defeats all of them at once while the assertion reports `passed` with
> compaction running upstream of a verdict (ADR-0007). Fifteen green assertions that mean
> nothing are worse than fifteen absent ones, because the green ones stop anybody looking.

The five are implemented as **shells** in `harness/containment/shells.py`: each names its
claim, the holes its check needs, and the check itself. An unread hole yields
`not_executed`, which F25 makes a failure and which `Worker.check_handle` already refuses to
dispatch on. **A shell never passes.** `open_holes()` is O5's worklist, and its count
reaching zero — by *answering* holes, not deleting them, which CI checks — is what
discharges O5.

The rest of the table needs no executor vocabulary and is written for real: C8, C9, C12 and
C13 in `harness/containment/inside.py`, C14 in `reassert.py`, C15 in `patch_side.py`, C6 and
C7 as before. **C4 and C11 are not written**, and are blocked on something other than O5: both
compare against a run fingerprint record that does not exist in this repository yet.

## Oracle absence

The organizing principle requires ground truth the agent did not author **and cannot
retrieve**. The retrieval half has an implemented enforcement — held-out values behind a
separate database role — and, until this section, an unimplemented one: the oracle
itself. CommonRoad-CriMe is the sole oracle for the Phase 0/1 task class, and no
independent second source exists: the definitional paper ships formulas and no reference
values. If the oracle is importable inside the agent container, a wrapper delegating to
it passes the published constants, every resampled perturbation and every invariance and
degeneracy property, with a clean transcript and no dishonesty anywhere in the loop.
Merge rate would then measure delegation.

### The rule that makes it enforceable: values cross, code never does

The oracle must exist somewhere — it is what produces the reference values. It exists in
exactly one place, and that place never executes agent-authored code:

| Environment | Holds the oracle | Executes agent code | Receives |
|---|---|---|---|
| Oracle environment | yes, pinned by commit SHA, offline | **never** | operator-driven generation runs only |
| `heldout` schema | no — values only | n/a | the oracle's outputs, as data |
| Criterion environment | **no** | yes | held-out values from `heldout` at verdict time |
| Agent container | **no** | yes | nothing from the oracle |

This is the load-bearing sentence: **the oracle's outputs cross the boundary as data; the
oracle's code never crosses it at all.** Asserting absence only in the agent container
would leave the delegation path open at verdict time, since it is agent-authored code
that runs in the criterion environment. Both environments therefore run the same probe.

### The denylist

Policy configuration, versioned, and its version is a fingerprint field. Two sets, and
the distinction between them is a recorded human judgment, not an inference:

- **Denied** — any distribution or module that computes a measure in the schedulable task
  class. `commonroad-crime` and its import name `commonroad_crime`; any package supplying
  an equivalent implementation of a scheduled measure, including the reachable-set and
  drivability packages that supply the drivable-area measure; any future criticality-
  metric package.
- **Permitted substrate** — packages that carry no measure implementation: the numeric
  stack, and the scenario reader if the product uses one for ingest.

Every dependency of the oracle is classified into one of these two sets by hand, with the
reason recorded, and the classification is re-run whenever the image digest or the
resolved closure changes. Banning "everything the oracle imports" would ban numpy;
banning only its own name would miss the packages that ship the same computation.

### The probe

Four layers, each catching something the others cannot.

1. **Closure check, outside, at image build.** The resolved lockfile is compared against
   the denylist by distribution name and by provided top-level module. A denied entry
   fails the build. Catches an oracle arriving as a declared or transitive dependency.
2. **Import probe, inside, at boot, before the agent process starts.** For every
   interpreter reachable inside the container, and for every denied top-level module
   name, `importlib.util.find_spec` is called and must return `None`; every installed
   distribution is enumerated and must not be denied. `find_spec` is used rather than
   `import` deliberately: importing a module to discover whether it is importable
   executes its module-level code inside the sandbox.
3. **Path scan, inside, same boot.** Every directory on the effective import path and
   every mount is walked for a file or directory matching a denied module name, for
   `*.dist-info` / `*.egg-info` naming a denied distribution, for `.pth` files and
   `sitecustomize`, and for the archives and caches C13 covers.
4. **Acquisition closure.** Egress deny-by-default with the canary (C6) means the oracle
   cannot be fetched mid-run; C12 and C13 mean it cannot be installed from anything
   already present. Together these are what let a boot-time assertion hold for the whole
   run rather than only for its first instant — and C14 re-asserts at the end anyway,
   because a control that holds "by argument" is a control that has not been checked.

Every failure path is fail-closed, including the probe erroring, the interpreter set
being unenumerable, and the denylist failing to load. A probe that did not run is not a
probe that passed.

### What the oracle-absence assertion does not cover

Stated plainly, because an assertion oversold is worse than one honestly bounded.

- **Reconstruction from model weights.** If the oracle's source or its published values
  are in the training data, the agent can reproduce them without importing anything. No
  import check touches this. Whether the published values sit in the selected lane's
  training data is unmeasured, and this probe cannot measure it.
- **A renamed, reformatted vendored copy.** The path scan matches names and the patch
  check matches normalized content hashes. A copy with renamed symbols and reflowed
  source passes both. The check is syntactic; it is not semantic.
- **Non-Python paths.** A shared object with an arbitrary name reached through `ctypes`,
  a binary invoked as a subprocess, or a data file carrying the constants, are not
  name-matchable.
- **A non-enumerable interpreter.** The probe covers the interpreters it can find. A
  relocated or embedded interpreter is not discoverable by enumeration.
- **The visible half of the criterion.** Visible criteria contain pinned constants that
  the agent legitimately sees, and a stub memorizing one already passes them. That is why
  at least one grading point per task is held out; the oracle-absence assertion protects
  the held-out half only, and nothing is claimed for the other.
- **What a permitted read path contains.** The mount assertion checks *which* paths are
  exposed, not what is inside them. Any harness subpath the product must import — the
  canonical-serialization encoder is one — is a read surface, mounted at subdirectory
  granularity and justified per path by a human.
- **A compromised runtime or base image.** A meta-path finder that lies to the probe
  defeats it. That is out of scope in the Threat Model, and this assertion inherits the
  exclusion rather than closing it.

**Consequence if the assertion cannot be made to execute:** every merge-rate figure
measured up to that point is void, not suspect. It is not a number with a caveat.

## Negative tests for the two boot controls

A control that has never been observed failing is an unproven control. The egress canary
and the oracle-absence probe are both fail-closed boot gates, so each is admitted only
once it has been *made to fire*.

**The negative tests run against a real difference, never a patched call.** A canary test
that stubs the connect path proves the reporting path and not the enforcement path — and
both documented failures in this class reported fine while enforcing nothing. Where a
real difference cannot be constructed on the runtime, the control is recorded as
**unproven** rather than substituted with a mock and recorded as proven.

**Egress canary.** A variant image identical to the runtime except that the default-drop
rule is absent, plus a listener on a deliberately non-allowlisted address.

| # | Injected | Required |
|---|---|---|
| E-a | The non-allowlisted connection **succeeds** | run does not start (C6) |
| E-b | The canary process itself errors before reaching a verdict | run does not start — the row that fails open in practice |
| E-c | Postgres is reachable from inside the container | run does not start |
| E-p | An **allowlisted** connection succeeds | run starts — without this, E-a passes on a container with no network stack |

**Oracle-absence probe.** Every case below runs **twice — once in the agent container and
once in the criterion environment** — and CI fails if either parameterization produced no
results. An environment that reported nothing is a failure, not an absence; the criterion
environment is the one D54 exists for and the one a suite silently drops.

| # | Injected | Required |
|---|---|---|
| O-a | A stub distribution provides a denied top-level module | run does not start; environment rebuilt; the **retry path refuses** the environment as-is |
| O-b | The probe errors | run does not start |
| O-c | The interpreter set enumerates empty | run does not start — an empty set is never read as clean |
| O-d | The denylist fails to load, or its version differs from the fingerprint | run does not start |
| O-e | A denied module appears **after** boot | claim rejected, `indeterminate`, patch not offered for merge |
| O-f | A `*.dist-info` naming a denied distribution with no importable module | run does not start — isolates the distribution-enumeration layer from `find_spec` |
| O-g | A `.pth` or `sitecustomize` puts a denied module on the path | run does not start — isolates the path-scan layer |
| O-p | A permitted-substrate package remains importable | probe passes — without this, every case above passes on an environment with no interpreter |

**Expected-miss cases, and they are asserted as misses.** Each hole named above gets a
constructed case whose required outcome is that the probe **passes**: a renamed and
reflowed vendored copy; a shared object reached through `ctypes` and a data file carrying
the constants; a relocated interpreter outside the enumerated set; and a meta-path finder
installed from somewhere the path scan does not name. A hole with no test is a hole
nobody remembers, and an expected-miss case that ever starts catching must fail the suite
on the *unexpected pass* — so that the control improving and the documentation of its
limits drifting cannot be the same silent event.

## Host

A dedicated non-admin OS user owns `harness/`, the policy configuration and the Postgres
data directory, unwritable by the operator's interactive account. Firewall rules are
port-granular. Model server auto-update is disabled — an unannounced serving-stack change
invalidates every fingerprint keyed to it.
