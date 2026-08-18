"""What the oracle environment is pinned to, and the platform finding that forced it.

D54: the oracle lives in one offline environment, pinned by commit SHA, that never
executes agent-authored code. Its values reach `heldout` as data; its code never crosses
at all. This module holds the pins and nothing else, so that a change to what the oracle
*is* shows up as a diff to one file rather than as a rebuilt image nobody compared.

------------------------------------------------------------------ the platform finding

Measured 2026-08-18 against the PyPI JSON API, not read from a classifier. CriMe's three
compiled dependencies publish these wheel platforms and no others:

    commonroad-drivability-checker  manylinux_2_17_x86_64  (cp310-cp313)
    commonroad-reach               manylinux_2_17_x86_64  (cp310-cp311)
    commonroad-clcs                manylinux_2_17_x86_64  (cp310-cp313)

**No arm64 wheel has ever been published for any of them, on any operating system.**
`commonroad-reach` and `commonroad-clcs` have never published a macOS wheel of any kind.
`commonroad-drivability-checker` has published macOS wheels — sixteen of them, every one
`macosx_10_13_x86_64`, last in 2022, Intel only.

This matters because the classifiers say otherwise: `commonroad-drivability-checker`
declares `Operating System :: MacOS` while shipping zero macOS wheels for any release in
four years. A classifier is a claim by the publisher; the wheel list is the fact. The
question "do macOS arm64 wheels exist" was answerable either way from the metadata and
only one of the two answers is true.

Consequence, and it is not a preference: the oracle image is **linux/amd64**, and on the
Apple-silicon host it runs under emulation. There is no arm64 path that does not mean
compiling CGAL, Boost and Eigen from sdist — which would produce an oracle whose binaries
nobody else can reproduce, defeating the pin.

------------------------------------------------------------------- the Python ceiling

`commonroad-reach~=2025.2.0` declares `requires_python <3.12,>=3.10`. So the image is
Python 3.11 — not because 3.11 was chosen, but because 3.12 is excluded and 3.10 is older
for no gain. Recorded here because "why is this image on an old Python" is otherwise a
question answered by guessing.
"""

from __future__ import annotations

from typing import Final

# github.com/CommonRoad/commonroad-crime. Zero tags, one branch: a SHA is the only
# available pin, and it is not a release boundary. The LRZ GitLab mirror is a separate,
# older repository with no tests at all — the reference values do not exist there.
ORACLE_NAME: Final = "commonroad-crime"
ORACLE_COMMIT_SHA: Final = "60bebed8005610f1b856e601852676a21e85cfc6"
ORACLE_REPO: Final = "https://github.com/CommonRoad/commonroad-crime"

# Pinned by digest, never by tag (docs/tier4/supply-chain-policy.md). Tag
# `python:3.11-slim-bookworm` at resolution time, kept for readability only.
BASE_IMAGE: Final = (
    "python@sha256:2e32f7d302adc1c37428355c1e646897c0c53f4fd60b6a551245fb90ee129f91"
)

# See the module docstring. Not a choice.
PLATFORM: Final = "linux/amd64"
PYTHON_VERSION: Final = "3.11"

IMAGE_TAG: Final = f"alfred-oracle:{ORACLE_COMMIT_SHA[:12]}"

# Transcribed from setup.py at ORACLE_COMMIT_SHA. Held here so that a drift between what
# the image installs and what the oracle repository asked for is a diff rather than a
# surprise; `verify_pins` re-reads the source copy inside the image and compares.
DECLARED_REQUIREMENTS: Final = (
    "commonroad-io~=2024.3",
    "commonroad-vehicle-models~=3.0.0",
    "commonroad-route-planner~=2025.1.0",
    "commonroad-drivability-checker~=2025.3.1",
    "commonroad-reach~=2025.2.0",
    "commonroad-clcs~=2025.2.0",
)

# Wheel platforms observed on PyPI, kept as data so the finding above is checkable rather
# than merely asserted. Re-measurable with one HTTP request per name.
WHEEL_PLATFORMS_OBSERVED: Final = {
    "commonroad-drivability-checker": ("manylinux_2_17_x86_64", "macosx_10_13_x86_64"),
    "commonroad-reach": ("manylinux_2_17_x86_64", "musllinux_1_1_x86_64"),
    "commonroad-clcs": ("manylinux_2_17_x86_64", "musllinux_1_1_x86_64"),
}

# The absence claim, stated positively so a future check can falsify it: if any of these
# names ever publishes a wheel whose platform tag contains one of these substrings, the
# linux/amd64 decision is reopened and this constant is what said so.
NO_WHEEL_PLATFORM_SUBSTRINGS: Final = ("aarch64", "arm64")
