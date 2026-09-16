#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

TMP_ROOT="$(mktemp -d)"
SERVER_PID=""
NS_NAME="netx-test-$$"
cleanup() {
  [[ -n "$SERVER_PID" ]] && kill "$SERVER_PID" 2>/dev/null || true
  if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    sudo ip netns del "$NS_NAME" >/dev/null 2>&1 || true
  fi
  rm -rf -- "$TMP_ROOT"
  rm -f -- /tmp/netx-eval-pwn
}
trap cleanup EXIT INT TERM

export HOME="$TMP_ROOT/home"
export XDG_STATE_HOME="$TMP_ROOT/state"
export XDG_CONFIG_HOME="$TMP_ROOT/config"
mkdir -p -- "$HOME" "$XDG_CONFIG_HOME/netx/stacks"

# Stateless commands must remain genuinely stateless.
Network/netx --version >/dev/null
[[ ! -e "$XDG_STATE_HOME/netx" ]] || fail "netx --version created state directory"
pass "stateless startup does not create state"

# Source helpers without entering main.
export NETX_LIBRARY_MODE=1
# shellcheck source=/dev/null
source Network/netx
unset NETX_LIBRARY_MODE

assert_eq '127.0.0.1|8080' "$(split_endpoint '127.0.0.1:8080')" "IPv4 endpoint parsing"
assert_eq '::1|443' "$(split_endpoint '[::1]:443')" "bracketed IPv6 endpoint parsing"
assert_eq '2001:db8::1|8443' "$(split_endpoint '2001:db8::1:8443')" "unbracketed IPv6 endpoint parsing"
assert_eq '*|53' "$(split_endpoint '*:53')" "wildcard endpoint parsing"
pass "IPv4/IPv6 endpoint parsing"

for addr in 10.1.2.3 127.0.0.1 169.254.2.3 172.16.0.1 172.31.255.254 192.168.1.2 100.64.0.1 192.0.2.1 198.51.100.4 203.0.113.5 ::1 fd00::1 fe80::1 ff02::1 2001:db8::1; do
  is_non_public_ip "$addr" || fail "expected non-public address: $addr"
done
for addr in 1.1.1.1 8.8.8.8 93.184.216.34 2606:4700:4700::1111; do
  if is_non_public_ip "$addr"; then fail "expected public address: $addr"; fi
done
pass "private/reserved/public address classification"

# json_escape must produce strings jq accepts, including controls/newlines.
escaped="$(printf 'a"b\\c\nline\tend' | json_escape)"
printf '"%s"\n' "$escaped" | jq -e . >/dev/null
pass "JSON escaping is parseable"

# TLS helper must preserve hostile-looking host text as one argv value, never shell-evaluate it.
MOCK_BIN="$TMP_ROOT/mock-bin"
mkdir -p "$MOCK_BIN"
cat >"$MOCK_BIN/openssl" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" >"${NETX_ARG_CAPTURE:?}"
cat >/dev/null
exit 1
EOF
chmod +x "$MOCK_BIN/openssl"
export NETX_ARG_CAPTURE="$TMP_ROOT/openssl.args"
OLD_PATH="$PATH"
PATH="$MOCK_BIN:$PATH"
_tls_s_client 'example.invalid;touch /tmp/netx-eval-pwn' 443 -showcerts >/dev/null 2>&1 || true
PATH="$OLD_PATH"
[[ ! -e /tmp/netx-eval-pwn ]] || fail "TLS host was shell-evaluated"
grep -Fx 'example.invalid;touch /tmp/netx-eval-pwn' "$NETX_ARG_CAPTURE" >/dev/null || fail "TLS host was not preserved as argv"
pass "TLS execution is argv-safe"

# Guard hooks consume alert data on stdin and preserve argv boundaries.
cat >"$TMP_ROOT/hook" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" >"${NETX_HOOK_ARGS:?}"
cat >"${NETX_HOOK_STDIN:?}"
EOF
chmod +x "$TMP_ROOT/hook"
export NETX_HOOK_ARGS="$TMP_ROOT/hook.args" NETX_HOOK_STDIN="$TMP_ROOT/hook.stdin"
run_guard_hook $'tcp|127.0.0.1:1|8.8.8.8:53|1|proc|user\n' "$TMP_ROOT/hook" 'arg with spaces'
assert_eq 'arg with spaces' "$(cat "$NETX_HOOK_ARGS")" "guard hook argv"
grep -F '8.8.8.8:53' "$NETX_HOOK_STDIN" >/dev/null || fail "guard hook did not receive alert data"
pass "guard hook argv/stdin boundary"

# Local bounded HTTP path + JSON wrapper.
python3 - "$TMP_ROOT/server.port" <<'PY' &
import http.server, socketserver, sys
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
    def log_message(self, *_): pass
with socketserver.TCPServer(('127.0.0.1', 0), Handler) as httpd:
    open(sys.argv[1], 'w').write(str(httpd.server_address[1]))
    httpd.serve_forever()
PY
SERVER_PID=$!
for _ in {1..50}; do [[ -s "$TMP_ROOT/server.port" ]] && break; sleep 0.1; done
[[ -s "$TMP_ROOT/server.port" ]] || fail "local HTTP fixture did not start"
PORT="$(cat "$TMP_ROOT/server.port")"
Network/netx http trace "http://127.0.0.1:$PORT" --timeout 2 >/dev/null
Network/netx --json http trace "http://127.0.0.1:$PORT" --timeout 2 | jq -e '.ok == true and .exit_code == 0' >/dev/null
pass "bounded local HTTP and generic JSON output"

if command -v ip >/dev/null 2>&1; then
  Network/netx --json route explain 127.0.0.1 | jq -e . >/dev/null
  pass "native route JSON is parseable"
fi

# nftables is the preferred firewall backend when both are available.
cat >"$MOCK_BIN/nft" <<'EOF'
#!/usr/bin/env bash
echo nft-selected
EOF
cat >"$MOCK_BIN/iptables" <<'EOF'
#!/usr/bin/env bash
echo iptables-selected
EOF
cat >"$MOCK_BIN/iptables-save" <<'EOF'
#!/usr/bin/env bash
echo iptables-save-selected
EOF
chmod +x "$MOCK_BIN/nft" "$MOCK_BIN/iptables" "$MOCK_BIN/iptables-save"
PATH="$MOCK_BIN:$OLD_PATH"
fw_out="$(fw_list --raw)"
PATH="$OLD_PATH"
grep -F 'nft-selected' <<<"$fw_out" >/dev/null || fail "nft backend was not preferred"
if grep -Fq 'iptables-selected' <<<"$fw_out"; then fail "iptables used despite nft availability"; fi
pass "nftables preference with iptables fallback"

# Network namespace fixture when the runner allows it.
if command -v ip >/dev/null 2>&1 && command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  if sudo ip netns add "$NS_NAME" 2>/dev/null; then
    sudo ip netns exec "$NS_NAME" ip link set lo up
    sudo Network/netx ns inspect "$NS_NAME" >/dev/null
    sudo ip netns exec "$NS_NAME" Network/netx --version >/dev/null 2>&1 || true
    sudo ip netns del "$NS_NAME"
    pass "network namespace inspection fixture"
  else
    printf 'SKIP: network namespace creation not permitted by runner\n'
  fi
else
  printf 'SKIP: network namespace test requires passwordless sudo + iproute2\n'
fi

if grep -Eq '(^|[[:space:]])eval([[:space:]]|$)' Network/netx; then
  fail "netx still contains eval execution"
fi
pass "netx has no eval execution boundary"

printf '\nAll netx Phase 3 checks passed.\n'
