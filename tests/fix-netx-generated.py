#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('Network/netx')
t = p.read_text()

old = '''        local proto local remote pid comm user local_ip local_port remote_ip remote_port
        IFS='|' read -r proto local remote pid comm user <<<"$line"
        IFS='|' read -r local_ip local_port < <(split_endpoint "$local")
        IFS='|' read -r remote_ip remote_port < <(split_endpoint "$remote")
'''
new = '''        local proto local_ep remote_ep pid comm user local_ip local_port remote_ip remote_port
        IFS='|' read -r proto local_ep remote_ep pid comm user <<<"$line"
        IFS='|' read -r local_ip local_port < <(split_endpoint "$local_ep")
        IFS='|' read -r remote_ip remote_port < <(split_endpoint "$remote_ep")
'''
if old not in t:
    raise SystemExit('generated guard variable block not found')
t = t.replace(old, new, 1)

pattern = r'''json_escape\(\) \{.*?\n\}\n\nvalidate_json_file\(\)'''
replacement = r'''json_escape() {
  local data
  data="$(cat)"
  data=${data//\\/\\\\}
  data=${data//\"/\\\"}
  data=${data//$'\b'/\\b}
  data=${data//$'\f'/\\f}
  data=${data//$'\n'/\\n}
  data=${data//$'\r'/\\r}
  data=${data//$'\t'/\\t}
  printf '%s' "$data"
}

validate_json_file()'''
t, count = re.subn(pattern, lambda _m: replacement, t, count=1, flags=re.S)
if count != 1:
    raise SystemExit('generated JSON escape function not found')

# The primary transform intentionally lives in a Python triple-quoted string;
# normalize its format string to one printf escape so the JSON document ends
# with an actual newline rather than a literal backslash-n token.
t = t.replace(r"printf '}\\n'", r"printf '}\n'", 1)

# `read` returns failure at EOF when curl -w has no trailing newline. Under
# `set -e` that made an otherwise successful trace command exit 1. Capture the
# one-line metrics with command substitution instead and retain hard bounds.
http_pattern = r'''http_trace\(\) \{.*?\n\}\n\nproxy_cmd\(\)'''
http_replacement = r'''http_trace() {
  require_curl
  local url="" timeout=5
  while [[ $# -gt 0 ]]; do
    case "$1" in
    --timeout)
      timeout="$2"
      shift
      ;;
    *) url="$1" ;;
    esac
    shift || true
  done
  [[ -z "$url" ]] && die "http trace: url required"
  is_positive_int "$timeout" || die "http trace: --timeout must be > 0"

  section "HTTP TRACE"
  kv "URL" "$url"
  kv "Timeout" "${timeout}s"

  local out
  out="$(curl_bounded "$timeout" -sS -o /dev/null \
    -w 'dns=%{time_namelookup}s connect=%{time_connect}s tls=%{time_appconnect}s ttfb=%{time_starttransfer}s total=%{time_total}s status=%{http_code} size=%{size_download}B redirects=%{num_redirects}' \
    "$url" || printf '%s' 'dns=0 connect=0 tls=0 ttfb=0 total=0 status=000 size=0 redirects=0')"
  local tok k v
  for tok in $out; do
    k=${tok%%=*}
    v=${tok#*=}
    case "$k" in
    dns) kv "DNS" "$v" ;;
    connect) kv "Connect" "$v" ;;
    tls) kv "TLS" "$v" ;;
    ttfb) kv "TTFB" "$v" ;;
    total) kv "Total" "$v" ;;
    status) kv "Status" "$v" ;;
    size) kv "Size" "$v" ;;
    redirects) kv "Redirects" "$v" ;;
    esac
  done
  return 0
}

proxy_cmd()'''
t, count = re.subn(http_pattern, lambda _m: http_replacement, t, count=1, flags=re.S)
if count != 1:
    raise SystemExit('generated http_trace function not found')

