#!/usr/bin/env python3
from pathlib import Path

path = Path("PHP/phpx")
text = path.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"expected block not found:\n{old[:300]}")
    text = text.replace(old, new, 1)


# Logging must never make a read-only command fail or print setup chatter.
start = text.index("setup_logging() {")
end = text.index("\n}\n\n################################################################################\n# Logging Helper", start) + 2
text = text[:start] + r'''setup_logging() {
  if [[ -n "${PHPX_NO_LOG:-}" ]]; then
    LOG_FILE=""
    return 0
  fi

  local log_dir="${PHPX_LOG_DIR:-}"
  if [[ -z "$log_dir" ]]; then
    if [[ "$EUID" -eq 0 ]]; then
      log_dir="/var/log/phpx"
    else
      log_dir="${XDG_STATE_HOME:-${HOME:-/tmp}/.local/state}/phpx"
    fi
  fi

  if ! mkdir -p -- "$log_dir" 2>/dev/null; then
    LOG_FILE=""
    return 0
  fi

  LOG_FILE="$log_dir/$(date +'%Y-%m-%d').log"
  if ! touch -- "$LOG_FILE" 2>/dev/null; then
    LOG_FILE=""
  fi
}
''' + text[end:]

replace_once(
'''  # If LOG_FILE is somehow empty or missing, log a warning to stderr and return.
  if [[ -z "$LOG_FILE" ]]; then
    echo -e "${RED}Warning: LOG_FILE not set. Logging to stderr:${NC}" >&2
    echo -e "$current_time - [$level] - $message" >&2
    return
  fi

  # Attempt to write to the log file. If that fails, fall back to stderr.
  if ! echo "$current_time - [$level] - $message" >>"$LOG_FILE"; then
    echo -e "${RED}Warning: Failed to write to $LOG_FILE. Logging to stderr:${NC}" >&2
    echo -e "$current_time - [$level] - $message" >&2
  fi
''',
'''  # Logging is deliberately best-effort. Operational output must not be polluted
  # and read-only commands must never fail because a log directory is unavailable.
  [[ -n "$LOG_FILE" ]] || return 0
  printf '%s - [%s] - %s\n' "$current_time" "$level" "$message" >>"$LOG_FILE" 2>/dev/null || true
''')

# Insert capability/platform helpers immediately after require_sudo.
needle = '''require_sudo() {
  # Ensures the script is run with root privileges (either as root or via sudo).
  # If not, we exit with code 1 and log the error.
  if [[ "$EUID" -ne 0 ]]; then
    echo -e "${RED}Please run this script with sudo or as root.${NC}"
    log_action "ERROR" "Script not run with sudo (EUID=$EUID)."
    exit 1
  fi
}
'''
replacement = needle + r'''
################################################################################
# Platform / package / service capabilities
################################################################################
require_root_for() {
  local operation="${1:-this operation}"
  if [[ "$EUID" -ne 0 ]]; then
    echo -e "${RED}${operation} requires root privileges.${NC}" >&2
    log_action "ERROR" "$operation requires root privileges (EUID=$EUID)."
    return 1
  fi
}

detect_package_manager() {
  if command -v apt-get >/dev/null 2>&1 && command -v dpkg-query >/dev/null 2>&1; then
    printf 'apt'
  elif command -v dnf >/dev/null 2>&1 && command -v rpm >/dev/null 2>&1; then
    printf 'dnf'
  elif command -v rpm >/dev/null 2>&1; then
    printf 'rpm'
  else
    printf 'none'
  fi
}

package_backend_require_mutation() {
  local backend
  backend="$(detect_package_manager)"
  case "$backend" in
  apt | dnf) printf '%s' "$backend" ;;
  *)
    echo -e "${RED}No supported package-mutation backend is available (detected: $backend).${NC}" >&2
    return 1
    ;;
  esac
}

package_installed() {
  local package="$1"
  case "$(detect_package_manager)" in
  apt) dpkg-query -W -f='${Status}' -- "$package" 2>/dev/null | grep -q '^install ok installed$' ;;
  dnf | rpm) rpm -q --quiet -- "$package" ;;
  *) return 1 ;;
  esac
}

package_install() {
  local backend
  backend="$(package_backend_require_mutation)" || return 1
  case "$backend" in
  apt)
    apt_update_once
    DEBIAN_FRONTEND=noninteractive apt-get install -y -- "$@"
    ;;
  dnf) dnf install -y -- "$@" ;;
  esac
}

package_remove() {
  local backend
  backend="$(package_backend_require_mutation)" || return 1
  case "$backend" in
  apt) DEBIAN_FRONTEND=noninteractive apt-get purge -y -- "$@" ;;
  dnf) dnf remove -y -- "$@" ;;
  esac
}

package_autoremove() {
  case "$(detect_package_manager)" in
  apt) DEBIAN_FRONTEND=noninteractive apt-get autoremove -y ;;
  dnf) dnf autoremove -y ;;
  *) return 0 ;;
  esac
}

detect_service_manager() {
  if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    printf 'systemd'
  elif command -v service >/dev/null 2>&1; then
    printf 'service'
  else
    printf 'none'
  fi
}

service_exists() {
  local service_name="$1"
  case "$(detect_service_manager)" in
  systemd) systemctl list-unit-files --type=service --no-legend 2>/dev/null | awk '{print $1}' | grep -Fxq "${service_name}.service" ;;
  service) [[ -x "/etc/init.d/$service_name" ]] ;;
  *) return 1 ;;
  esac
}

service_is_active() {
  local service_name="$1"
  case "$(detect_service_manager)" in
  systemd) systemctl is-active --quiet "$service_name" 2>/dev/null ;;
  service) service "$service_name" status >/dev/null 2>&1 ;;
  *) return 1 ;;
  esac
}

service_action() {
  local action="$1" service_name="$2"
  case "$(detect_service_manager)" in
  systemd) systemctl "$action" "$service_name" ;;
  service)
    case "$action" in
    start | stop | restart | reload | status) service "$service_name" "$action" ;;
    *) echo -e "${RED}Service action '$action' requires systemd.${NC}" >&2; return 1 ;;
    esac
    ;;
  *) echo -e "${RED}No supported service manager is available.${NC}" >&2; return 1 ;;
  esac
}

service_enable_action() {
  local action="$1" service_name="$2"
  [[ "$(detect_service_manager)" == "systemd" ]] || {
    echo -e "${RED}Service '$action' requires systemd.${NC}" >&2
    return 1
  }
  systemctl "$action" "$service_name"
}

find_php_binary() {
  local version="${1:-}" candidate
  if [[ -n "$version" ]]; then
    for candidate in "/usr/bin/php$version" "/usr/local/bin/php$version"; do
      [[ -x "$candidate" ]] && { printf '%s' "$candidate"; return 0; }
    done
    return 1
  fi
  command -v php 2>/dev/null
}
'''
replace_once(needle, replacement)

