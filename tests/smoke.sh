#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

# ChromaCat is the presentation/pipeline tool and must preserve plain text in
# a non-TTY/no-color path.
plain_input=$'toolset smoke\nsecond line'
plain_output="$(printf '%s\n' "$plain_input" | NO_COLOR=1 ChromaCat/chromacat --no-color)"
assert_eq "$plain_input" "$plain_output" "chromacat no-color pipeline must preserve text"
pass "chromacat non-TTY/no-color pipeline"

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

installer_help="$(HOME="$(mktemp -d)" bash install.sh --help)"
assert_contains "$installer_help" "Install one or more standalone Toolset CLIs" "installer help contract"
pass "installer --help works without network access"

installer_list="$(bash install.sh --list)"
for name in chromacat cleanx dockex gitx netx phpx sqlitex; do
  assert_contains "$installer_list" "$name" "installer lists $name"
done
pass "installer tool catalog"

# Critical destructive-path regression coverage stays in the baseline gate.
bash tests/cleanx.sh
