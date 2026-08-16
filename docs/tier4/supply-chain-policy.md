---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      An unconstrained dependency has broken a graph library's tool node in a patch release. Identical model weights have produced opposite tool-calling outcomes on different serving stacks. Imatrix quantization variants share names while differing in content.
falsifies_if:  A dependency, image or model artifact resolves to content other than its pinned hash, or a behaviour change is traced to a component whose identity was believed pinned.
review_after:  Phase 2
---

# Supply Chain Policy

Everything that can change behaviour is pinned by content hash, and its identity is part
of the fingerprint that autonomy grants are keyed to.

## Python dependencies

Resolved and locked by `uv`, pinned by hash across the **full closure** — not just direct
dependencies. The resolved lockfile hash is a fingerprint field.

Rationale is concrete rather than precautionary: an unconstrained dependency in a
prebuilt graph package broke `ToolNode.afunc` in a patch release. A transitive change is
indistinguishable from a capability regression unless the closure is pinned.

Adding a dependency requires a technology selection record naming what was rejected.

**The resolved closure is also checked against the oracle denylist**, by distribution
name and by provided top-level module, and a denied entry fails the image build. The
oracle is the ground truth an agent must not be able to retrieve; a transitive dependency
is the way it arrives without anyone deciding to add it. The denylist version is a
fingerprint field, because a run measured under a weaker denylist is not comparable to
one measured under a stronger one.

## Container images

The runtime image is pinned **by digest**, never by tag, and mirrored locally. The digest
is a fingerprint field.

Images are pulled **outside the sandbox network namespace**, so no registry host ever
appears in the in-sandbox allowlist. The pull happens before the sandbox exists.

## Model artifacts

Prefer the author's official quantization, or quantize locally from hash-verified
originals. A community repack loads first inside a throwaway VM under the standard egress
posture, with the uploader recorded.

**The quantization artifact hash is what matters, not the quant name.** Imatrix variants
share names while differing in content, so a name is not an identity. Where full weight
hashing is deferred, the recorded substitute is the config and weight-index hashes plus
the shard-size manifest, and the deferral is stated.

The serving stack is pinned too — inference runtime identity and version, server version.
Identical weights have produced opposite tool-calling outcomes across servers, and one
server has been observed emitting truncated tool-call JSON with the issue closed and
unowned. Auto-update on the model server is disabled.

## Orchestrator and harness

Pinned by commit SHA or binary hash. Canonical repository paths that redirect are
resolved and pinned to the destination, not to the redirect.

**An orchestrator change is a criterion-set epoch boundary.** Prior autonomy grants
invalidate, and historical wall-clock-per-merged-task becomes incomparable across the
boundary. This is stated because the alternative — quietly comparing across a harness
change — produces numbers that look like progress and are not.

Harness identity alone has been measured moving the same model by several percentage
points, the same order as the spread between leading benchmark submissions.

## Diff-level scanning

Before any human sees a change, CI rejects diffs introducing non-ASCII control,
zero-width or bidi characters outside declared string literals, with particular force on
agent-instruction files. It also rejects additions of `.pth` files, `sitecustomize`, and
new instruction files.

This is not theoretical: instruction files carrying zero-width-encoded directives have
been planted in pull requests against major agent repositories, and platform tooling flags
bidi characters but not zero-width ones.

## Outbound licensing

The shipped container carries its own obligations. Every bundled component's licence is
inventoried, attribution notices ship with the image, and the inventory is CI-linted
against the dependency closure. Inbound data licensing is covered separately in Data
Classification and Handling.
