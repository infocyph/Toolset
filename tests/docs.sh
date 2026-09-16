#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=tests/lib/assert.sh
source "$ROOT/tests/lib/assert.sh"

cd "$ROOT"

entries=(
  'gitx|Git/gitx|Git/README.md'
  'phpx|PHP/phpx|PHP/README.md'
  'dockex|Docker/dockex|Docker/README.md'
  'netx|Network/netx|Network/README.md'
  'sqlitex|Sqlite/sqlitex|Sqlite/README.md'
  'cleanx|Clean/cleanx|Clean/README.md'
  'chromacat|ChromaCat/chromacat|ChromaCat/README.md'
)

headings=(
  '## Purpose'
  '## Install'
  '## Requirements'
  '## Supported platforms/capabilities'
  '## Quick start'
  '## Command reference'
  '## Destructive/security behavior'
  '## Exit/output contract'
  '## Self-update'
  '## Examples'
)

for entry in "${entries[@]}"; do
  IFS='|' read -r name tool readme <<<"$entry"
  [[ -x "$tool" ]] || fail "$tool is not executable"
  [[ -f "$readme" ]] || fail "$readme is missing"

  for heading in "${headings[@]}"; do
    grep -Fqx -- "$heading" "$readme" || fail "$readme missing heading: $heading"
  done

  grep -Fq -- '--help' "$readme" || fail "$readme must document --help"
  grep -Fq -- '--version' "$readme" || fail "$readme must document --version"

  help="$($tool --help 2>&1)"
  [[ -n "$help" ]] || fail "$name --help returned empty output"
  grep -qi -- "$name" <<<"$help" || fail "$name --help does not identify the tool"

  version="$($tool --version 2>/dev/null)"
  [[ "$version" == "$name "* ]] || fail "$name --version contract is stale"

done
pass "all per-tool README contract headings and live help/version identities match"

for name in gitx phpx dockex netx sqlitex cleanx chromacat; do
  grep -Fq -- "\`$name\`" README.md || fail "root README missing $name"
done
pass "root README lists every standalone CLI"

if grep -RInE --include='README.md' \
  'raw\.githubusercontent\.com/infocyph/Toolset/(main|master)/|github\.com/infocyph/Toolset/(blob|raw)/(main|master)/' \
  README.md Git PHP Docker Network Sqlite Clean ChromaCat; then
  fail "stable documentation still contains a mutable main/master Toolset install URL"
fi
pass "stable README installation paths do not use mutable main/master URLs"

[[ -f docs/cli-contracts.md ]] || fail "docs/cli-contracts.md is missing"
grep -Fq 'Dependency and capability matrix' docs/cli-contracts.md || fail "capability matrix is missing"
grep -Fq 'Destructive and security boundaries' docs/cli-contracts.md || fail "security boundary documentation is missing"
grep -Fq 'Output contract' docs/cli-contracts.md || fail "output contract documentation is missing"
pass "suite capability/security/output contracts are present"
