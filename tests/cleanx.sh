#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

TMP_ROOT="$(mktemp -d)"
HOLDER_PID=""
cleanup() {
  if [[ -n "$HOLDER_PID" ]]; then
    kill "$HOLDER_PID" 2>/dev/null || true
    wait "$HOLDER_PID" 2>/dev/null || true
  fi
  rm -rf -- "$TMP_ROOT"
}
trap cleanup EXIT INT TERM

export CLEANX_LIBRARY_MODE=1
# shellcheck source=Clean/cleanx
source Clean/cleanx
unset CLEANX_LIBRARY_MODE

# Declarative config must never execute shell syntax.
marker="$TMP_ROOT/config-executed"
config="$TMP_ROOT/cleanx.conf"
cat >"$config" <<EOF
TMP_DAYS=9
EXCLUDE_GLOB="*.keep"
MALICIOUS=\$(touch "$marker")
EOF

EXCLUDE_GLOBS=()
TMP_DAYS=7
load_config_file "$config" 1
assert_eq "9" "$TMP_DAYS" "declarative config should apply scalar values"
assert_eq "*.keep" "${EXCLUDE_GLOBS[0]}" "declarative config should append exclusion glob"
[[ ! -e "$marker" ]] || fail "config content executed as shell code"
pass "declarative config does not execute shell syntax"

# Invalid target users must fail instead of falling back to the invoking HOME.
if (TARGET_USER="cleanx-user-that-does-not-exist"; resolve_target_user) >/dev/null 2>&1; then
  fail "invalid target user unexpectedly resolved"
fi
pass "target user validation rejects nonexistent accounts"

# Destructive helpers must handle special characters without reparsing shell text.
DRY_RUN=0
SECURE_ERASE=0
LOW_IMPACT=0
EXCLUDE_GLOBS=()
weird_tree="$TMP_ROOT/delete tree [x] ; literal"
mkdir -p -- "$weird_tree/sub dir"
printf 'delete me\n' >"$weird_tree/sub dir/file * literal"
secure_delete_tree "$weird_tree"
[[ ! -e "$weird_tree" ]] || fail "argv-safe tree delete did not remove test tree"
pass "argv-safe deletion handles shell metacharacters literally"

# Exclusions must not be bypassed by recursive rm.
exclude_tree="$TMP_ROOT/exclusion-tree"
mkdir -p -- "$exclude_tree/keep/sub" "$exclude_tree/drop/sub"
printf 'keep\n' >"$exclude_tree/keep/sub/data"
printf 'drop\n' >"$exclude_tree/drop/sub/data"
EXCLUDE_GLOBS=("$exclude_tree/keep")
secure_delete_tree "$exclude_tree"
[[ -f "$exclude_tree/keep/sub/data" ]] || fail "excluded subtree was deleted"
[[ ! -f "$exclude_tree/drop/sub/data" ]] || fail "non-excluded file was not deleted"
pass "recursive deletion preserves excluded subtrees"

# A second process must not be able to acquire the same runtime lock.
runtime_dir="$TMP_ROOT/runtime"
mkdir -p -- "$runtime_dir"
ready="$TMP_ROOT/lock-ready"
XDG_RUNTIME_DIR="$runtime_dir" CLEANX_LIBRARY_MODE=1 bash -c '
  set -Eeuo pipefail
  source Clean/cleanx
  take_lock
  : >"$1"
  sleep 20
' _ "$ready" &
HOLDER_PID=$!

for _ in {1..50}; do
  [[ -e "$ready" ]] && break
  sleep 0.1
done
[[ -e "$ready" ]] || fail "lock holder did not initialize"

set +e
XDG_RUNTIME_DIR="$runtime_dir" CLEANX_LIBRARY_MODE=1 bash -c '
  set -Eeuo pipefail
  source Clean/cleanx
  take_lock
' >/dev/null 2>&1
lock_rc=$?
set -e
((lock_rc != 0)) || fail "second cleanx process acquired an active lock"
pass "runtime lock rejects concurrent cleanx process"
kill "$HOLDER_PID" 2>/dev/null || true
wait "$HOLDER_PID" 2>/dev/null || true
HOLDER_PID=""

# Explicit CLI channel must override config/default values.
channel_output="$(bash Clean/cleanx --channel=phase2-test --print-config)"
assert_contains "$channel_output" "CHANNEL           = phase2-test" "--channel should update effective config"
pass "CLI channel override is honored"

# Unknown options must fail instead of becoming task names.
set +e
bash Clean/cleanx --definitely-unknown >/dev/null 2>&1
unknown_rc=$?
set -e
((unknown_rc != 0)) || fail "unknown option unexpectedly succeeded"
pass "unknown option fails clearly"

# JSON mode must reserve stdout for one parseable JSON document.
json_out="$TMP_ROOT/report.json"
json_log="$TMP_ROOT/report.stderr"
set +e
timeout 30 bash Clean/cleanx --json --dry-run report >"$json_out" 2>"$json_log"
json_rc=$?
set -e
if ((json_rc != 0)); then
  printf 'cleanx JSON report failed with status %d\n' "$json_rc" >&2
  printf '%s\n' '--- stderr ---' >&2
  cat "$json_log" >&2 || true
  printf '%s\n' '--- stdout ---' >&2
  cat "$json_out" >&2 || true
  fail "JSON report command failed"
fi
python3 - "$json_out" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text())
assert data["tool"] == "cleanx"
assert data["mode"] == "dry-run"
assert data["tasks"] == ["report"]
assert isinstance(data["aggressive"], bool)
assert isinstance(data["quota_reached"], bool)
PY
pass "JSON mode emits machine-clean parseable stdout"

printf '\nAll cleanx safety checks passed.\n'
