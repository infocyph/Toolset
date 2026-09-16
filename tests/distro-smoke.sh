#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

TOOLS=(
  ChromaCat/chromacat
  Clean/cleanx
  Docker/dockex
  Git/gitx
  Network/netx
  PHP/phpx
  Sqlite/sqlitex
)

# shellcheck disable=SC1091
. /etc/os-release 2>/dev/null || true
printf 'Distro: %s\n' "${ID:-unknown} ${VERSION_ID:-unknown}"
printf 'Bash: %s\n' "${BASH_VERSION}"

for tool in "${TOOLS[@]}"; do
  bash -n "$tool"
  pass "syntax on distro: $tool"
done

input=$'portable pipeline\nsecond line'
output="$(printf '%s\n' "$input" | NO_COLOR=1 TERM=dumb bash ChromaCat/chromacat --no-color)"
assert_eq "$input" "$output" "chromacat plain pipeline must be distro-portable"
pass "chromacat plain pipeline"

# phpx generic capabilities are distro-portable, while mutation support is explicit.
export PHPX_LIBRARY_MODE=1 PHPX_NO_LOG=1
# shellcheck source=PHP/phpx
source PHP/phpx
unset PHPX_LIBRARY_MODE
case "${ID:-unknown}" in
  debian|ubuntu) expected_phpx_backend=apt ;;
  fedora) expected_phpx_backend=dnf ;;
  alpine) expected_phpx_backend=none ;;
  *) expected_phpx_backend="$(detect_package_manager)" ;;
esac
assert_eq "$expected_phpx_backend" "$(detect_package_manager)" "phpx package capability backend"
pass "phpx package capability on ${ID:-unknown}: $expected_phpx_backend"
