#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

TOOLS=(
  "chromacat:ChromaCat/chromacat"
  "cleanx:Clean/cleanx"
  "dockex:Docker/dockex"
  "gitx:Git/gitx"
  "netx:Network/netx"
  "phpx:PHP/phpx"
  "sqlitex:Sqlite/sqlitex"
)

REPORT_DIR="${REPORT_DIR:-reports/contracts}"
rm -rf -- "$REPORT_DIR"
mkdir -p -- "$REPORT_DIR"

TMP_HOME="$(mktemp -d)"
trap 'rm -rf -- "$TMP_HOME"' EXIT

failures=0

run_flag() {
  local name="$1" path="$2" flag="$3" suffix
  suffix="${flag#--}"

  local stdout_file="$REPORT_DIR/${name}-${suffix}.stdout"
  local stderr_file="$REPORT_DIR/${name}-${suffix}.stderr"
  local status_file="$REPORT_DIR/${name}-${suffix}.status"

  local rc=0
  set +e
  timeout 10 env \
    HOME="$TMP_HOME" \
    NO_COLOR=1 \
    PHPX_NO_LOG=1 \
    NETX_COLOR=never \
    TERM=dumb \
    bash "$path" "$flag" >"$stdout_file" 2>"$stderr_file"
  rc=$?
  set -e

  printf '%s\n' "$rc" >"$status_file"

  if (( rc != 0 )); then
    printf 'FAIL: %s %s exited %d\n' "$name" "$flag" "$rc" >&2
    failures=$((failures + 1))
    return
  fi

  if LC_ALL=C grep -q $'\033' "$stdout_file" "$stderr_file"; then
    printf 'FAIL: %s %s emitted ANSI with NO_COLOR/non-TTY contract\n' "$name" "$flag" >&2
    failures=$((failures + 1))
    return
  fi

  if [[ ! -s "$stdout_file" && ! -s "$stderr_file" ]]; then
    printf 'FAIL: %s %s produced no output\n' "$name" "$flag" >&2
    failures=$((failures + 1))
    return
  fi

  pass "$name $flag"
}

for item in "${TOOLS[@]}"; do
  name="${item%%:*}"
  path="${item#*:}"

  run_flag "$name" "$path" --help
  run_flag "$name" "$path" --version
done

if (( failures > 0 )); then
  printf '\n%d standalone CLI contract check(s) failed. See %s/.\n' "$failures" "$REPORT_DIR" >&2
  exit 1
fi

printf '\nAll standalone CLI help/version contracts passed.\n'
