#!/usr/bin/env python3
from pathlib import Path

path = Path("Clean/cleanx")
text = path.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"expected block not found:\n{old[:240]}")
    text = text.replace(old, new, 1)


replace_once(
'''# Config files (optional, sourced if present):
#   /etc/cleanfy.conf
#   ~/.config/cleanfy.conf
#   --config=/path/to/custom.conf
#
# EXCLUDE_GLOBS / INCLUDE_GLOBS should be bash arrays, e.g.:
#   EXCLUDE_GLOBS=( "/var/log/private/*" "/var/tmp/do-not-touch/*" )
#   INCLUDE_GLOBS=( "*.log" "*.gz" )
''',
'''# Config files use a declarative KEY=VALUE format; they are never sourced.
# Preferred paths:
#   /etc/cleanx.conf
#   ~/.config/cleanx.conf
# Legacy cleanfy paths are still read first for scalar-key compatibility:
#   /etc/cleanfy.conf
#   ~/.config/cleanfy.conf
# Extra config: --config=/path/to/custom.conf
# Repeat EXCLUDE_GLOB=... / INCLUDE_GLOB=... for multiple patterns.
''')

replace_once(
'''TARGET_USER="${SUDO_USER:-${USER}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6 || echo "$HOME")"
LOCK="/tmp/.cleanfy.lock"
''',
'''TARGET_USER="${SUDO_USER:-${USER:-}}"
TARGET_HOME=""
LOCK=""
LOCK_FD=""
LOCK_DIR_FALLBACK=""
''')

replace_once(
'''take_lock() {
  if [[ -e "$LOCK" ]]; then
    die "Another ${TOOL_NAME} run seems active (lock: $LOCK). Remove if stale."
  fi
  echo $$ >"$LOCK"
  trap 'rm -f "$LOCK"' EXIT
}

asroot() { [[ $EUID -eq 0 ]] || die "Run as root (sudo) for system cleanup."; }

preflight() {
  # Safety: bail if rootfs >= 98% used unless --force
  local use_pct
  use_pct=$(df -P / | awk 'NR==2{gsub("%","",$5); print $5+0}')
  if ((use_pct >= 98 && !FORCE_RUN)); then
    warn "Root filesystem at ${use_pct}% use. Use --force to proceed."
    exit 1
  fi
}
''',
'''take_lock() {
  local lock_base uid
  uid="$(id -u)"

  if [[ -n "${XDG_RUNTIME_DIR:-}" && -d "$XDG_RUNTIME_DIR" && -w "$XDG_RUNTIME_DIR" ]]; then
    lock_base="$XDG_RUNTIME_DIR"
  elif [[ "$EUID" -eq 0 && -d /run/lock && -w /run/lock ]]; then
    lock_base="/run/lock"
  else
    lock_base="${TMPDIR:-/tmp}/cleanx-${uid}"
    (umask 077 && mkdir -p -- "$lock_base") || die "Unable to create lock directory: $lock_base"
    chmod 700 -- "$lock_base" 2>/dev/null || true
  fi

  if command -v flock >/dev/null 2>&1; then
    LOCK="$lock_base/cleanx.lock"
    exec {LOCK_FD}>"$LOCK" || die "Unable to open lock file: $LOCK"
    flock -n "$LOCK_FD" || die "Another ${TOOL_NAME} run is active (lock: $LOCK)."
  else
    LOCK_DIR_FALLBACK="$lock_base/cleanx.lock.d"
    mkdir -- "$LOCK_DIR_FALLBACK" 2>/dev/null || die "Another ${TOOL_NAME} run is active (lock: $LOCK_DIR_FALLBACK)."
    trap 'rmdir -- "$LOCK_DIR_FALLBACK" 2>/dev/null || true' EXIT INT TERM
  fi
}

asroot() { [[ $EUID -eq 0 ]] || die "Run as root (sudo) for system cleanup."; }

preflight() {
  local use_pct
  use_pct=$(df -P / | awk 'NR==2{gsub("%","",$5); print $5+0}')
  if ((use_pct >= 98 && !FORCE_RUN)); then
    warn "Root filesystem is ${use_pct}% full; continuing because selected cleanx tasks reclaim space. Use --force to suppress this warning."
  fi
}
''')

