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
