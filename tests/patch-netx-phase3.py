#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('Network/netx')
t = p.read_text()

def one(old: str, new: str, label: str) -> None:
    global t
    if old not in t:
        raise SystemExit(f'missing patch anchor: {label}')
    t = t.replace(old, new, 1)

def regex(pattern: str, repl: str, label: str) -> None:
    global t
    t2, n = re.subn(pattern, repl, t, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'failed regex patch: {label} ({n})')
    t = t2

one('VERSION="0.4.0"', 'VERSION="0.5.0"', 'version')
one('                    [--exclude-cidr list] [--exec cmd]', '                    [--exclude-cidr list] [--exec command [args...]]\n                    # --exec is argv-only and must be the final option', 'guard usage')
one('  netx report [--out file]\n\nEOF', '  netx report [--out file]\n\nSecurity note: listener/outbound risk scoring is heuristic triage, not a security verdict.\nEOF', 'heuristic help')

old = '''NETX_DIR="${HOME}/.netx"
mkdir -p "$NETX_DIR"

split_csv() { tr ',' '\\n' <<<"$1"; }

is_private_ip() {
  local ip="$1"
  case "$ip" in
  10.* | 192.168.* | 172.1[6-9].* | 172.2[0-9].* | 172.3[0-1].* | 127.*) return 0 ;;
  ::1 | fc* | fd* | fe80:*) return 0 ;;
  esac
  return 1
}
'''
new = r'''NETX_STATE_DIR="${NETX_STATE_HOME:-${XDG_STATE_HOME:-${HOME:-/tmp}/.local/state}/netx}"
NETX_CONFIG_DIR="${NETX_CONFIG_HOME:-${XDG_CONFIG_HOME:-${HOME:-/tmp}/.config}/netx}"
NETX_CONNECT_TIMEOUT="${NETX_CONNECT_TIMEOUT:-3}"
NETX_OPERATION_TIMEOUT="${NETX_OPERATION_TIMEOUT:-10}"

ensure_state_dir() {
  mkdir -p -m 0700 -- "$NETX_STATE_DIR"
}

state_file() {
  printf '%s/%s\n' "$NETX_STATE_DIR" "$1"
}

split_csv() { tr ',' '\n' <<<"$1"; }

is_uint() { [[ "${1:-}" =~ ^[0-9]+$ ]]; }
is_positive_int() { is_uint "${1:-}" && ((10#${1} > 0)); }

validate_port() {
  local p="${1:-}"
  is_uint "$p" && ((10#$p >= 1 && 10#$p <= 65535))
}

split_endpoint() {
  local endpoint="${1:-}" host port
  if [[ "$endpoint" =~ ^\[([^]]+)\]:([^:]*)$ ]]; then
    host="${BASH_REMATCH[1]}"
    port="${BASH_REMATCH[2]}"
  elif [[ "$endpoint" == *:* ]]; then
    host="${endpoint%:*}"
    port="${endpoint##*:}"
    [[ -n "$host" ]] || host='::'
  else
    host="$endpoint"
    port=''
  fi
  printf '%s|%s\n' "$host" "$port"
}

is_non_public_ip() {
  local ip="${1:-}" a b c d
  ip="${ip#[}"
  ip="${ip%]}"
  ip="${ip%%%*}"
  ip="${ip,,}"

  if [[ "$ip" == *:* ]]; then
    case "$ip" in
      ::|::1|fc*|fd*|ff*|2001:db8:*|2001:db8::*) return 0 ;;
      fe[89ab]*:*) return 0 ;;
    esac
    return 1
  fi

  IFS='.' read -r a b c d <<<"$ip"
  for octet in "$a" "$b" "$c" "$d"; do
    is_uint "$octet" || return 1
    ((10#$octet <= 255)) || return 1
  done

  a=$((10#$a)); b=$((10#$b))
  ((a == 0 || a == 10 || a == 127)) && return 0
  ((a == 169 && b == 254)) && return 0
  ((a == 172 && b >= 16 && b <= 31)) && return 0
  ((a == 192 && b == 168)) && return 0
  ((a == 100 && b >= 64 && b <= 127)) && return 0
  ((a == 192 && b == 0)) && return 0
  ((a == 192 && b == 2)) && return 0
  ((a == 198 && (b == 18 || b == 19 || b == 51))) && return 0
  ((a == 203 && b == 0)) && return 0
  ((a >= 224)) && return 0
  return 1
}

# Compatibility name retained for callers/tests; semantics intentionally include
# reserved, loopback, link-local, documentation and shared address space.
is_private_ip() { is_non_public_ip "$@"; }

curl_bounded() {
  local max_time="${1:-$NETX_OPERATION_TIMEOUT}"
  shift || true
  curl --connect-timeout "$NETX_CONNECT_TIMEOUT" --max-time "$max_time" "$@"
}

json_escape() {
  local data char code i
  IFS= read -r -d '' data < <(cat; printf '\0') || true
  for ((i=0; i<${#data}; i++)); do
    char="${data:i:1}"
    case "$char" in
      '"') printf '\\"' ;;
      '\\') printf '\\\\' ;;
      $'\b') printf '\\b' ;;
      $'\f') printf '\\f' ;;
      $'\n') printf '\\n' ;;
      $'\r') printf '\\r' ;;
      $'\t') printf '\\t' ;;
      *)
        printf -v code '%d' "'$char"
        if ((code < 32)); then printf '\\u%04x' "$code"; else printf '%s' "$char"; fi
        ;;
    esac
  done
}

validate_json_file() {
  local file="$1"
  if have jq; then
    jq -e . "$file" >/dev/null 2>&1
  elif have python3; then
    python3 -m json.tool "$file" >/dev/null 2>&1
  else
    return 0
  fi
}

privilege_hint() {
  err "$1 may require root or Linux network capabilities (for example CAP_NET_ADMIN/CAP_NET_RAW)."
}
'''
one(old, new, 'state/address/json helpers')

