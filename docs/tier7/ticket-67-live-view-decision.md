---
status:        provisional
owner:         human
enforcement:   none
evidence:      Six requirements given by the operator on 2026-09-03, read against mission-control-specification.md (the boundary split, the read-model no-cache rule, the deliberately-hard-to-reach list, Part B, the deferred table, and authentication and exposure), ADR-0047, and the handoff contract graduated the same day. No Mission Control code exists; nothing here rests on an observed render.
falsifies_if:  Agent-stated intent is found on S2 or cited by a gate; or the live view and Part B become visually indistinguishable; or an operator watches a run overrun with no action available.
review_after:  the first screen that exists
---

# Ticket #67 — the live multi-agent view

Resolves [issue #67](https://github.com/Akamel01/Alfred/issues/67). Six decisions, three ADRs, six tickets filed for what was deferred.

**Two of the six requirements landed unchanged. Three collided with decisions taken hours earlier the same day. One was adjacent to something already specified.** This record says which was which, because a requirement quietly reshaped is a requirement nobody agreed to.

## D1 — "Live" is polling, not streaming

Requirements 2 and 3 ask for live agent status and live inter-agent traffic. `docs/tier7/ticket-52-read-model-decision.md` D1, decided the same morning, forbids the mechanism: **queries at request time, no snapshots, no event stream.**

**The live view re-queries every 2–3 seconds and stamps how current it is.** #52 stands untouched.

The event stream was dropped because §19's duplicate, partial and reordered failures *exist only because there are events*. Polling keeps them impossible rather than handling them.

**The cost, stated:** a 2-second lag, and anything that appears and vanishes between polls is not seen. That is the honest price of not introducing a second source of truth on the surface where being wrong means approving bad work.

## D2 — Agent-stated intent is rendered, and this reverses a rule

Requirement 2 asks for each agent's **goals**. Most of it derives from recorded facts — `phase_start` carries `capability_id`, `phase` and `task_class`; the routing policy maps capability to a pinned model; the task carries its executable criterion.

*Goals* does not derive. The specification forbids it:

> **Any agent self-assessment** of progress, completeness or blockage. It is not recorded, so it cannot be rendered.

The operator was shown the rule and the reasoning and chose to render it anyway. **ADR-0049** is the record.

## D3 — It appears on the live view and nowhere a decision is taken

The ban's argument is specific: on the **approval screen**, agent prose is the thing being judged arguing with its judge. That argument holds completely for S2 and does not reach a monitoring view, where nothing is approved.

So: rendered on the live view, attributed, marked unverified, A10-scanned. **Never on S2.** S4's existing treatment — behind one click, labelled, escaped, scanned — is unchanged.

**This is a boundary rather than a convention.** S2's decision-critical panel is drawn by the command surface; the live view is the read model's; there is no import path between them and CI checks it. S2 cannot render agent prose because the program that draws S2 cannot reach it.

## D4 — No agent-to-agent messaging. Render the handoffs that exist

Requirement 3 names four events. Three are real; one is not a display gap:

| Event | Status |
|---|---|
| handoff to another agent | **Recorded.** `phase_end.artifact_ref` plus the topology's `hands-off-to` edges |
| write to the shared database | **Runtime state.** Display-only, `unknown` when unavailable |
| update shared state | **Runtime state.** Same |
| direct message to another agent | **Does not exist in Alfred** |

`docs/tier3/handoff-contract-standard.md`, graduated the same day, says a handoff carries content-addressed references and **never** agent-authored summaries — so a successor acts on the work rather than on its predecessor's account of it. `phase_end.artifact_ref` is a hash; there is no field a message could travel in.

Adding messaging would be an architectural change that partly undoes that contract, not a rendering decision. **Not taken.**

## D5 — Confirm all five actions; a blocking dialog only where irreversible

Requirement 5 asks for visual confirmation of *"almost all operations."* Two rules bound it. There are exactly five operator actions, each writing one `operator_action` record; and *"nothing on any screen is stored back"*, so no confirmation persists. The design system adds its own: a confirmation dialog belongs only on destructive irreversible actions, because overusing them trains people to click through.

| Action | Treatment |
|---|---|
| Approve merge | **Blocking dialog**, then confirmation naming the record written |
| Reject · Reopen · Take this myself · Open full diff | **No dialog.** Immediate confirmation naming the record written |

Every action confirms. Only the irreversible one interrupts.

## D6 — The live view looks different from Part B, on purpose

Part B renders what happened, per attempt, and its guarantee is that it is *"a pure function of two immutable inputs … never stored."* The live view renders runtime state, which ADR-0047 says owns nothing and is never evidence.

Two graphs where one is trustworthy in a way the other structurally cannot be. **They must not look alike**, or the mutable one is read with the trust the immutable one earned.

| | Part B | Live view |
|---|---|---|
| Edges | solid | dashed for unverified runtime traffic, solid for recorded facts |
| Ground | full weight | lighter |
| Marker | none | persistent `live · unverified` with the poll timestamp |

Missing runtime facts render as **`unknown`**, never **`none`**.

## What was deferred, and where it now lives

Per the operator's standing rule that a deferred step becomes a ticket:

| Deferred | Ticket |
|---|---|
| The authentication layer replacing the loopback bind | [#68](https://github.com/Akamel01/Alfred/issues/68) |
| An interruption path for in-flight runs | [#69](https://github.com/Akamel01/Alfred/issues/69) |
| Measuring a capability so the `trivial` class can stop being empty | [#70](https://github.com/Akamel01/Alfred/issues/70) |
| Rationalization-phrase detection without a hook | [#71](https://github.com/Akamel01/Alfred/issues/71) |
| Check A — assert the reported model against the fingerprint | [#72](https://github.com/Akamel01/Alfred/issues/72) |
| Writing `orchestration/topology.json` | [#73](https://github.com/Akamel01/Alfred/issues/73) |
| Motion design | [#74](https://github.com/Akamel01/Alfred/issues/74) |

## The premature-by-its-own-trigger note

The specification defers this whole feature, and the deferral was reasoned:

> Until interruption is possible, watching is not observability, it is anxiety.

**Neither trigger condition is met.** It is built anyway, by operator decision, recorded as **ADR-0051** — which explicitly does *not* discharge the reasoning. The sentence stays true until [#69](https://github.com/Akamel01/Alfred/issues/69) lands.
