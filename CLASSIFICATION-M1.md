# M1 classification — what the two uncovered gates would actually report

**Base** `main` @ `fa62b4b` · **Measured** 2026-08-19 · venv from
`uv sync --frozen --all-extras --dev`

This is Step 2 of `PLAN-M1.md`, widened to cover `ruff` as well as `pyright`, because the
corrected ruff measurement turned the "cheap gate" into a second scope question of the same
shape as OBSERVER-1.

---

## Step 0 baseline — the numbers everything else is compared against

| Measurement | Result |
|---|---|
| `uv run pytest tests bench harness` | **1109 passed, 0 skipped, 3 failed** (21.7s) |
| the 3 failures | `harness/deploy/test_deploy.py`, all three needing `ALFRED_PG_PASSWORD` — environmental, matches `_COMMON.md` |
| `uv run ruff check` (product gate as configured) | **All checks passed** — 0 violations |
| `uv run pyright` (product gate as configured) | **0 errors, 0 warnings** |
| `uv run ruff check harness` (as configured) | `warning: No Python files found under the given path(s)` — exit **0** |
| `uv run ruff check harness` with `include` widened | **866 violations** |
| the same, with `S101` ignored under `harness/**` | **236 violations** |
| `uv run pyright harness` | **311 errors** |
| `.py` files under `harness/` | **74** |

The "237" in the handoff and the "No Python files found" in the salvaged plan are **both
correct and are not the same measurement**. As configured, `[tool.ruff].include` reaches no
file under `harness/`, so ruff collects nothing and exits 0 — this is exactly the ADR-0007
vacuity shape, and it is how the gap stayed invisible. The 236/237 number only appears once
the include is widened *and* `S101` (assert) is ignored the way `tests/*` already ignores it.
Without that one ignore the number is 866. **630 of the 866 are `S101`.**

---

## Step 1 — the gap proven empirically, with the `src/` control arm

Planted at module top level in `harness/acs/acs1.py`:

```python
import os  # a ruff-visible violation
def broken(x: int) -> str: return x   # a pyright-visible defect
```

| Arm | `uv run ruff check` | `uv run pyright` |
|---|---|---|
| plant in `harness/acs/acs1.py` | **All checks passed**, exit 0 | **0 errors** |
| plant in `src/domain/ids.py` (control) | **2 errors** (E402, F811), exit 1 | **2 errors**, incl. `reportReturnType: "int" is not assignable to return type "str"` at the planted line |

The control arm is the load-bearing half. Without it, "the gates passed it" is consistent with
the gates being **inert**. With it, the gates are demonstrably **live** and `harness/` is
demonstrably **scoped out**. Both plants were reverted; `git status` is clean.

---

## Step 2a — the 311 pyright errors, by kind

