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

for tool in "${TOOLS[@]}"; do
  [[ -f "$tool" ]] || fail "missing distributable tool: $tool"
  bash -n "$tool"
  pass "bash syntax: $tool"

  mode="$(git ls-files -s -- "$tool" | awk 'NR==1 {print $1}')"
  assert_eq "100755" "$mode" "distributable tool must be executable: $tool"
  pass "git executable mode: $tool"
done

[[ -f install.sh ]] || fail "missing release installer: install.sh"
bash -n install.sh
pass "bash syntax: install.sh"

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck --severity=error -- "${TOOLS[@]}" install.sh
  pass "ShellCheck error-level gate"
else
  fail "shellcheck is required for static validation"
fi
