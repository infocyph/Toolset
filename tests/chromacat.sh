#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TOOL="$ROOT/ChromaCat/chromacat"
# shellcheck source=tests/lib/assert.sh
source "$ROOT/tests/lib/assert.sh"

tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT INT TERM

assert_file_eq() {
  local expected="$1" actual="$2" message="$3"
  cmp -s -- "$expected" "$actual" || fail "$message"
}

assert_no_sgr() {
  local file="$1" message="$2"
  if LC_ALL=C grep -q $'\033\[[0-9;]*m' "$file"; then
    fail "$message"
  fi
}

# Default non-TTY behavior is byte-for-byte cat semantics, including UTF-8,
# existing ANSI and trailing/newline edge cases.
printf 'alpha\nβeta\n\033[31mred\033[0m\n\n' >"$tmp/stdin.expected"
env -u TERM "$TOOL" <"$tmp/stdin.expected" >"$tmp/stdin.actual"
assert_file_eq "$tmp/stdin.expected" "$tmp/stdin.actual" "default stdin must be byte-faithful"
pass "default stdin is byte-faithful"

printf 'no-final-newline' >"$tmp/no-newline.expected"
env -u TERM "$TOOL" <"$tmp/no-newline.expected" >"$tmp/no-newline.actual"
assert_file_eq "$tmp/no-newline.expected" "$tmp/no-newline.actual" "default stdin must preserve missing final newline"
pass "missing final newline is preserved"

printf 'one\n' >"$tmp/one file.txt"
printf 'two\n\n' >"$tmp/two.txt"
cat -- "$tmp/one file.txt" "$tmp/two.txt" >"$tmp/files.expected"
env -u TERM "$TOOL" "$tmp/one file.txt" "$tmp/two.txt" >"$tmp/files.actual"
assert_file_eq "$tmp/files.expected" "$tmp/files.actual" "multiple files must retain cat ordering/content"
pass "multiple-file passthrough is faithful"

: >"$tmp/empty"
env -u TERM "$TOOL" "$tmp/empty" >"$tmp/empty.actual"
assert_file_eq "$tmp/empty" "$tmp/empty.actual" "empty input must remain empty"
pass "empty input remains empty"

# Explicit raw passthrough is available even when the input name begins with '-'.
printf 'dash-file\n' >"$tmp/-payload"
"$TOOL" --cat -- "$tmp/-payload" >"$tmp/cat.actual"
assert_file_eq "$tmp/-payload" "$tmp/cat.actual" "--cat must provide explicit raw passthrough"
pass "explicit --cat passthrough works"

set +e
unknown_err="$($TOOL --definitely-not-an-option 2>&1 >/dev/null)"
unknown_rc=$?
set -e
[[ $unknown_rc -ne 0 ]] || fail "unknown option must fail"
assert_contains "$unknown_err" "Unknown option" "unknown option diagnostic"
pass "unknown options fail clearly"

# --no-color and NO_COLOR remove SGR color/blink/invert sequences, including
# sequences already present in input.
printf '\033[31mred\033[0m plain\n' | "$TOOL" --no-color >"$tmp/no-color.out"
assert_no_sgr "$tmp/no-color.out" "--no-color must not emit SGR escapes"
assert_contains "$(cat "$tmp/no-color.out")" "red plain" "--no-color content"
pass "--no-color is ANSI-clean"

printf '\033[5;7;32mgreen\033[0m\n' | NO_COLOR=1 "$TOOL" >"$tmp/no-color-env.out"
assert_no_sgr "$tmp/no-color-env.out" "NO_COLOR must not emit SGR escapes"
assert_contains "$(cat "$tmp/no-color-env.out")" "green" "NO_COLOR content"
pass "NO_COLOR is ANSI-clean"

# Forced formatting still emits styling when explicitly requested.
printf 'forced\n' | TERM=xterm-256color "$TOOL" --force >"$tmp/forced.out"
LC_ALL=C grep -q $'\033\[' "$tmp/forced.out" || fail "--force should enable formatting on a pipe"
pass "--force explicitly enables pipe colouring"

# TERM/tput absence must not break plain execution.
printf 'term-safe\n' >"$tmp/term.expected"
PATH="/usr/bin:/bin" env -u TERM "$TOOL" <"$tmp/term.expected" >"$tmp/term.actual"
assert_file_eq "$tmp/term.expected" "$tmp/term.actual" "missing TERM must not break plain output"
pass "missing TERM is harmless for plain output"

# Validation closes arithmetic/regex edge cases before they reach rendering.
for args in '--spread 0' '--speed 0' '--seed x[0]' '--style nope' '--orientation sideways' '--image-opacity 101'; do
  read -r -a argv <<<"$args"
  set +e
  printf 'x\n' | "$TOOL" "${argv[@]}" --force >/dev/null 2>"$tmp/validation.err"
  rc=$?
  set -e
  [[ $rc -ne 0 ]] || fail "invalid arguments unexpectedly succeeded: $args"
done
pass "numeric/style/orientation validation rejects invalid input"

set +e
printf 'x\n' | "$TOOL" --theme not-a-theme --force >/dev/null 2>"$tmp/theme.err"
theme_rc=$?
set -e
[[ $theme_rc -ne 0 ]] || fail "unknown theme must fail"
pass "unknown themes fail clearly"

set +e
printf 'x\n' | "$TOOL" --only-match --no-color >/dev/null 2>"$tmp/match.err"
match_rc=$?
set -e
[[ $match_rc -ne 0 ]] || fail "--only-match without --match must fail"
pass "--only-match requires a regex"

# No-color matching remains functional without injecting presentation escapes.
printf 'INFO one\nERROR two\n' | "$TOOL" --no-color --match 'ERROR' --only-match >"$tmp/match.out"
assert_no_sgr "$tmp/match.out" "plain matching must remain ANSI-clean"
assert_eq $'\nERROR' "$(cat "$tmp/match.out")" "plain only-match output"
pass "plain match filtering works"

# Unicode content must survive box rendering; width is best-effort based on the
# host locale and is documented rather than byte-count-corrupting the payload.
printf '界🙂 café\n' | LC_ALL=C.UTF-8 "$TOOL" --no-color --box --center >"$tmp/unicode-box.out"
assert_contains "$(cat "$tmp/unicode-box.out")" "界🙂 café" "unicode box payload"
assert_no_sgr "$tmp/unicode-box.out" "unicode no-color box must remain ANSI-clean"
pass "Unicode box content is preserved"

# Streaming must flush before EOF and remain bounded for a representative log.
fifo="$tmp/input.fifo"
mkfifo "$fifo"
"$TOOL" --stream --no-color <"$fifo" >"$tmp/stream.out" &
stream_pid=$!
exec 3>"$fifo"
printf 'first\n' >&3
for _ in {1..20}; do
  grep -q '^first$' "$tmp/stream.out" 2>/dev/null && break
  sleep 0.05
done
grep -q '^first$' "$tmp/stream.out" || fail "stream mode buffered until EOF"
printf 'second\n' >&3
exec 3>&-
wait "$stream_pid"
assert_eq $'first\nsecond' "$(cat "$tmp/stream.out")" "stream output"
pass "stream mode flushes incrementally"

seq 1 20000 | sed 's/^/log line /' >"$tmp/large.log"
timeout 10 "$TOOL" --stream --no-color "$tmp/large.log" >"$tmp/large.out"
assert_eq "20000" "$(wc -l <"$tmp/large.out" | tr -d ' ')" "large stream line count"
pass "large stream remains bounded and completes"
