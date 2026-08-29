# deploy/CONTEXT.md

One job: release machinery — identity-baked image, compose, ledger, rollback — the path `docker compose up` actually serves.

## Inputs

- Working: `deploy/api.Dockerfile`, `deploy/docker-compose.yml`, `harness/deploy/` (ledger, driver, tests)
- Reference: `docs/tier2/branch-release-deploy-protocol.md` (S8), `src/api/` (deployable unit), `docs/tier2/execution-order.md` § S8

## Process

1. Bake release identity into artifact (build arg → env) — never read identity from repo/mount/git at request time; image without identity fails at import.
2. Deploy through `docker compose` — rollback is same code with different target; ledger written only after `/version` is observed serving.
3. Verify transitions by reading `/version` from the running service, not by exit code of the command that caused it.

## Outputs

- Release served via `docker compose up`, ledger-recorded, rollback-verified (`harness/deploy/` tests green).

## Human check

Does `/version` on the running service match the intended release after deploy and after rollback, with ledger entry only after observation?
