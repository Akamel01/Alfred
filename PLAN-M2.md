# PLAN-M2 — the containment controls that exist and do not run

**Module** M2 · **ADR assigned** 0030 · **Base** `main` @ `fa62b4b` · **Branch**
`m2/containment-controls` · **Written** 2026-08-19

Four items. Two are mine outright (1, 4). Two carry OBSERVER decisions (2, 3): I investigate,
report the options with their costs, and do not pick.

## Baseline, measured before anything changed

```
uv run pytest tests bench harness     1112 collected, 1109 passed, 0 skipped, 3 failed
uv run ruff check                     All checks passed!
uv run pyright                        0 errors, 0 warnings, 0 informations
scripts/lint_*.py (all nine)          all OK, exit 0
```

The three failures are `harness/deploy/test_deploy.py`, environmental — `ALFRED_PG_PASSWORD`
is not in this shell. Exactly the expected baseline. **If that count moves at all I stop and
report.** `uv sync --frozen --all-extras --dev` was needed first: without `psycopg`, six
suites fail at collection, which is a louder failure than a skip and was not a change to the
tree.

## Commit units

One commit per item, plus this plan, plus the ADR. A session limit can end me at any point and
an uncommitted control is worth nothing to the observer.

---

## Item 1 — C17 joins C14's re-assertion set (mine)

**What changes.** `REASSERTED` in `harness/containment/reassert.py` gains `"C17"`. The module
docstring gains the argument for why, in the shape C16's paragraph already has: C17's subject
is the `docker run` argv and the published port bindings, both of which a **relaunch** can
change while every boot-time assertion stays true of a container that no longer exists.
ADR-0023 named this as deliberately not done and said the argv is recorded in `observed`
*precisely so that it could be compared*. `_check_c17` already records the full argv and the
binding list, un-summarized, for this reason.

Ordering: appended after `C16`. `compare` sorts by the set's own order, so appending is the
only edit that does not renumber existing output.

**The negative control.** A run that **passes C17 at boot and fails at re-assertion** — a
container relaunched with a published `0.0.0.0` binding and `--cap-drop` gone. The drift-kind
assertion is the control, not the outcome: the test requires `compare` to name
`DriftKind.VALUE` on `container_launch_args` *and* on `published_port_bindings`, because an
outcome-level pass/fail pair would also be produced by a check that stopped reading the argv
altogether. A second control covers the relaunch that keeps the same posture but a different
argv — both ends `PASSED`, drift still reported — since that is the case an outcome
comparison cannot express at all and the one C14's value-diff exists for.

**What would show it vacuous.** `value_blind` returning `"C17"`: an adaptor that re-runs C17
without observations would be compared on outcome alone. `value_blind`'s existing test over the
real checks is extended to cover C17, so a member added to `REASSERTED` that records nothing is
caught by the control that already exists for exactly that.

**What I do not do.** I do not make C17 mandatory anywhere it was not, beyond membership in the
closed set; `reassert` already treats a missing member as `NOT_EXECUTED`, so this makes the
end-of-run report's obligations larger by exactly one assertion, which is the intended change
and is stated in the ADR.

---

## Item 2 — C11's `parallel_slots` conjunct (OBSERVER)

**Investigate, do not decide.** ADR-0020 states the field is a launch-time property of the
server and absent from `/api/v0/models`, so it arrives as an explicit argument and its absence
is `not_executed`. The question the handoff asks is narrower: is the slot count knowable from
anything the harness already observes — a launch record, a deploy manifest, a process argv —
at the place C11 is called?

I search for the lane's launch surface, report what exists with `path:line`, and write down the
two options and their costs:

- a production reading, if one exists;
- a permanent `UNREAD` hole in the `shells.py` discipline, if it does not.

Recording a permanent `UNREAD` hole and deleting the conjunct are different claims about the
sandbox. I write neither into the tree.

---

## Item 3 — C15 clause 3 has no production caller (OBSERVER)

**Investigate, do not wire.** `assert_patch` is called by no production code at all; the
register ADR-0024 built works whenever something calls it. The caller's *site* is the decision:
C15's stated property is that it runs on the diff and never on a working tree, and wiring it
into the wrong place forfeits that.

`harness/patch/` is owned by another agent and uncommitted; I do not touch it. I report the
candidate sites, what each would cost C15's runs-on-the-diff property, and my recommendation.

**Finding 8 stays open.** Added lines hashed against whole-file digests; only a whole-new-file
diff can match. A post-application check is a second, different check and closing it here would
cost the property above. Not closed, and the existing test that pins the limit is left alone.

---

## Item 4 — nothing checks that an adaptor key is one the holes name (mine)

**What changes.** `shells.py` gains the key-set half of ADR-0026's contract. ADR-0026 typed the
*values* and recorded the gap in as many words: an unknown key is legal and ignored, which is
correct, *but a typo'd key reads as absent rather than as a mistake — it fails closed with the
wrong reason.*

The check is deliberately not "reject unknown keys": the executor's configuration surface is
larger than the set Alfred reads, and rejecting unknown keys would be a different and false
claim. It is **confusability**: a key that is not one the holes name, but whose case- and
separator-normalized form collides with one that is. `containerId` against `container_id`;
`sessionApiKeys` against `session_api_keys`. Those cannot both be real keys of one executor,
and the collision is exact rather than a guess at intent.

Placement follows ADR-0026's own argument: refused at construction in
`ExecutorObservation.__post_init__`, beside `validated_config`, because an adaptor sending a
key nobody can read should be told so where it sent it rather than three checks later.

**The negative controls.**
1. `sessionApiKeys` in place of `session_api_keys` is refused at construction, naming both
   spellings. Paired with the demonstration of the defect: the same observation built past the
   guard makes C17 report the key *absent* — failing closed for the wrong reason, the exact
   sentence ADR-0026 left open.
2. A genuinely unknown key (`some_key_alfred_does_not_read`) is **accepted**. Without this the
   check would be rejecting unknown keys, and every test above would still pass.
3. The named-key set is non-empty and derived from the register rather than typed out — D57.
   A check whose reference set is empty finds nothing and reports clean.

**What would show it vacuous.** An empty named-key set, covered by control 3; and a
normalization so aggressive that everything collides, covered by control 2.

**The limit, written down rather than papered over.** A genuine misspelling —
`sesion_api_keys` — normalizes to itself and is not caught. This catches spelling-convention
drift (camelCase, hyphens, casing), which is the class the handoff names and the class an
adaptor written against JSON documentation actually produces. Edit-distance matching would
catch more and would produce false positives in the one check whose findings are meant to be
acted on. Stated in the docstring, pinned by a test, in the shape of `patch_side.py`'s "The
limit" section.

---

## ADR-0030

One record covering all four: what changed, what was investigated and deliberately not
changed, and the two OBSERVER decisions with their options. Written last, over the work rather
than ahead of it.

## Standing rules I am operating under

D20 (all of this is inspector machinery), Major-fix #8 (every commit here becomes an O9 review
item, and I say so in the report), D57, F25, ADR-0007's vacuity class. No `Co-Authored-By`
trailer. No push, no merge, no PR. `harness/patch/` and `harness/selftest/` untouched.