one('''  local remote_ip remote_port
  remote_ip=${remote_addr%:*}
  remote_port=${remote_addr##*:}

  # Public destination
  if ! is_private_ip "$remote_ip"; then
''', '''  local remote_ip remote_port
  IFS='|' read -r remote_ip remote_port < <(split_endpoint "$remote_addr")

  # Public destination
  if ! is_non_public_ip "$remote_ip"; then
''', 'suspicious endpoint split')
one('''  if [[ "$remote_port" -ge 1024 && "$safe" -eq 0 ]]; then
''', '''  if is_uint "$remote_port" && ((10#$remote_port >= 1024)) && [[ "$safe" -eq 0 ]]; then
''', 'suspicious numeric port')
one('''      if [[ -n "$uid_name" && "$uid_name" != "root" ]] && ! is_private_ip "$remote_ip" && [[ "$safe" -eq 0 ]]; then
''', '''      if [[ -n "$uid_name" && "$uid_name" != "root" ]] && ! is_non_public_ip "$remote_ip" && [[ "$safe" -eq 0 ]]; then
''', 'suspicious public check')

# Doctor and DNS bounded operations.
t = t.replace('dig +short "$host" A', 'dig +time=2 +tries=1 +short "$host" A')
t = t.replace('traceroute -n -m 20 "$host"', 'traceroute -n -w 2 -m 20 "$host"')
t = t.replace('''        curl -sS -o /dev/null --max-time 10 \\
''', '''        curl_bounded 10 -sS -o /dev/null \\
''', 1)
regex(r'''      local tmp\n      tmp=\$\(mktemp\)\n      local cmd="openssl s_client -servername \$host -connect \$host:\$port"\n      if have timeout; then\n        cmd="timeout 5 \$cmd"\n      fi\n      if echo \| eval "\$cmd" 2>/dev/null \| openssl x509 -noout -subject -issuer -dates >"\$tmp"; then''', '''      local tmp\n      tmp=$(mktemp)\n      if _tls_s_client "$host" "$port" | openssl x509 -noout -subject -issuer -dates >"$tmp"; then''', 'doctor TLS eval')

