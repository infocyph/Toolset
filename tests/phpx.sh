#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

TMP_ROOT="$(mktemp -d)"
cleanup() { rm -rf -- "$TMP_ROOT"; }
trap cleanup EXIT INT TERM

export PHPX_LIBRARY_MODE=1
export PHPX_NO_LOG=1
# shellcheck source=PHP/phpx
source PHP/phpx
unset PHPX_LIBRARY_MODE

package_backend="$(detect_package_manager)"
case "$package_backend" in
apt | dnf | rpm | none) ;;
*) fail "unexpected package backend: $package_backend" ;;
esac
pass "package capability detection: $package_backend"

service_backend="$(detect_service_manager)"
case "$service_backend" in
systemd | service | none) ;;
*) fail "unexpected service backend: $service_backend" ;;
esac
pass "service capability detection: $service_backend"

# Unsupported package mutation must fail explicitly rather than guessing commands.
detect_package_manager() { printf 'none'; }
set +e
unsupported_output="$(package_backend_require_mutation 2>&1)"
unsupported_rc=$?
set -e
((unsupported_rc != 0)) || fail "unsupported package mutation backend unexpectedly succeeded"
assert_contains "$unsupported_output" "No supported package-mutation backend" "unsupported backend should be explicit"
pass "unsupported package mutation fails explicitly"
unset -f detect_package_manager

# Logging failures must be non-fatal and silent for read-only commands.
blocked_log="$TMP_ROOT/not-a-directory"
printf 'block\n' >"$blocked_log"
log_stdout="$TMP_ROOT/log.stdout"
log_stderr="$TMP_ROOT/log.stderr"
set +e
PHPX_NO_LOG= PHPX_LOG_DIR="$blocked_log" HOME="$TMP_ROOT" bash PHP/phpx fpm config 8.3 >"$log_stdout" 2>"$log_stderr"
log_rc=$?
set -e
((log_rc == 0)) || {
  cat "$log_stderr" >&2 || true
  fail "read-only fpm config failed because logging was unavailable"
}
assert_contains "$(cat "$log_stdout")" "PHP-FPM config paths for 8.3" "fpm config output"
[[ ! -s "$log_stderr" ]] || fail "logging failure polluted stderr for read-only command"
pass "logging is non-fatal for read-only commands"

# Read-only FPM config must not require root. Exercise the identity boundary only
# when the harness itself can switch users; ordinary CI smoke runs skip this part.
if (( EUID == 0 )) && command -v runuser >/dev/null 2>&1 && id nobody >/dev/null 2>&1; then
  nonroot_home="$TMP_ROOT/nobody-home"
  mkdir -p -- "$nonroot_home"
  chmod 777 -- "$nonroot_home"
  nonroot_output="$(runuser -u nobody -- env HOME="$nonroot_home" PHPX_NO_LOG=1 bash "$ROOT_DIR/PHP/phpx" fpm config 8.3)"
  assert_contains "$nonroot_output" "PHP-FPM config paths for 8.3" "non-root fpm config"
  pass "read-only FPM config works without root"

  set +e
  mutation_output="$(runuser -u nobody -- env HOME="$nonroot_home" PHPX_NO_LOG=1 bash "$ROOT_DIR/PHP/phpx" fpm restart 8.3 2>&1)"
  mutation_rc=$?
  set -e
  ((mutation_rc != 0)) || fail "non-root FPM restart unexpectedly succeeded"
  assert_contains "$mutation_output" "requires root privileges" "FPM mutation should enforce root"
  pass "FPM mutation requires root"
else
  printf 'SKIP: root/runuser/nobody unavailable for identity-switch privilege test\n'
fi

# Syntax checking is a generic PHP capability and must not depend on apt/systemd.
php_stub="$TMP_ROOT/php-stub"
cat >"$php_stub" <<'EOF'
#!/usr/bin/env bash
[[ "${1:-}" == "-l" ]] || exit 2
printf 'No syntax errors detected in %s\n' "${2:-}"
EOF
chmod +x "$php_stub"
project="$TMP_ROOT/project"
mkdir -p -- "$project"
printf '<?php echo "ok";\n' >"$project/example.php"
syntax_output="$(cd "$project" && PHPX_NO_LOG=1 bash "$ROOT_DIR/PHP/phpx" syntax --php "$php_stub" --no-progress)"
assert_contains "$syntax_output" "No syntax errors found" "syntax command should complete via explicit PHP binary"
pass "syntax checker is independent of package/service backends"

# Unknown commands must fail with a dedicated command error.
set +e
unknown_output="$(PHPX_NO_LOG=1 bash PHP/phpx definitely-not-a-command 2>&1)"
unknown_rc=$?
set -e
assert_eq "2" "$unknown_rc" "unknown phpx command exit code"
assert_contains "$unknown_output" "Unknown command" "unknown phpx command message"
pass "unknown command contract"

printf '\nAll phpx foundation safety checks passed.\n'