# apt update helper must explicitly be apt-only.
replace_once(
'''apt_update_once() {
  # Purpose: run `apt update` at most once per script execution.
  if [[ -z "${_PHPX_APT_UPDATED:-}" ]]; then
    apt update -y 2>&1 | show_last_lines
    _PHPX_APT_UPDATED=1
  fi
}
''',
'''apt_update_once() {
  [[ "$(detect_package_manager)" == "apt" ]] || {
    echo -e "${RED}APT backend is not available on this system.${NC}" >&2
    return 1
  }
  if [[ -z "${_PHPX_APT_UPDATED:-}" ]]; then
    apt-get update 2>&1 | show_last_lines
    _PHPX_APT_UPDATED=1
  fi
}
''')

# Generic version discovery must not require Debian package metadata.
start = text.index("list_php_versions() {")
end = text.index("\n}\n\n################################################################################\n# PHP Info", start) + 2
text = text[:start] + r'''list_php_versions() {
  local -a versions=()
  local candidate version

  shopt -s nullglob
  for candidate in /usr/bin/php[0-9]*.[0-9]* /usr/local/bin/php[0-9]*.[0-9]*; do
    [[ -x "$candidate" ]] || continue
    version="${candidate##*/php}"
    [[ "$version" =~ ^[0-9]+\.[0-9]+$ ]] && versions+=("$version")
  done
  shopt -u nullglob

  if command -v php >/dev/null 2>&1; then
    version="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;' 2>/dev/null || true)"
    [[ "$version" =~ ^[0-9]+\.[0-9]+$ ]] && versions+=("$version")
  fi

  if ((${#versions[@]} == 0)); then
    echo -e "${YELLOW}No PHP CLI installations were discovered.${NC}"
    return 0
  fi

  mapfile -t versions < <(printf '%s\n' "${versions[@]}" | sort -Vu)
  local default_path default_version=""
  default_path="$(command -v php 2>/dev/null || true)"
  [[ -n "$default_path" ]] && default_version="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;' 2>/dev/null || true)"

  echo -e "${GREEN}Discovered PHP versions:${NC}"
  for version in "${versions[@]}"; do
    candidate="$(find_php_binary "$version" 2>/dev/null || true)"
    printf ' • PHP %-4s' "$version"
    [[ -n "$candidate" ]] && printf '  (CLI: %s)' "$candidate"
    [[ "$version" == "$default_version" ]] && printf '  [default CLI]'
    if service_exists "php${version}-fpm"; then
      if service_is_active "php${version}-fpm"; then
        printf '  [FPM: active]'
      else
        printf '  [FPM: installed/inactive]'
      fi
    fi
    printf '\n'
  done

  echo
  echo "Package backend: $(detect_package_manager)"
  echo "Service manager: $(detect_service_manager)"
  [[ -n "$default_path" ]] && echo -e "${YELLOW}Current default php:${NC} $default_path ${default_version:+(PHP $default_version)}"
}
''' + text[end:]