marker = '''# ---------- Doctor / Config / Completions ----------
'''
insert = r'''# ---------- Declarative config / target identity ----------
trim_ws() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

config_unquote() {
  local value
  value="$(trim_ws "$1")"
  if [[ ${#value} -ge 2 ]]; then
    if [[ "${value:0:1}" == '"' && "${value: -1}" == '"' ]] ||
      [[ "${value:0:1}" == "'" && "${value: -1}" == "'" ]]; then
      value="${value:1:${#value}-2}"
    fi
  fi
  printf '%s' "$value"
}

config_bool() {
  case "${1,,}" in
  1 | true | yes | on) printf '1' ;;
  0 | false | no | off) printf '0' ;;
  *) return 1 ;;
  esac
}

apply_config_entry() {
  local key="$1" value="$2" parsed
  value="$(config_unquote "$value")"

  case "$key" in
  CHANNEL) CHANNEL="$value" ;;
  JOURNAL_KEEP) JOURNAL_KEEP="$value" ;;
  LOG_MAX_SIZE) LOG_MAX_SIZE="$value" ;;
  TMP_DAYS) TMP_DAYS="$value" ;;
  SNAP_RETAIN) SNAP_RETAIN="$value" ;;
  TARGET_USER) TARGET_USER="$value" ;;
  QUOTA_BYTES) QUOTA_BYTES="$(parse_size "$value")" ;;
  INODE_PATH) INODE_PATH="$value" ;;
  INODE_DEPTH) INODE_DEPTH="$value" ;;
  INODE_TOP) INODE_TOP="$value" ;;
  AGGRESSIVE | LOW_IMPACT | FORCE_RUN | SECURE_ERASE)
    parsed="$(config_bool "$value")" || {
      warn "Ignoring invalid boolean config: $key=$value"
      return 0
    }
    printf -v "$key" '%s' "$parsed"
    ;;
  EXCLUDE_GLOB) EXCLUDE_GLOBS+=("$value") ;;
  INCLUDE_GLOB) INCLUDE_GLOBS+=("$value") ;;
  EXCLUDE_GLOBS | INCLUDE_GLOBS)
    warn "Ignoring legacy array config '$key'; use repeated ${key%S}=VALUE entries instead."
    ;;
  TARGET_HOME)
    warn "Ignoring config TARGET_HOME; home is resolved from the system account database."
    ;;
  *) warn "Ignoring unknown config key: $key" ;;
  esac
}

load_config_file() {
  local file="$1" required="${2:-0}" raw line key value
  if [[ ! -f "$file" ]]; then
    ((required)) && die "Config file not found: $file"
    return 0
  fi

  while IFS= read -r raw || [[ -n "$raw" ]]; do
    line="$(trim_ws "$raw")"
    [[ -z "$line" || "${line:0:1}" == '#' ]] && continue

    if [[ ! "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]]; then
      warn "Ignoring non-declarative config line in $file: $line"
      continue
    fi

    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    apply_config_entry "$key" "$value"
  done <"$file"
}

load_default_configs() {
  local config_home="${XDG_CONFIG_HOME:-${HOME:-}/.config}"
  load_config_file /etc/cleanfy.conf 0
  [[ -n "$config_home" ]] && load_config_file "$config_home/cleanfy.conf" 0
  load_config_file /etc/cleanx.conf 0
  [[ -n "$config_home" ]] && load_config_file "$config_home/cleanx.conf" 0
}

resolve_target_user() {
  local entry _pw _uid _gid _gecos home _shell

  if [[ -z "$TARGET_USER" ]]; then
    TARGET_USER="$(id -un 2>/dev/null || true)"
  fi
  [[ -n "$TARGET_USER" ]] || die "Unable to determine target user. Use --user=NAME."

  entry="$(getent passwd "$TARGET_USER" 2>/dev/null || true)"
  [[ -n "$entry" ]] || die "Target user does not exist: $TARGET_USER"
  IFS=: read -r _pw _pw _uid _gid _gecos home _shell <<<"$entry"

  [[ "$home" == /* ]] || die "Target user home is not absolute: $TARGET_USER -> $home"
  [[ "$home" != "/" ]] || die "Refusing target home '/': $TARGET_USER"
  [[ -d "$home" ]] || die "Target user home does not exist: $TARGET_USER -> $home"
  TARGET_HOME="$home"
}

'''
if marker not in text:
    raise SystemExit("config insertion marker missing")
text = text.replace(marker, insert + marker, 1)

replace_once(
'''  --force                   run even if rootfs >= 98% used
''',
'''  --force                   suppress the >=98% rootfs warning
''')
replace_once(
'''  --config=PATH             extra config file to source
  --channel=NAME            update/check channel (default: main)
''',
'''  --config=PATH             extra declarative KEY=VALUE config file
  --channel=NAME            update/check channel (default: stable)
''')

replace_once(
'''# Config files (after defaults, before CLI args)
[[ -f /etc/cleanfy.conf ]] && . /etc/cleanfy.conf
[[ -f "$HOME/.config/cleanfy.conf" ]] && . "$HOME/.config/cleanfy.conf"

TASKS=()
# early pass for --config and --channel
for arg in "$@"; do
  case "$arg" in
  --config=*) CONFIG_OVERRIDE_FILE="${arg#*=}" ;;
  --channel=*) CHANNEL="${arg#*=}" ;;
  esac
done
[[ -n "$CONFIG_OVERRIDE_FILE" && -f "$CONFIG_OVERRIDE_FILE" ]] && . "$CONFIG_OVERRIDE_FILE"

# Now parse all args
''',
'''TASKS=()
# Resolve only the explicit config path early. All normal CLI options are parsed
# after config loading so command-line values always win over config files.
for arg in "$@"; do
  case "$arg" in
  --config=*) CONFIG_OVERRIDE_FILE="${arg#*=}" ;;
  esac
done

load_default_configs
[[ -n "$CONFIG_OVERRIDE_FILE" ]] && load_config_file "$CONFIG_OVERRIDE_FILE" 1
resolve_target_user

# Now parse all args
''')

replace_once(
'''  --user=*)
    TARGET_USER="${arg#*=}"
    TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6 || echo "$HOME")"
    ;;
''',
'''  --user=*)
    TARGET_USER="${arg#*=}"
    resolve_target_user
    ;;
''')

replace_once(
'''  --help | -h)
    usage
    exit 0
    ;;
  *) TASKS+=("$arg") ;;
''',
'''  --help | -h)
    usage
    exit 0
    ;;
  --report) TASKS+=("report") ;;
  --*) die "Unknown option: $arg" ;;
  *) TASKS+=("$arg") ;;
''')

path.write_text(text)