# Bound dig throughout DNS commands.
t = t.replace('dig @"$resolver" "$name" "$type" +short', 'dig +time=2 +tries=1 @"$resolver" "$name" "$type" +short')
t = t.replace('dig "$name" "$type" +short', 'dig +time=2 +tries=1 "$name" "$type" +short')
t = t.replace('dig "$name" "$type" +trace', 'dig +time=2 +tries=1 "$name" "$type" +trace')
t = t.replace('dig -x "$ip" +short', 'dig +time=2 +tries=1 -x "$ip" +short')
t = t.replace('dig @"$resolver" +short TXT CH whoami.cloudflare', 'dig +time=2 +tries=1 @"$resolver" +short TXT CH whoami.cloudflare')
t = t.replace('dig @"$resolver" +short A whoami.cloudflare', 'dig +time=2 +tries=1 @"$resolver" +short A whoami.cloudflare')

# HTTP/proxy bounded defaults.
t = t.replace('local curl_args=(-sS --max-time "$timeout")', 'local curl_args=(-sS --connect-timeout "$NETX_CONNECT_TIMEOUT" --max-time "$timeout")')
t = t.replace('curl -sS -I --max-time "$timeout" "$url"', 'curl_bounded "$timeout" -sS -I "$url"')
t = t.replace('''    curl -sS -o /dev/null --max-time "$timeout" \\
''', '''    curl_bounded "$timeout" -sS -o /dev/null \\
''', 1)
t = t.replace('NO_PROXY="*" no_proxy="*" curl -sS -o /dev/null', 'NO_PROXY="*" no_proxy="*" curl_bounded 10 -sS -o /dev/null')
t = t.replace('  curl -sS -o /dev/null -w \'status=%{http_code} time=%{time_total}s\\n\' "$url" || echo "  failed"', '  curl_bounded 10 -sS -o /dev/null -w \'status=%{http_code} time=%{time_total}s\\n\' "$url" || echo "  failed"')
t = t.replace('curl -sS -o /dev/null --max-time "$timeout" -w "%{http_code}"', 'curl --connect-timeout 3 -sS -o /dev/null --max-time "$timeout" -w "%{http_code}"')

regex(r'''_tls_s_client\(\) \{.*?\n\}\n\ntls_info\(\)''', r'''_tls_s_client() {
  local host="$1" port="$2"
  shift 2
  local -a extra=("$@") cmd
  local endpoint
  validate_port "$port" || { err "invalid TLS port: $port"; return 2; }
  have timeout || { err "timeout is required for bounded TLS operations"; return 3; }
  if [[ "$host" == *:* && "$host" != \[*\] ]]; then endpoint="[$host]:$port"; else endpoint="$host:$port"; fi
  cmd=(openssl s_client -servername "$host" -connect "$endpoint" "${extra[@]}")
  printf '' | timeout --signal=TERM 5 "${cmd[@]}" 2>/dev/null
}

tls_info()''', 'TLS argv helper')

