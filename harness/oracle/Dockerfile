# The oracle environment. One job: run CommonRoad-CriMe at a pinned commit and emit
# numbers. It never executes agent-authored code, and nothing in this image is reachable
# from the agent container or the criterion environment (D50, D54).
#
# Platform is linux/amd64 and that is forced, not chosen — see harness/oracle/pins.py.
# The three compiled dependencies have never published an arm64 wheel.
#
# Pinned by digest, never by tag: docs/tier4/supply-chain-policy.md.
FROM --platform=linux/amd64 python@sha256:2e32f7d302adc1c37428355c1e646897c0c53f4fd60b6a551245fb90ee129f91

# `git clone` + `checkout <sha>` rather than a source tarball, and the reason is a
# supply-chain one rather than convenience. A GitHub-generated tarball's bytes are not
# guaranteed stable across time — the compression has changed before — so a checksum
# pinned against one is a pin that can spuriously break. A commit SHA is git's own
# content address over the tree: it cannot drift, and `git rev-parse HEAD` inside the
# image re-derives it, which is what verify_pins checks.
ARG ORACLE_COMMIT_SHA=60bebed8005610f1b856e601852676a21e85cfc6
ARG ORACLE_REPO=https://github.com/CommonRoad/commonroad-crime

# git for the SHA pin; a C/C++ toolchain because the closure is not wheels-only.
# Measured, not anticipated: `polygon3`, reached transitively, publishes an sdist and no
# wheel for any platform, so the build fails on a compiler-less image with
# `error: [Errno 2] No such file or directory: 'gcc'`. Worth recording rather than
# quietly fixing — it means the oracle image cannot be reduced to a wheels-only install,
# and a future attempt to slim it will rediscover this the same way.
#
# The X libraries are for `cv2`, reached through `commonroad_reach`, which fails at import
# with `libxcb.so.1: cannot open shared object file`. Installing the system libraries
# rather than substituting `opencv-python-headless`: swapping a package the oracle
# declared would make this image compute something the pinned oracle does not, which is
# the one thing an oracle image may not do.
RUN apt-get update \
 && apt-get install --no-install-recommends -y \
      git ca-certificates build-essential \
      libgl1 libglib2.0-0 libxcb1 libsm6 libxext6 libxrender1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /oracle

# Full clone, then detach at the SHA. A shallow clone of a single commit would work and
# is refused deliberately: `git log` inside the image is how a reader confirms the SHA is
# where the recorded commit date says it is.
RUN git clone "${ORACLE_REPO}" src \
 && git -C src checkout --detach "${ORACLE_COMMIT_SHA}" \
 && test "$(git -C src rev-parse HEAD)" = "${ORACLE_COMMIT_SHA}"

# The oracle's own declared dependency set, resolved by pip. Not a lockfile: CriMe
# declares compatible-release pins (`~=`) and pinning tighter here would mean the image
# installs something the oracle repository did not ask for. The resolved set is captured
# after the fact by `pip freeze` into /oracle/resolved.txt, which is the artifact a
# rebuild is compared against.
RUN python -m pip install --no-cache-dir --upgrade pip \
 && python -m pip install --no-cache-dir ./src \
 && python -m pip freeze > /oracle/resolved.txt

# The extractor. COPY, never a mount: code mounted at run time is code the run could have
# been given anything for, and this image's whole claim is that it executes nothing the
# harness did not build into it.
COPY extract.py /oracle/extract.py
COPY points.py /oracle/points.py

# The fingerprint emitter and the vectors that cross-check its normalization. Same COPY
# discipline and the same reason. It is not the entrypoint: the driver overrides it, so the
# default path of this image stays the extractor and nothing gains a second way to run.
COPY fingerprints.py /oracle/fingerprints.py
COPY normalization_vectors.json /oracle/normalization_vectors.json

# The output directory is the only writable path the run needs. Created here and owned by
# the unprivileged user so the container never runs as root.
# The clone is chowned to the unprivileged user because git refuses a repository whose
# owner differs from the caller ("dubious ownership") and `git rev-parse HEAD` at run time
# is how the image is asked what commit it actually holds. The alternative — baking the
# SHA into a file at build time — would have the image report the SHA it was told rather
# than the one it has, which is the difference the check exists to catch.
RUN useradd --create-home --uid 10001 oracle \
 && mkdir -p /out \
 && chown -R oracle:oracle /out /oracle
USER oracle

# Deterministic collation and no bytecode, for the same reason the compose file sets it:
# a value that differs by locale is a reproducibility failure with nothing to do with the
# metric. MPLBACKEND because several CriMe measures import matplotlib at module scope and
# would otherwise try to open a display that does not exist.
ENV LANG=C \
    LC_ALL=C \
    PYTHONHASHSEED=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    ORACLE_COMMIT_SHA=${ORACLE_COMMIT_SHA}

# `commonroad_reach` compiles a Cython module at IMPORT time via pyximport, writing to
# ~/.pyxbld. Discovered by the run failing with
# `PermissionError: [Errno 13] Permission denied: '/home/oracle/.pyxbld'` under a
# read-only root.
#
# The fix is to compile here rather than to give the run a writable home. An oracle that
# builds part of itself on every invocation is one whose output depends on a compiler
# available at run time — and the run has no network, no writable root and, ideally, no
# work to do beyond arithmetic. Warming the cache into the image makes the run hermetic
# and moves the compile into the layer that is pinned.
# Warmed through the same import chain the extractor uses, not by naming the generated
# module directly: pyximport registers it lazily, so `import
# commonroad_reach.utility.util_py_grid_online_reach` fails with ModuleNotFoundError
# before the package has installed its meta-path hook.
RUN python -c "import commonroad_crime.measure" \
 && test -d /home/oracle/.pyxbld

ENTRYPOINT ["python", "/oracle/extract.py"]
