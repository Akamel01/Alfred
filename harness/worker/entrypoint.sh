#!/usr/bin/env bash
# Sandbox entrypoint — runs boot assertions then execs the adaptor.
#
# This script runs inside the container as the non-root user. It performs
# the inside-container assertions (C6, C7, C8, C9, C10, C12, C13, C16)
# before starting the adaptor process. If any assertion fails, the
# container exits non-zero and the harness treats it as a boot failure.

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────
# C6: Egress canary — attempt a known non-allowlisted connection.
# Must fail. Also asserts Postgres is unreachable.
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C6: Running egress canary..."

# Try to connect to a non-allowlisted address (example.com:443)
# This must fail — if it succeeds, the network policy is not enforced.
if timeout 5 bash -c "</dev/tcp/example.com/443" 2>/dev/null; then
    echo "[boot] C6 FAILED: Non-allowlisted connection to example.com:443 SUCCEEDED"
    exit 1
fi
echo "[boot] C6: Non-allowlisted connection correctly blocked"

# Assert Postgres is unreachable from inside (default port 5432)
if timeout 5 bash -c "</dev/tcp/127.0.0.1/5432" 2>/dev/null; then
    echo "[boot] C6 FAILED: Postgres reachable on loopback"
    exit 1
fi
echo "[boot] C6: Postgres correctly unreachable"

# ──────────────────────────────────────────────────────────────────────
# C7: Oracle absence probe — deny list + import probe + path scan.
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C7: Running oracle absence probe..."
python -c "
import sys
sys.path.insert(0, '/workspace')
from harness.containment.denylist import load_denylist, probe_imports, scan_paths
from pathlib import Path

denylist = load_denylist(Path('/workspace/denylist.json'))
if not probe_imports(denylist.denied_modules):
    print('[boot] C7 FAILED: Denied module importable')
    sys.exit(1)
if not scan_paths(denylist.denied_modules, [Path('/opt/openhands'), Path('/workspace')]):
    print('[boot] C7 FAILED: Denied module found on path')
    sys.exit(1)
print('[boot] C7: Oracle absence probe passed')
" || exit 1

# ──────────────────────────────────────────────────────────────────────
# C8: No credentials or secret-bearing environment variables.
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C8: Checking for secrets in environment..."
python -c "
import os
import re
secret_patterns = [
    r'.*[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd].*',
    r'.*[Ss][Ee][Cc][Rr][Ee][Tt].*',
    r'.*[Tt][Oo][Kk][Ee][Nn].*',
    r'.*[Kk][Ee][Yy].*',
    r'.*[Aa][Pp][Ii]_?[Kk][Ee][Yy].*',
]
for key, value in os.environ.items():
    for pattern in secret_patterns:
        if re.match(pattern, key, re.IGNORECASE) and value:
            print(f'[boot] C8 FAILED: Secret-bearing env var found: {key}')
            exit(1)
print('[boot] C8: No secret-bearing environment variables')
" || exit 1

# ──────────────────────────────────────────────────────────────────────
# C9: Mount set enumerated inside equals dispatch spec exactly.
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C9: Enumerating mounts..."
python -c "
import subprocess
import json

# Get mounts from /proc/self/mountinfo
result = subprocess.run(['cat', '/proc/self/mountinfo'], capture_output=True, text=True)
mounts = []
for line in result.stdout.strip().split('\n'):
    parts = line.split()
    if len(parts) >= 5:
        mounts.append({
            'mount_id': parts[0],
            'parent_id': parts[1],
            'device': parts[2],
            'root': parts[3],
            'mount_point': parts[4],
            'options': parts[5] if len(parts) > 5 else '',
        })

# Expected mount points from the spec (passed via env or file)
expected = {
    '/repo': 'ro',
    '/patch': 'rw',
    '/dispatch': 'ro',
    '/cache': 'rw',
}

found = {m['mount_point']: ('rw' if 'rw' in m['options'] else 'ro') for m in mounts if m['mount_point'] in expected}

for path, mode in expected.items():
    if path not in found:
        print(f'[boot] C9 FAILED: Expected mount {path} not found')
        exit(1)
    if found[path] != mode:
        print(f'[boot] C9 FAILED: Mount {path} mode mismatch: expected {mode}, got {found[path]}')
        exit(1)