# State-backed connection recording.
regex(r'''conn_record\(\) \{\n  require_ss_or_netstat\n  local interval=5 duration=120 out="\$NETX_DIR/connections\.log".*?\n  echo "Recorded to \$out"\n\}''', r'''conn_record() {
  require_ss_or_netstat
  local interval=5 duration=120 out="" default_out=1
  while [[ $# -gt 0 ]]; do
    case "$1" in
    --interval) interval="$2"; shift ;;
    --duration) duration="$2"; shift ;;
    --out) out="$2"; default_out=0; shift ;;
    *) die "conn record: unknown option '$1'" ;;
    esac
    shift || true
  done
  is_positive_int "$interval" || die "conn record: --interval must be > 0"
  is_positive_int "$duration" || die "conn record: --duration must be > 0"
  if ((default_out)); then ensure_state_dir; out="$(state_file connections.log)"; fi
  local end=$((SECONDS + duration))
  : >"$out"
  while ((SECONDS < end)); do
    echo "### $(date -Is)" >>"$out"
    if have ss; then ss -tunp >>"$out" 2>/dev/null || true; else netstat -tunp >>"$out" 2>/dev/null || true; fi
    sleep "$interval"
  done
  echo "Recorded to $out"
}''', 'conn_record XDG')

one('guard_file_default="$NETX_DIR/outbound_baseline.txt"', 'guard_file_default="$(state_file outbound_baseline.txt)"', 'guard path')
one('''  if have ss; then
    ss -tunp | normalize_conn_ss_line | sort -u >"$file"
''', '''  if [[ "$file" == "$guard_file_default" ]]; then ensure_state_dir; fi
  if have ss; then
    ss -tunp | normalize_conn_ss_line | sort -u >"$file"
''', 'guard snapshot state')

# Add hook helper and replace watch parser/execution.
one('''_guard_pretty_line() {
''', '''run_guard_hook() {
  local payload="$1"
  shift
  (($#)) || return 0
  printf '%s' "$payload" | "$@"
}

_guard_pretty_line() {
''', 'guard hook helper')
regex(r'''guard_watch\(\) \{.*?\n\}\n\n# -------------------- 8\. Security''', r'''guard_watch() {
  require_ss_or_netstat
  local file="$guard_file_default" interval=20
  local exclude_user="" exclude_port="" exclude_cidr=""
  local -a exec_argv=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
    --file) file="$2"; shift 2 ;;
    --interval) interval="$2"; shift 2 ;;
    --exclude-user) exclude_user="$2"; shift 2 ;;
    --exclude-port) exclude_port="$2"; shift 2 ;;
    --exclude-cidr) exclude_cidr="$2"; shift 2 ;;
    --exec)
      shift
      (($#)) || die "guard watch: --exec requires a command"
      exec_argv=("$@")
      break
      ;;
    *) die "guard watch: unknown option '$1'" ;;
    esac
  done
  is_positive_int "$interval" || die "guard watch: --interval must be > 0"
  [[ -f "$file" ]] || guard_snapshot --file "$file"
  echo "Watching outbound connections every ${interval}s (baseline: $file)"
  while :; do
    local tmp new
    tmp=$(mktemp)
    trap 'rm -f -- "$tmp"' RETURN
    if have ss; then ss -tunp | normalize_conn_ss_line | sort -u >"$tmp"; else netstat -tunp | normalize_conn_ss_line | sort -u >"$tmp"; fi

    new=$(comm -13 "$file" "$tmp" || true)
    if [[ -n "$new" ]]; then
      section "${c_err}ALERT${c_reset} at $(date -Is)"
      while read -r line; do
        [[ -z "$line" ]] && continue
        local proto local remote pid comm user local_ip local_port remote_ip remote_port
        IFS='|' read -r proto local remote pid comm user <<<"$line"
        IFS='|' read -r local_ip local_port < <(split_endpoint "$local")
        IFS='|' read -r remote_ip remote_port < <(split_endpoint "$remote")

        if [[ -n "$exclude_user" ]]; then
          for e in $(split_csv "$exclude_user"); do [[ "$comm" == "$e" ]] && continue 2; done
        fi
        if [[ -n "$exclude_port" ]]; then
          for p in $(split_csv "$exclude_port"); do [[ "$local_port" == "$p" || "$remote_port" == "$p" ]] && continue 2; done
        fi
        if [[ -n "$exclude_cidr" ]]; then
          for c in $(split_csv "$exclude_cidr"); do case "$remote_ip" in "$c"*) continue 2 ;; esac; done
        fi
        _guard_pretty_line "$line"
      done <<<"$new"

      if ((${#exec_argv[@]})); then run_guard_hook "$new" "${exec_argv[@]}" || true; fi
    fi

    mv -- "$tmp" "$file"
    trap - RETURN
    [[ "${NETX_GUARD_ONCE:-0}" == 1 ]] && break
    sleep "$interval"
  done
}

# -------------------- 8. Security''', 'guard watch argv')

