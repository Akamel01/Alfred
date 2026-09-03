# Criterion — <name>

> Visible | Held-out — copy from `_templates/criterion.md`, never edit in place.

## Interface signature

```python
def metric(trajectory: Trajectory) -> MetricValue: ...
```

## Assertion

- Input: `tests/reference/<fixture>` or `tests/properties/` generated
- Expected:
- Tolerance:

## Provenance

- Formula citation:
- Oracle value (if held-out, sealed separately):

## Verdict binding

- Runner: `harness/selftest/` or `CriterionRunner` via `migrations/`
- Evidence: hash-chained row in `migrations/harness/` — never in this file.