| Rule | Count | Bucket |
|---|---|---|
| `reportUnknownArgumentType` | 88 | 1 volume |
| `reportUnknownVariableType` | 62 | 1 volume |
| `reportUnknownMemberType` | 38 | 1 volume |
| `reportArgumentType` | 35 | mixed — see below |
| `reportOptionalMemberAccess` | 22 | 1 volume (narrowing), 4 latent |
| `reportUnknownParameterType` | 22 | 1 volume |
| `reportMissingTypeArgument` | 13 | 1 volume |
| `reportMissingParameterType` | 8 | 1 volume |
| `reportUnknownLambdaType` | 5 | 1 volume |
| `reportPrivateUsage` | 4 | 2 config (tests reaching a module's `_helper`) |
| `reportUnnecessaryIsInstance` | 4 | 3 latent — dead guards |
| `reportUnusedImport` | 2 | 1 volume |
| `reportUnnecessaryComparison` | 1 | 3 latent — dead guard |
| `reportUnusedFunction` | 1 | 3 latent — a register helper nothing calls |
| `reportMissingImports` | 1 | 2 config — `commonroad_crime`, a domain package |
| `reportDeprecated` | 1 | 1 volume |
| `reportPossiblyUnboundVariable` | 1 | 1 volume |
| `reportCallIssue` | 1 | **rule-conflict — see the negative-control finding** |
| `reportUnnecessaryTypeIgnoreComment` | 1 | 1 volume |
| `reportGeneralTypeIssues` | 1 | 3 latent — `Final` redeclared in a subclass |

By directory: `lane` 151, `containment` 37, `fingerprint` 29, `acs` 27, `oracle` 26,
`criterion` 15, `evidence` 11, `selftest` 8, `deploy` 3, `db` 2, `patch` 2.

### Bucket 3 — the real ones. There are about seven.

| Site | What it is |
|---|---|
| `harness/acs/mutate.py:541` | `__doc__.splitlines()` where `__doc__` is `str \| None`. Under `python -OO` this is an `AttributeError` at import of the mutation driver. A one-line fix; a real latent crash. |
| `harness/containment/patch_side.py:306` | `clause_three_ran = bool(x)` then `if clause_three_ran and x is not None` on a parameter pyright types non-optional. The `is not None` arm can never be false: a guard that cannot fire. **M2's file — reported, not touched.** |
| `harness/containment/shells.py:363` | `isinstance(v, str)` where `v` is already `str`. Dead guard. **M2's file.** |
| `harness/lane/lane_fingerprint.py:169,200` and `lane/lane_salvage.py:107` | `isinstance(x, Mapping)` where `x` is already `Mapping`. Dead guards — three assertions that assert nothing. |
| `harness/selftest/test_replay.py:119` | `arity` redeclared in a subclass where the parent declares it `Final`. **M3's file.** |
| `harness/containment/test_c_assertions.py:1346` | `_source_hash_register` is never accessed — a register helper that no test calls. **M2's file.** |

Everything else in bucket 3's neighbourhood dissolves on reading. `evidence/test_store.py:127`
(`last` possibly unbound) is bound by a `range(1, 6)` loop that always runs.
`lane_salvage.py:403` accesses `.name` on an optional that the preceding
`if r.salvaged` filter guarantees — an invariant pyright cannot see. Those are bucket 1.

### The finding that changes the shape of OBSERVER-1

`harness/fingerprint/test_record.py:64` is `reportCallIssue: No parameter named
"fingerprint_sha256"` — inside this test:

```python
def test_the_hash_is_not_stored_and_cannot_be_supplied() -> None:
    with pytest.raises(TypeError):
        RunFingerprint(**_BASE, fingerprint_sha256="deadbeef")  # type: ignore[arg-type]
```

The call is **deliberately wrong**; the test asserts it raises. Pyright is right and the code
is right. The line already carries a mypy-shaped `# type: ignore[arg-type]` that pyright does
not honour for this rule. The 24 `reportArgumentType` errors at
`harness/fingerprint/test_record.py:50` are the same shape — a `**overrides: object` helper
that exists precisely so wrong-typed values can be fed in.

**A bulk pass over the 311 would delete the repository's own negative controls.** A tool
flagging a deliberately-invalid call, and an agent "fixing" it by making the call valid, is
how a seeded-defect suite quietly stops seeding defects. This is the single strongest argument
against option C below, and it is stronger than the volume argument.

### Negative control on the classification itself

Plan Step 2 requires that the classification recognise the one error known to be real. Planted
`def broken(x: int) -> str: return x` into `harness/acs/acs1.py`, re-ran `pyright harness`:
**311 → 312**, and the added error is the *only* `reportReturnType` in the entire tree. The
rule class the planted defect belongs to has exactly one member and it is the plant. Stated
the other way round: **`harness/` today contains zero return-type and zero assignment-type
errors.** The 311 are annotation debt, narrowing artefacts, and seven dead guards — not
silent type lies.

---

## Step 2b — the 236 ruff violations, by kind

Measured with `include=["harness/**/*.py"]` and `per-file-ignores={"harness/**"=["S101"]}`.
44 are auto-fixable safely; 27 more only with `--unsafe-fixes`.

| Group | Rules | Count | What it is |
|---|---|---|---|
| **Auto-fixable, safe** | `I001` 28, `UP012` 4, `UP035` 4, `F401` 2, `RUF022` 2, `RUF100` 2, `SIM300` 2 | **44** | `ruff --fix` clears these. Zero judgement. |
| **Hand edits, non-semantic** | `E501` 67, `ANN401` 24, `ANN001` 8, `ANN202` 5, `ANN204` 1, `ARG001` 10, `ARG005` 4, `ARG002` 1 | **120** | Line wrapping and annotations. Mechanical, but 120 separate edits across ~50 files in the protected tree. |
| **Rule/tree conflicts — the honest answer is a scoped ignore, not a fix** | `T201` 19 (harness scripts print by design), `S603` 15 + `S607` 12 (a harness that shells out to `docker`/`git` is the point), `S608` 4 (test SQL against a throwaway cluster), `S311` 2, `S108` 2, `S104` 1 | **55** | Fixing these would change harness behaviour. Suppressing them is defensible but it is a scope decision, not a cleanup. |
| **Judgement, one at a time** | `RUF001` 4 (fullwidth `Ｚ` in ACS-1 vectors — *intentional*, they are Unicode test vectors), `RUF002` 2, `RUF005` 2, `B905` 1, `BLE001` 1, `TRY004` 1, `RUF036` 1, `RUF043` 1, `RUF015` 1, `ERA001` 1, `S310` 1, `S105` 1 | **17** | Each needs a read. Several must **not** be fixed. |

Three worth naming from the judgement group:

- `harness/lane/test_lane_controls.py:166` `BLE001` — the blind `except Exception` is *inside*
  a test named `test_mutant_without_fail_closed_reading_would_swallow_the_error`, i.e. it is a
  deliberately-modelled failure mode. Fixing it deletes the control.
- `harness/acs/gen_vectors.py` `RUF001` ×4 — fullwidth `Ｚ` in ACS-1 test vectors. The
  ambiguity is the test. `gen_vectors.py` is also byte-identity-checked in CI
  (`gates.yml:119`), so an "ambiguous character" fix would fail that gate.
- `harness/containment/shells.py:342` `RUF036` — `None` mid-union, with a comment directly
  above explaining why `None` is meaningful there.
- `harness/patch/validate.py:138` `S105` — inside `harness/patch/`, which no module may touch.

### The finding: the cheap gate is not cheap

The handoff offered `ruff check harness` as the cheap increment with pyright deferred. On the
real numbers it is not cheap, and it is the same *kind* of decision as OBSERVER-1:

- 866 raw, or 236 after the single ignore `tests/*` already gets.
- Of the 236: 44 free, **120 hand edits**, 55 that should be suppressed rather than fixed, 17
  that need individual judgement and several of which must not be fixed at all.
- 45 of them are in `harness/containment/` (**M2**), 8 in `harness/selftest/` (**M3**), 2 in
  `harness/patch/` (**forbidden to every module**). I cannot make ruff green over `harness/`
  without writing into two other live modules' territory and one tree nobody may touch.

That last line is decisive on its own. Per `PLAN-M1.md` Step 3 — *"if any fix would change
harness behaviour, it does not land here"* — and per the observer's instruction that Step 3
stops rather than landing a gate propped up by per-file-ignores, **the ruff include does not
land in this module.** It becomes part of the OBSERVER-1 answer.
