# The deployable artifact. Its identity is baked in, and that is the point.
#
# ALFRED_RELEASE_ID and ALFRED_RELEASE_DIGEST are build arguments promoted to environment
# variables inside the image. `/version` reads them and nothing else — no repository, no
# mount, no git call. A rollback is verifiable only because the served identity travels
# inside the artifact: read it from outside and the verifier would report the old release
# while the new code kept serving, agreeing with itself in exactly the case it exists to
# catch.
#
# Pinned by digest, never by tag (docs/tier4/supply-chain-policy.md). Tag
# `python:3.12-slim-bookworm`, kept in the comment for readability.
FROM python@sha256:a116514e19457bcb7af7efe9c3dd0b9b71e85b317694e7882a1c52aa15a78134 AS base

ARG ALFRED_RELEASE_ID
ARG ALFRED_RELEASE_DIGEST

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
 && python -m pip install --no-cache-dir .

# Non-root. The API holds no database credential in Phase 0 and should not be able to
# acquire one by writing into its own image.
RUN useradd --create-home --uid 10002 alfred
USER alfred

ENV ALFRED_RELEASE_ID=${ALFRED_RELEASE_ID} \
    ALFRED_RELEASE_DIGEST=${ALFRED_RELEASE_DIGEST} \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C \
    LC_ALL=C

EXPOSE 8000

# Fails at import if the identity is missing, which is what makes an unstamped image
# refuse to serve rather than serve anonymously.
CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