# FPM: root only for mutations; config/status/test are read-only.
start = text.index("phpx_fpm() {")
end = text.index("\n}\n\n# Apache command suite", start) + 2
text = text[:start] + r'''phpx_fpm() {
  local sub="${1:-status}"
  shift || true

  local version="${1:-}"
  if [[ -z "$version" ]]; then
    version="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;' 2>/dev/null || true)"
  else
    shift || true
  fi
  validate_php_version "$version"

  local svc="php${version}-fpm"
  case "$sub" in
  status)
    if ! service_exists "$svc"; then
      echo -e "${YELLOW}${svc}: not installed or not registered with the service manager${NC}"
      return 1
    fi
    if service_is_active "$svc"; then
      echo -e "${GREEN}${svc}: active${NC}"
    else
      echo -e "${YELLOW}${svc}: inactive${NC}"
    fi
    ;;
  config)
    echo -e "${GREEN}PHP-FPM config paths for ${version}:${NC}"
    echo "  main: /etc/php/${version}/fpm/php-fpm.conf"
    echo "  pools: /etc/php/${version}/fpm/pool.d/"
    echo "  php.ini: /etc/php/${version}/fpm/php.ini"
    ;;
  test)
    local bin="php-fpm${version}"
    if command -v "$bin" >/dev/null 2>&1; then
      "$bin" -t
    else
      echo -e "${YELLOW}php-fpm${version} binary is not available for a config test.${NC}"
      return 1
    fi
    ;;
  start | stop | restart | reload)
    require_root_for "phpx fpm $sub" || return 1
    service_exists "$svc" || { echo -e "${RED}Service not found: ${svc}${NC}"; return 1; }
    service_action "$sub" "$svc"
    ;;
  enable | disable)
    require_root_for "phpx fpm $sub" || return 1
    service_exists "$svc" || { echo -e "${RED}Service not found: ${svc}${NC}"; return 1; }
    service_enable_action "$sub" "$svc"
    ;;
  *)
    echo -e "${RED}Usage:${NC} phpx fpm {start|stop|restart|reload|status|enable|disable|test|config} [X.Y]"
    return 2
    ;;
  esac
}
''' + text[end:]

# Apache: status read-only, mutators root-gated, availability not tied to dpkg.
old = '''phpx_apache() {
  require_sudo

  local sub="${1:-status}"
'''
new = '''phpx_apache() {
  local sub="${1:-status}"
'''
replace_once(old, new)
replace_once(
'''  if ! dpkg -l | grep -q "^ii  apache2 "; then
    echo -e "${RED}Apache is not installed (package: apache2).${NC}"
    return 1
  fi

  case "$sub" in
''',
'''  if ! command -v apache2ctl >/dev/null 2>&1 && ! command -v apachectl >/dev/null 2>&1; then
    echo -e "${RED}Apache control binary is not installed.${NC}"
    return 1
  fi

  case "$sub" in
''')
replace_once(
'''  reload|restart)
    systemctl "$sub" apache2
    ;;
  fpm)
''',
'''  reload|restart)
    require_root_for "phpx apache $sub" || return 1
    service_action "$sub" apache2
    ;;
  fpm)
    require_root_for "phpx apache fpm" || return 1
''')
replace_once(
'''  modphp)
    if [[ -z "$version" ]]; then
''',
'''  modphp)
    require_root_for "phpx apache modphp" || return 1
    if [[ -z "$version" ]]; then
''')

# perform_system_checks: capability diagnostics only; never auto-install tooling.
start = text.index("perform_system_checks() {")
end = text.index("\n}\n\n################################################################################\n# Self-Update", start) + 2
text = text[:start] + r'''perform_system_checks() {
  local cmd="${1:-}"
  local mutation=0 need_network=0

  case "$cmd" in
  switch | s | install | i | remove | ext | extensions | x | sury | clean)
    mutation=1
    ;;
  self-update)
    need_network=1
    ;;
  esac

  if ((mutation)); then
    local free_space
    free_space="$(df -Pk / 2>/dev/null | awk 'NR==2 {print $4}')"
    if [[ "$free_space" =~ ^[0-9]+$ ]] && ((free_space < 50000)); then
      echo -e "${YELLOW}Warning: less than 50MB is free on /. Mutation may fail.${NC}" >&2
    fi
  fi

  if ((need_network)) && ! command -v curl >/dev/null 2>&1; then
    echo -e "${RED}$cmd requires curl.${NC}" >&2
    return 1
  fi

  log_action "INFO" "Capabilities: command=${cmd:-<none>} package=$(detect_package_manager) service=$(detect_service_manager)"
}
''' + text[end:]

# Library mode for permanent tests. It must occur before logging/main side effects.
needle = '''setup_logging
perform_system_checks "${1:-}"

case "$1" in
'''
replacement = '''if [[ "${PHPX_LIBRARY_MODE:-0}" == "1" ]]; then
  return 0 2>/dev/null || exit 0
fi

setup_logging
perform_system_checks "${1:-}" || exit $?

case "${1:-}" in
'''
replace_once(needle, replacement)

# Empty command and unknown commands should be explicit and nonzero.
replace_once(
'''*)
  display_usage
  ;;
esac
''',
'''"")
  display_usage
  exit 1
  ;;
*)
  echo -e "${RED}Unknown command: ${1:-}${NC}" >&2
  display_usage >&2
  exit 2
  ;;
esac
''')

path.write_text(text)
