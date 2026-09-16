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

printf 'Distro: %s\n' "$(. /etc/os-release 2>/dev/null && printf '%s %s' "${ID:-unknown}" "${VERSION_ID:-unknown}" || printf unknown)"
printf 'Bash: %s\n' "${BASH_VERSION}"

for tool in "${TOOLS[@]}"; do
  bash -n "$tool"
  pass "syntax on distro: $tool"
done

input=$'portable pipeline\nsecond line'
output="$(printf '%s\n' "$input" | NO_COLOR=1 TERM=dumb bash ChromaCat/chromacat --no-color)"
assert_eq "$input" "$output" "chromacat plain pipeline must be distro-portable"
pass "chromacat plain pipeline"
