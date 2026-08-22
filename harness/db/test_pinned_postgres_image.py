"""Dev compose and the CI grant matrix must run one Postgres, and only a comment said so.

`docs/tier1/data-architecture.md § How the matrix is enforced` requires the grant suite
to run against a migrated throwaway cluster in CI and against the live one at harness
startup, and `docs/tier4/supply-chain-policy.md § Container images` requires both to be
the same image pinned by digest — a grant matrix verified against one Postgres is not
evidence about another. Until this test the only binding between
`docker-compose.yml`'s `postgres.image` and `harness/db.cluster.PINNED_POSTGRES_IMAGE`
was the compose file's own comment ("Must match PINNED_POSTGRES_IMAGE in
harness/db/cluster.py"). A comment is edited in the same commit that breaks it; this
test makes the divergence loud at commit time instead.

Parsed as plain text rather than with a YAML dependency: one indented `image:` key under
one service is not worth a supply-chain edge for the inspector, and a parser here must
not become its own thing to pin.
"""

from __future__ import annotations

from harness.db.cluster import REPO_ROOT, PINNED_POSTGRES_IMAGE

COMPOSE = REPO_ROOT / "docker-compose.yml"


def _postgres_image(compose_text: str) -> str | None:
    """The `image:` value of the `postgres` service, or None if the stanza is absent.

    Two-space keys name services; four-space keys are their settings. A second `image:`
    inside one service block is a parse ambiguity and is refused rather than resolved by
    ordering.
    """
    current_service: str | None = None
    image: str | None = None
    seen_services: set[str] = set()
    for raw_line in compose_text.splitlines():
        line = raw_line.split(" #", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 2 and stripped.endswith(":"):
            current_service = stripped[:-1]
            seen_services.add(current_service)
            continue
        if indent == 4 and current_service == "postgres" and stripped.startswith("image:"):
            value = stripped.removeprefix("image:").strip()
            if image is not None:
                raise AssertionError(
                    "docker-compose.yml declares two image: keys under services.postgres; "
                    "which one pins the database is not decidable from the text"
                )
            image = value
    assert {"postgres", "api"} <= seen_services, (
        f"docker-compose.yml no longer names the expected services (found {sorted(seen_services)}); "
        "the parser's shape assumption is stale"
    )
    return image


def test_dev_compose_runs_the_pinned_image() -> None:
    """The one image, named twice in the repo, asserted once."""
    text = COMPOSE.read_text(encoding="utf-8")
    image = _postgres_image(text)

    # Vacuity guard (D57): a parser that finds nothing agrees with nothing. The equality
    # below would pass against a missing stanza only if it were written `!=`, which it
    # is not — so the absence must fail here, loudly.
    assert image is not None, (
        f"{COMPOSE} carries no image: for services.postgres; dev has lost its database "
        "stanza and this test is checking an empty set"
    )
    assert image == PINNED_POSTGRES_IMAGE, (
        "docker-compose.yml and harness/db/cluster.py pin different Postgres images: "
        f"compose runs {image!r}, cluster.py pins {PINNED_POSTGRES_IMAGE!r}. Dev and the "
        "CI grant matrix are then evidence about two different servers."
    )
