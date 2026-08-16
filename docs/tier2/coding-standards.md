---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      Strict typing is enforced now because retrofitting it onto a grown codebase is impractical; the agent inherits Phase 0's conventions, so conventions set before Phase 1 are the ones that propagate.
falsifies_if:  Merged code carries a type suppression without a recorded justification, or the agent's output requires routine style correction in review — meaning the conventions are not reaching it.
review_after:  Phase 2
---

# Coding Standards

The configuration is the standard. This document explains the choices; `pyproject.toml`
enforces them.

## Toolchain

Python throughout. `uv` for dependency resolution and locking, `ruff` for lint and
format, `pyright --strict` for types, `pytest` with `hypothesis` for tests, FastAPI with
Pydantic for the API surface, Alembic for migrations, Postgres, Docker.

One toolchain, chosen so there is one way to do each thing. Pydantic gives executable
contracts rather than documented ones. Hypothesis is the strongest deterministic
adversary available. numpy and scipy are correct for the domain.

## Typing

`pyright --strict` is a **hard gate in the criterion runner**, not advisory. It gives
the agent a cheap deterministic verdict before tests run, which is worth more than it
sounds: a fast failing signal shortens the retry loop that would otherwise consume the
inference lane.

Every module is annotated from its first commit.

Enforce this while the codebase is small. Retrofitting strict mode later is impractical,
and the agent inherits whatever conventions Phase 0 establishes.

### Suppressions

**A justification lives on the suppression line, in the code.** Not in a registry file, not
in a commit message, not here. A registry drifts from the code it describes and the drift
is invisible; a comment cannot be separated from the line it excuses. The required form is
exactly:

```python
expr  # pyright: ignore[reportCallIssue] — <why this is correct, one clause>
```

Three rules, each of which was wrong in this repository before 2026-08-15:

1. **`# pyright: ignore[rule]`, never `# type: ignore[code]`.** Pyright is this project's
   only type checker and it does not honour mypy error codes: `# type: ignore[call-arg]`
   suppresses **every** diagnostic on the line regardless of the code written in the
   brackets. Verified directly — a line carrying `# type: ignore[call-arg]` had an
   unrelated `reportAssignmentType` error silently suppressed, while the same line under
   `# pyright: ignore[reportCallIssue]` still reported it. A bracketed code that the
   checker ignores is documentation that looks like a constraint, which is worse than no
   code at all.
2. **The rule name must be the one the checker emits**, so the suppression narrows to the
   diagnostic it was written for and stops suppressing the next, unrelated one.
3. **The justification is required and is machine-checkable** — an em-dash or hyphen
   followed by at least one word, on the same line.

**Enforcement, stated honestly.** There is today no gate for any of this: the repository
contains no CI configuration, and `[tool.ruff.lint].select` does not include `PGH`, so not
even a codeless `# type: ignore` is flagged. The mechanism, due with the first CI
workflow, is three lines of configuration plus one check:

- `enableTypeIgnoreComments = false` in `[tool.pyright]` — makes blanket `# type: ignore`
  inert, so rule 1 is enforced by the checker rather than by review.
- `reportUnnecessaryTypeIgnoreComment = "error"` — a suppression that no longer suppresses
  anything is removed rather than accumulating.
- `PGH` added to `[tool.ruff.lint].select`.
- A justification check over `# pyright: ignore` lines, in the same gate.

Until those exist, this section is a convention and the `falsifies_if` above is scored
against the recorded suppressions below rather than against a running check.

### Recorded suppressions

Two, both on deliberately-invalid constructor calls inside tests that assert those calls
fail. Verified 2026-08-15 by removing both and re-running the checker: exactly two errors
appear, both `reportCallIssue`, so both suppressions are necessary and neither is masking
anything else.

| Location | Suppresses | Why it is correct |
|---|---|---|
| `tests/test_provenance.py:220` | `reportCallIssue` — *Argument missing for parameter "stamp"* | The test asserts a result cannot be constructed without a stamp. The call is invalid **on purpose**; the checker is right and the runtime rejection is the thing under test. |
| `tests/test_metric_value.py:148` | `reportCallIssue` — *No parameter named "extra_field"* | The test asserts the frozen arms reject extra fields. Same shape: a static error is the precondition for the runtime assertion. |

This table is a **transitional record, not the home**. It exists because the two lines
carry no inline justification today and the register should not claim a control it does not
have. Both are due to be rewritten to the required form — `# pyright: ignore[reportCallIssue]`
plus the clause above — at which point this table is deleted rather than maintained. A
justification recorded in two places is a justification that can disagree with itself.

## Dependencies

Install `langgraph` standalone; do not pull in the wider LangChain surface. Every
dependency is pinned by hash across the full closure — an unconstrained dependency has
already broken a graph library's tool node in the wild.

Adding a dependency requires a technology selection record naming what was rejected.

## Structure

```
src/
  domain/        Pydantic trajectory and scenario schemas — the load-bearing abstraction
  metrics/       metric implementations; formulas pinned to citations
  provenance/    result stamping
  thresholds/    declared, cited, versioned config — never agent-authored
  ingest/        dataset adapters
  replay/        deterministic harness
  api/           FastAPI surface
tests/
  properties/    Hypothesis property tests over composed operations
  reference/     oracle reproduction fixtures
  heldout/       composed and perturbed criteria — never in agent context
migrations/
harness/         OUTSIDE the agent tree — CriterionRunner, egress canary, floor test
scripts/
docs/
```

`harness/` sits outside the agent tree deliberately and is in the protected set. No file
under it is ever agent-writable.

## Conventions

- Modules under 500 lines. Longer means the boundary is wrong.
- Validate input at system boundaries; trust it internally.
- Pure functions for metrics: trajectories in, values out, no I/O, no clock, no
  randomness without a declared seed.
- Every computation pins its seed and its versions. Reproducibility is the product.
- No destructive operations on evidence. Ever.
- Comment density matches the surrounding code. Comments explain why, not what.

## Determinism

Anything on the replay path must produce byte-identical output across runs. That
constrains dictionary iteration where it reaches output, floating-point reduction order,
and any use of wall-clock time or randomness. Where a computation cannot be made
deterministic, it does not belong on the replay path.