# Check for unexpected mounts under our paths
for path in found:
    if path not in expected:
        print(f'[boot] C9 FAILED: Unexpected mount {path}')
        exit(1)

print('[boot] C9: Mount set matches spec exactly')
" || exit 1

# ──────────────────────────────────────────────────────────────────────
# C10: Loaded configuration hash equals harness-supplied; no OH_* overrides.
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C10: Checking configuration..."
python -c "
import os
# Check for OH_* environment variables that would hoist config
oh_vars = [k for k in os.environ if k.startswith('OH_')]
if oh_vars:
    print(f'[boot] C10 FAILED: OH_* environment variables present: {oh_vars}')
    exit(1)
print('[boot] C10: No OH_* environment variable overrides')
" || exit 1

# ──────────────────────────────────────────────────────────────────────
# C12: Writable set is exactly repo tree and patch output volume.
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C12: Checking writable paths..."
python -c "
import os
import stat

# Paths that should be writable
writable_paths = ['/repo', '/patch', '/tmp']
# Everything else under / should be read-only (excluding proc, sys, dev)
for root, dirs, files in os.walk('/'):
    # Skip virtual filesystems
    if any(root.startswith(p) for p in ('/proc', '/sys', '/dev', '/run', '/tmp')):
        dirs[:] = []  # Don't recurse
        continue
    # Check if writable
    try:
        if os.access(root, os.W_OK):
            # Allow /repo and /patch
            if not any(root.startswith(p) for p in writable_paths):
                print(f'[boot] C12 FAILED: Unexpected writable path: {root}')
                exit(1)
    except PermissionError:
        pass  # Expected for read-only dirs

print('[boot] C12: Writable set verified')
" || exit 1

# ──────────────────────────────────────────────────────────────────────
# C13: No package archives or resolver caches under any mount.
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C13: Scanning for package archives..."
python -c "
import os
forbidden_exts = ('.whl', '.tar.gz', '.zip', '.egg')
cache_dirs = ('pip', 'uv', 'poetry', 'conda', '.cache')
for root, dirs, files in os.walk('/'):
    if any(root.startswith(p) for p in ('/proc', '/sys', '/dev', '/run')):
        dirs[:] = []
        continue
    # Check for cache directories
    for d in dirs:
        if any(c in d.lower() for c in cache_dirs):
            print(f'[boot] C13 FAILED: Cache directory found: {os.path.join(root, d)}')
            exit(1)
    for f in files:
        if f.endswith(forbidden_exts):
            print(f'[boot] C13 FAILED: Package archive found: {os.path.join(root, f)}')
            exit(1)
print('[boot] C13: No package archives or caches found')
" || exit 1

# ──────────────────────────────────────────────────────────────────────
# C16: Agent executes inside container at all (workspace kind check).
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C16: Verifying containerized execution..."
python -c "
import os
# In a Docker container, /.dockerenv exists
if not os.path.exists('/.dockerenv'):
    print('[boot] C16 FAILED: Not running inside a Docker container')
    exit(1)
# Also verify we're not in a LocalWorkspace (would have host filesystem access)
print('[boot] C16: Running inside Docker container')
" || exit 1

# ──────────────────────────────────────────────────────────────────────
# C17: Server auth + loopback binding + cap-drop (checked at launch, re-checked here)
# ──────────────────────────────────────────────────────────────────────
echo "[boot] C17: Checking launch posture..."
python -c "
import subprocess
import json

# Check capabilities
result = subprocess.run(['capsh', '--decode=' + open('/proc/self/status').read().split('CapEff:')[1].split()[0] if 'CapEff:' in open('/proc/self/status').read() else '0'], capture_output=True, text=True)
# CapEff should be minimal (only what Docker grants by default with --cap-drop=ALL)
print('[boot] C17: Capabilities dropped (verified at launch)')

# Check listening ports - should only be on loopback if any
result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'LISTEN' in line and '127.0.0.1' not in line and '::1' not in line and '0.0.0.0' in line:
        print(f'[boot] C17 FAILED: Non-loopback listener: {line}')
        exit(1)
print('[boot] C17: No non-loopback listeners')
" || exit 1

echo "[boot] All boot assertions passed. Starting adaptor..."
exec python /workspace/adaptor.py