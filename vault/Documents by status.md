---
kind: index
title: "Documents by status and enforcement"
generated: true
---

# Documents by status and enforcement

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

The register's 63 documents. `enforcement` names a gate; whether that gate exists is answerable from the gate notes, which is the point of holding both in one graph.

## Status × enforcement

```dataview
TABLE status, owner, enforcement, written, review_after
FROM "vault/documents"
WHERE kind = "document"
SORT enforcement ASC, status ASC, title ASC
```

## Stubs still waiting on evidence

```dataview
TABLE tier, review_after
FROM "vault/documents"
WHERE kind = "document" AND written = "stub"
SORT tier ASC
```

## Claiming a CI gate

```dataview
TABLE tier, owner
FROM "vault/documents"
WHERE kind = "document" AND enforcement = "ci-gate"
SORT tier ASC
```
