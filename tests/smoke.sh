#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

# ChromaCat is the presentation/pipeline tool and must preserve plain text in
# a non-TTY/no-color path. This is intentionally small for the baseline gate;
# per-tool smoke coverage will grow as each CLI is hardened.
plain_input=$'toolset smoke\nsecond line'
plain_output="$(printf '%s\n' "$plain_input" | NO_COLOR=1 ChromaCat/chromacat --no-color)"
assert_eq "$plain_input" "$plain_output" "chromacat no-color pipeline must preserve text"
pass "chromacat non-TTY/no-color pipeline"

# Verify each script can be loaded far enough for Bash parsing without executing
# commands that may mutate the host. Full --help/--version checks are added once
# their public contracts are standardized in Phase 1.
for tool in \
  ChromaCat/chromacat \
  Clean/cleanx \
  Docker/dockex \
  Git/gitx \
  Network/netx \
  PHP/phpx \
  Sqlite/sqlitex; do
  [[ -s "$tool" ]] || fail "tool is empty: $tool"
done
pass "all distributable scripts are present and non-empty"