# Listener port parsing.
one('''      local port pid="" comm=""
      port="${local_addr##*:}"
''', '''      local port pid="" comm="" endpoint_host
      IFS='|' read -r endpoint_host port < <(split_endpoint "$local_addr")
''', 'listener endpoint parse')
one('''      [[ "$port" -gt 1024 ]] && warn=1
''', '''      is_uint "$port" && ((10#$port > 1024)) && warn=1
''', 'listener numeric port')

# Packet capture argv/privilege and bounded sniff HTTP.
t = t.replace('curl -k -L --max-time "$timeout" -sS \\', 'curl -k -L --connect-timeout "$NETX_CONNECT_TIMEOUT" --max-time "$timeout" -sS \\')
regex(r'''  local SUDO=""\n  if \[\[ "\$\{EUID:-\$\(id -u\)\}" -ne 0 \]\]; then\n    have sudo \|\| die "sniff pkt: need root or sudo"\n    SUDO="sudo"\n  fi''', r'''  local -a privilege=()
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    if have sudo; then privilege=(sudo --); else privilege_hint "sniff pkt"; return 1; fi
  fi''', 'sniff privilege')
one('''  echo "Running: ${SUDO:+$SUDO }${args[*]}" >&2
  exec ${SUDO:+$SUDO } "${args[@]}"
''', '''  printf 'Running:' >&2
  printf ' %q' "${privilege[@]}" "${args[@]}" >&2
  printf '\n' >&2
  exec "${privilege[@]}" "${args[@]}"
''', 'sniff exec')

# Public IP bounded fetches.
t = t.replace('curl -s https://api.seeip.org/jsonip', 'curl_bounded 8 -s https://api.seeip.org/jsonip')
t = t.replace('curl -s https://ipv4.icanhazip.com', 'curl_bounded 8 -s https://ipv4.icanhazip.com')
t = t.replace('curl -s "https://api.seeip.org/jsonip?format=json"', 'curl_bounded 8 -s "https://api.seeip.org/jsonip?format=json"')
t = t.replace('curl -s https://ipv6.icanhazip.com', 'curl_bounded 8 -s https://ipv6.icanhazip.com')

# Route resolution and native JSON escaping.
t = t.replace('dig +short "$target" A', 'dig +time=2 +tries=1 +short "$target" A')
t = t.replace('dig +short "$target" AAAA', 'dig +time=2 +tries=1 +short "$target" AAAA')
one('''    printf '{"target":"%s","ip":"%s","dev":"%s","via":"%s","src":"%s","raw":"%s"}\\n' \\
      "$target" "$ip_addr" "${dev:-}" "${gw:-}" "${src:-}" "$(printf '%s' "$out" | sed 's/"/\\\\"/g')"
''', '''    printf '{"target":"%s","ip":"%s","dev":"%s","via":"%s","src":"%s","raw":"%s"}\\n' \\
      "$(printf '%s' "$target" | json_escape)" \\
      "$(printf '%s' "$ip_addr" | json_escape)" \\
      "$(printf '%s' "${dev:-}" | json_escape)" \\
      "$(printf '%s' "${gw:-}" | json_escape)" \\
      "$(printf '%s' "${src:-}" | json_escape)" \\
      "$(printf '%s' "$out" | json_escape)"
''', 'route native JSON')