# The source previously nested route_explain inside route_show because the
# route_show closing brace was misplaced. Replace both functions as one block
# so direct `route explain` is always defined and native JSON is escaped safely.
route_pattern = r'''route_show\(\) \{.*?\n\}\n\n# -------------------- 10\. Watchers / Waiters'''
route_replacement = r'''route_show() {
  have ip || die "ip required"
  section "Routes"
  printf '%-8s %-20s %-12s %-s\n' "Type" "Destination" "Dev" "Extra"
  ip route show | while read -r dst rest; do
    local dev extra typ="other"
    dev=$(grep -o 'dev [^ ]*' <<<"$rest" | awk '{print $2}' || true)
    if [[ -n "$dev" ]]; then extra=$(sed "s/.*dev $dev//" <<<"$rest"); else extra="$rest"; fi
    [[ "$dst" == "default" ]] && typ="default"
    printf '%-8s %-20s %-12s %-s\n' "$typ" "$dst" "$dev" "$extra"
  done
}

route_explain() {
  local target="${1:-}"
  [[ -n "$target" ]] || die "route explain: host required"
  have ip || die "route explain: ip required"

  local ip_addr=""
  if [[ "$target" == *:* || "$target" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    ip_addr="$target"
  elif have dig; then
    ip_addr=$(dig +time=2 +tries=1 +short "$target" A 2>/dev/null | head -n1 || true)
    [[ -z "$ip_addr" ]] && ip_addr=$(dig +time=2 +tries=1 +short "$target" AAAA 2>/dev/null | head -n1 || true)
  fi
  if [[ -z "$ip_addr" ]] && have getent; then
    ip_addr=$(getent ahostsv4 "$target" 2>/dev/null | awk 'NR==1{print $1}' || true)
    [[ -z "$ip_addr" ]] && ip_addr=$(getent ahostsv6 "$target" 2>/dev/null | awk 'NR==1{print $1}' || true)
  fi
  [[ -z "$ip_addr" ]] && ip_addr="$target"

  local out
  out=$(ip route get "$ip_addr" 2>/dev/null || true)

  if ((NETX_QUIET)); then
    local dev
    dev=$(grep -oE ' dev [^ ]+' <<<"$out" | awk '{print $2}' || true)
    [[ -n "$dev" ]] && { echo "$dev"; return 0; }
    echo "$out"
    return 0
  fi

  if ((NETX_JSON)); then
    NETX_JSON_NATIVE=1
    local dev gw src
    dev=$(grep -oE ' dev [^ ]+' <<<"$out" | awk '{print $2}' || true)
    gw=$(grep -oE ' via [^ ]+' <<<"$out" | awk '{print $2}' || true)
    src=$(grep -oE ' src [^ ]+' <<<"$out" | awk '{print $2}' || true)
    printf '{"target":"%s","ip":"%s","dev":"%s","via":"%s","src":"%s","raw":"%s"}\n' \
      "$(printf '%s' "$target" | json_escape)" \
      "$(printf '%s' "$ip_addr" | json_escape)" \
      "$(printf '%s' "${dev:-}" | json_escape)" \
      "$(printf '%s' "${gw:-}" | json_escape)" \
      "$(printf '%s' "${src:-}" | json_escape)" \
      "$(printf '%s' "$out" | json_escape)"
    return 0
  fi

  section "Route explain"
  kv "Target" "$target"
  kv "Resolved IP" "$ip_addr"
  if [[ -z "$out" ]]; then
    echo "  ${c_err}No route found${c_reset}"
    return 1
  fi
  echo "  $out"
  local dev gw src
  dev=$(grep -oE ' dev [^ ]+' <<<"$out" | awk '{print $2}' || true)
  gw=$(grep -oE ' via [^ ]+' <<<"$out" | awk '{print $2}' || true)
  src=$(grep -oE ' src [^ ]+' <<<"$out" | awk '{print $2}' || true)
  [[ -n "$dev" ]] && kv "Interface" "$dev"
  [[ -n "$gw" ]] && kv "Gateway" "$gw"
  [[ -n "$src" ]] && kv "Source IP" "$src"
  return 0
}

# -------------------- 10. Watchers / Waiters'''
t, count = re.subn(route_pattern, lambda _m: route_replacement, t, count=1, flags=re.S)
if count != 1:
    raise SystemExit('generated route block not found')

p.write_text(t)
