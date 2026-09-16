#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

DIST_DIR="${DIST_DIR:-dist}"
rm -rf -- "$DIST_DIR"
mkdir -p -- "$DIST_DIR"

TOOLS=(
  "ChromaCat/chromacat:chromacat"
  "Clean/cleanx:cleanx"
  "Docker/dockex:dockex"
  "Git/gitx:gitx"
  "Network/netx:netx"
  "PHP/phpx:phpx"
  "Sqlite/sqlitex:sqlitex"
)

for item in "${TOOLS[@]}"; do
  src="${item%%:*}"
  name="${item#*:}"
  install -m 0755 -- "$src" "$DIST_DIR/$name"
  bash -n "$DIST_DIR/$name"
  [[ -x "$DIST_DIR/$name" ]] || fail "packaged tool is not executable: $name"
  pass "packaged standalone artifact: $name"
done

(
  cd "$DIST_DIR"
  sha256sum chromacat cleanx dockex gitx netx phpx sqlitex > SHA256SUMS
  sha256sum -c SHA256SUMS
)
pass "SHA256SUMS generated and verified"

DIST_DIR="$DIST_DIR" \
SUITE_VERSION="${SUITE_VERSION:-2.0.0-dev}" \
RELEASE_TAG="${RELEASE_TAG:-}" \
SOURCE_COMMIT="${SOURCE_COMMIT:-}" \
  python3 tests/generate-manifest.py >/dev/null

python3 - "$DIST_DIR/manifest.json" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
manifest = json.loads(manifest_path.read_text())

assert manifest["schema_version"] == 1
assert manifest["suite"]["name"] == "Toolset"
assert manifest["suite"]["version"]
assert manifest["suite"]["source_commit"]

names = [entry["name"] for entry in manifest["tools"]]
assert names == ["chromacat", "cleanx", "dockex", "gitx", "netx", "phpx", "sqlitex"]

for entry in manifest["tools"]:
    artifact = manifest_path.parent / entry["asset"]
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert entry["sha256"] == digest
    assert entry["version"]

print("manifest verified")
PY

pass "manifest.json generated and verified"