# Watch HTTP bounded per iteration.
one("code=$(curl -sS -o /dev/null -w '%{http_code}' \"$url\" || echo 0)", "code=$(curl_bounded \"${NETX_WATCH_HTTP_TIMEOUT:-10}\" -sS -o /dev/null -w '%{http_code}' \"$url\" || echo 0)", 'watch http timeout')

# XDG config and endpoint parsing in stacks.
one('local dir="${NETX_STACK_DIR:-$HOME/.config/netx/stacks}"', 'local dir="${NETX_STACK_DIR:-$NETX_CONFIG_DIR/stacks}"', 'stack config XDG')
one('''      host=${target%:*}
      port=${target##*:}
''', '''      IFS='|' read -r host port < <(split_endpoint "$target")
      validate_port "$port" || { echo "${c_err}invalid target${c_reset}"; continue; }
''', 'stack endpoint split')

# Namespace diagnostics: preserve no-surprise execution but explain capability failures.
one('''  if ! ip netns exec "$ns" ip -o addr show 2>/dev/null; then
    echo "  Cannot open network namespace '$ns'"
    echo "  Hint: this expects a netns name (from 'ip netns ls'), not an interface like 'wlp0s20f3'."
    return 1
  fi
''', '''  if ! ip netns exec "$ns" ip -o addr show 2>/dev/null; then
    echo "  Cannot open network namespace '$ns'"
    echo "  Hint: this expects a netns name (from 'ip netns ls'), not an interface like 'wlp0s20f3'."
    [[ "${EUID:-$(id -u)}" -ne 0 ]] && privilege_hint "ns inspect"
    return 1
  fi
''', 'namespace diagnostic')
regex(r'''ns_exec\(\) \{\n  have ip \|\| die "ip required"\n  local ns="\$\{1:-\}"\n  shift \|\| true\n  \[\[ -z "\$ns" \]\] && die "ns exec: ns required"\n  \[\[ \$# -eq 0 \]\] && die "ns exec: command required"\n  ip netns exec "\$ns" "\$@"\n\}''', r'''ns_exec() {
  have ip || die "ip required"
  local ns="${1:-}"
  shift || true
  [[ -z "$ns" ]] && die "ns exec: ns required"
  [[ $# -eq 0 ]] && die "ns exec: command required"
  if ! ip netns exec "$ns" "$@"; then
    [[ "${EUID:-$(id -u)}" -ne 0 ]] && privilege_hint "ns exec"
    return 1
  fi
}''', 'namespace exec diagnostic')

# Bounded path tracing.
t = t.replace('traceroute -n -m "$max_hops" "$host"', 'traceroute -n -w 2 -m "$max_hops" "$host"')

# Firewall capability diagnostics while preserving nft-first semantics.
regex(r'''fw_summary\(\) \{.*?\n\}\n\nfw_list\(\)''', r'''fw_summary() {
  section "Firewall summary"
  if have nft; then
    local out rc=0
    out=$(nft list ruleset 2>/dev/null) || rc=$?
    if ((rc != 0)); then
      privilege_hint "fw summary"
      return "$rc"
    elif [[ -z "$out" ]]; then
      echo "  nftables present with no rules"
    else
      echo "$out" | head -n 80 | sed 's/^/  /'
      local lines
      lines=$(printf '%s\n' "$out" | wc -l | awk '{print $1}')
      ((lines > 80)) && echo "  ... (truncated, use 'netx fw list --raw' for full ruleset)"
    fi
  elif have iptables; then
    if ! iptables -L -n --line-numbers | sed 's/^/  /'; then privilege_hint "fw summary"; return 1; fi
  else
    echo "  No nftables/iptables found"
  fi
  if have ufw; then ufw status 2>/dev/null | sed 's/^/  /' || true; fi
}

fw_list()''', 'firewall summary')
regex(r'''fw_list\(\) \{.*?\n\}\n\n# -------------------- 15\. Net report''', r'''fw_list() {
  local raw=0
  while [[ $# -gt 0 ]]; do case "$1" in --raw) raw=1 ;; *) die "fw list: unknown option '$1'" ;; esac; shift || true; done
  section "Firewall rules"
  if have nft; then
    if ((raw)); then nft list ruleset || { privilege_hint "fw list"; return 1; }
    else nft list ruleset | sed 's/^/  /' || { privilege_hint "fw list"; return 1; }; fi
  elif have iptables; then
    if ((raw)); then iptables-save || { privilege_hint "fw list"; return 1; }
    else iptables -S | sed 's/^/  /' || { privilege_hint "fw list"; return 1; }; fi
  else
    echo "  No nftables/iptables found"
  fi
}

# -------------------- 15. Net report''', 'firewall list')

# Lazy report state.
regex(r'''report_cmd\(\) \{\n  local out="\$NETX_DIR/net-report\.txt".*?\n  echo "Report saved to \$out"\n\}''', r'''report_cmd() {
  local out="" default_out=1
  while [[ $# -gt 0 ]]; do
    case "$1" in --out) out="$2"; default_out=0; shift ;; *) die "report: unknown option '$1'" ;; esac
    shift || true
  done
  if ((default_out)); then ensure_state_dir; out="$(state_file net-report.txt)"; fi
  {
    echo "netx report $(date -Is)"
    ip_info || true
    route_show || true
    dns_system || true
    section "Listening ports (tcp)"
    port_ls --listening --tcp --process || true
    conn_ls --outbound || true
  } >"$out"
  echo "Report saved to $out"
}''', 'report state')

# Main JSON wrapper: validate every emitted JSON document when validator capability exists.
old = '''    if ((NETX_JSON_NATIVE)); then
      cat "$out"
    else
      printf '{'
      printf '"ok":%s,' "$([[ "$rc" -eq 0 ]] && echo true || echo false)"
      printf '"exit_code":%s,' "$rc"
      printf '"cmd":"%s",' "$(printf '%s' "$cmd" | json_escape)"
      printf '"stdout":"%s",' "$(cat "$out" | json_escape)"
      printf '"stderr":"%s"' "$(cat "$errf" | json_escape)"
      printf '}\n'
    fi
    rm -f "$out" "$errf"
    return "$rc"
'''
new = '''    local jsonf
    jsonf="$(mktemp 2>/dev/null || mktemp -t netx)"
    if ((NETX_JSON_NATIVE)); then
      cp -- "$out" "$jsonf"
    else
      {
        printf '{'
        printf '"ok":%s,' "$([[ "$rc" -eq 0 ]] && echo true || echo false)"
        printf '"exit_code":%s,' "$rc"
        printf '"cmd":"%s",' "$(printf '%s' "$cmd" | json_escape)"
        printf '"stdout":"%s",' "$(cat "$out" | json_escape)"
        printf '"stderr":"%s"' "$(cat "$errf" | json_escape)"
        printf '}\\n'
      } >"$jsonf"
    fi
    if ! validate_json_file "$jsonf"; then
      err "internal JSON serialization failure"
      rm -f -- "$out" "$errf" "$jsonf"
      return 70
    fi
    cat "$jsonf"
    rm -f -- "$out" "$errf" "$jsonf"
    return "$rc"
'''
one(old, new, 'JSON wrapper')

# Library mode for deterministic helper tests.
one('\n\nmain "$@"\n', '\n\nif [[ "${NETX_LIBRARY_MODE:-0}" == 1 ]]; then\n  return 0 2>/dev/null || exit 0\nfi\n\nmain "$@"\n', 'library mode')

# Final invariant: netx must not retain shell eval execution.
if re.search(r'(^|[;|&(){}[:space:]])eval([[:space:]]|$)', t):
    raise SystemExit('eval remains in netx after patch')

p.write_text(t)
