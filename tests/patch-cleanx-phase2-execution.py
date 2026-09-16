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
'''info() { echo "$(color '1;34' '[INFO]') $*"; }
ok() { echo "$(color '1;32' '[ OK ]') $*"; }
warn() { echo "$(color '1;33' '[WARN]') $*"; }
err() { echo "$(color '1;31' '[ERR ]') $*" >&2; }
''',
'''info() {
  if ((JSON_REPORT)); then echo "$(color '1;34' '[INFO]') $*" >&2; else echo "$(color '1;34' '[INFO]') $*"; fi
}
ok() {
  if ((JSON_REPORT)); then echo "$(color '1;32' '[ OK ]') $*" >&2; else echo "$(color '1;32' '[ OK ]') $*"; fi
}
warn() { echo "$(color '1;33' '[WARN]') $*" >&2; }
err() { echo "$(color '1;31' '[ERR ]') $*" >&2; }
''')

replace_once(
'''run() {
  if ((DRY_RUN)); then
    echo "    [dry-run] $*"
  else
    low_impact_wrap bash -c "$*"
  fi
}
''',
'''print_cmd() {
  printf '    [dry-run]'
  printf ' %q' "$@"
  printf '\n'
}

run_cmd() {
  if ((DRY_RUN)); then
    print_cmd "$@"
  else
    low_impact_wrap "$@"
  fi
}

run_cmd_allow_fail() {
  if ((DRY_RUN)); then
    print_cmd "$@"
  else
    low_impact_wrap "$@" || true
  fi
}

run_cmd_quiet() {
  if ((DRY_RUN)); then
    print_cmd "$@"
  else
    low_impact_wrap "$@" >/dev/null 2>&1 || true
  fi
}
''')

start = text.index("# Build find prune expression from EXCLUDE_GLOBS")
end = text.index("# Quota accounting", start)
new_find = r'''# Build find expressions as argv; never serialize them into shell code.
append_exclude_prune() {
  local -n dest="$1"
  local first=1 glob
  ((${#EXCLUDE_GLOBS[@]})) || return 0

  dest+=("(")
  for glob in "${EXCLUDE_GLOBS[@]}"; do
    if ((first)); then first=0; else dest+=(-o); fi
    dest+=(-path "$glob")
  done
  dest+=(")" -prune -o)
}

append_include_names() {
  local -n dest="$1"
  local first=1 glob
  ((${#INCLUDE_GLOBS[@]})) || return 0

  dest+=("(")
  for glob in "${INCLUDE_GLOBS[@]}"; do
    if ((first)); then first=0; else dest+=(-o); fi
    dest+=(-name "$glob")
  done
  dest+=(")")
}

validate_delete_tree_root() {
  local root="$1"
  [[ -n "$root" && "$root" == /* ]] || die "Refusing non-absolute delete root: $root"
  case "$root" in
  / | /bin | /boot | /dev | /etc | /home | /lib | /lib64 | /opt | /proc | /root | /run | /sbin | /srv | /sys | /tmp | /usr | /var)
    die "Refusing unsafe delete root: $root"
    ;;
  esac
}

secure_delete_files() {
  local root="$1"
  shift || true
  local -a args=("$root")
  append_exclude_prune args
  args+=(-type f "$@")

  if ((SECURE_ERASE)); then
    args+=(-exec shred -zuf -- '{}' '+')
  else
    args+=(-exec rm -f -- '{}' '+')
  fi
  run_cmd find "${args[@]}"
}

secure_delete_tree() {
  local root="$1"
  [[ -e "$root" || -L "$root" ]] || return 0
  validate_delete_tree_root "$root"

  if ((${#EXCLUDE_GLOBS[@]})); then
    # A recursive rm would bypass nested exclusions. Delete only unexcluded
    # files/symlinks and leave the directory skeleton when exclusions exist.
    secure_delete_files "$root"
    local -a links=("$root")
    append_exclude_prune links
    links+=(-type l -exec rm -f -- '{}' '+')
    run_cmd find "${links[@]}"
    return 0
  fi

  if ((SECURE_ERASE)); then
    local -a files=("$root" -type f -exec shred -zuf -- '{}' '+')
    run_cmd find "${files[@]}"
  fi
  run_cmd rm -rf -- "$root"
}

'''
text = text[:start] + new_find + text[end:]

start = text.index("# ---------- Tasks ----------")
end = text.index("# ---------- Declarative config / target identity ----------", start)
new_tasks = r'''# ---------- Tasks ----------
detect_package_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    printf 'apt'
  elif command -v dnf >/dev/null 2>&1; then
    printf 'dnf'
  elif command -v zypper >/dev/null 2>&1; then
    printf 'zypper'
  elif command -v pacman >/dev/null 2>&1; then
    printf 'pacman'
  else
    printf 'none'
  fi
}

task_apt() {
  local pm
  pm="$(detect_package_manager)"
  info "Package cleanup backend: $pm"
  case "$pm" in
  apt)
    run_cmd apt-get autoremove --purge -y
    run_cmd apt-get clean
    ;;
  dnf)
    run_cmd dnf autoremove -y
    run_cmd dnf clean all
    ;;
  zypper)
    run_cmd zypper --non-interactive clean --all
    warn "zypper autoremove is not applied automatically; only cache cleanup is performed."
    ;;
  pacman)
    warn "pacman cleanup is skipped: cleanx does not remove pacman cache/packages without an explicit distro policy."
    ;;
  none)
    warn "No supported package manager found; package cleanup skipped."
    ;;
  esac
}

task_apt_residuals() {
  if [[ "$(detect_package_manager)" != "apt" ]] || ! command -v dpkg >/dev/null 2>&1; then
    warn "Residual-package purge is apt/dpkg-specific; skipped on this system."
    return 0
  fi
  info "APT residual configs (rc packages): purge"
  if ((DRY_RUN)); then
    dpkg -l | awk '/^rc/{print "    [would] apt-get purge -y "$2}'
  else
    dpkg -l | awk '/^rc/{print $2}' | xargs -r -L100 apt-get purge -y
  fi
}

task_journal() {
  info "Systemd journal vacuum -> keep: ${JOURNAL_KEEP}"
  command -v journalctl >/dev/null 2>&1 || {
    warn "journalctl not present; journal cleanup skipped."
    return 0
  }
  run_cmd journalctl --rotate
  run_cmd journalctl --disk-usage
  if [[ "$JOURNAL_KEEP" =~ ^[0-9]+[smhdw]$ ]]; then
    run_cmd journalctl "--vacuum-time=${JOURNAL_KEEP}"
  else
    run_cmd journalctl "--vacuum-size=${JOURNAL_KEEP}"
  fi
}

task_logs() {
  info "Logs: delete rotated older than 14d, truncate *.log > ${LOG_MAX_SIZE}"
  secure_delete_files /var/log -name '*.gz' -a -mtime +14

  local -a args=(/var/log)
  append_exclude_prune args
  args+=(-type f)
  if ((${#INCLUDE_GLOBS[@]})); then
    append_include_names args
  else
    args+=(-name '*.log')
  fi
  args+=(-size "+${LOG_MAX_SIZE}" -exec truncate -s 0 -- '{}' '+')
  run_cmd find "${args[@]}"
}

task_tmp() {
  info "/tmp: delete files/links older than ${TMP_DAYS}d and then empty directories"
  local -a files=(/tmp)
  append_exclude_prune files
  files+=(-mindepth 1 -type f -mtime "+${TMP_DAYS}" -exec rm -f -- '{}' '+')
  run_cmd find "${files[@]}"

  local -a links=(/tmp)
  append_exclude_prune links
  links+=(-mindepth 1 -type l -mtime "+${TMP_DAYS}" -exec rm -f -- '{}' '+')
  run_cmd find "${links[@]}"

  local -a dirs=(/tmp)
  append_exclude_prune dirs
  dirs+=(-mindepth 1 -type d -empty -mtime "+${TMP_DAYS}" -exec rmdir -- '{}' '+')
  run_cmd find "${dirs[@]}"
}

task_tmpfiles() {
  info "systemd-tmpfiles: clean according to policy"
  command -v systemd-tmpfiles >/dev/null 2>&1 || {
    warn "systemd-tmpfiles not present"
    return 0
  }
  run_cmd systemd-tmpfiles --clean
}

task_usercache() {
  info "User caches & trash for $TARGET_USER ($TARGET_HOME)"
  if [[ -d "$TARGET_HOME/.cache" ]]; then
    secure_delete_files "$TARGET_HOME/.cache"
    local -a empty_dirs=("$TARGET_HOME/.cache")
    append_exclude_prune empty_dirs
    empty_dirs+=(-type d -empty -exec rmdir -- '{}' '+')
    run_cmd find "${empty_dirs[@]}"
  fi
  secure_delete_tree "$TARGET_HOME/.thumbnails"
  secure_delete_tree "$TARGET_HOME/.cache/thumbnails"
  secure_delete_tree "$TARGET_HOME/.local/share/Trash/files"
  secure_delete_tree "$TARGET_HOME/.local/share/Trash/info"
}

run_user_cache_tool() {
  local tool="$1"
  shift
  local user_path="$TARGET_HOME/.local/bin:$TARGET_HOME/.composer/vendor/bin:/usr/local/bin:/usr/bin:/bin"

  if ! PATH="$user_path" command -v "$tool" >/dev/null 2>&1; then
    return 0
  fi
  if ! command -v runuser >/dev/null 2>&1; then
    warn "runuser not available; skipping $tool cache cleanup for $TARGET_USER."
    return 0
  fi

  if ((DRY_RUN)); then
    print_cmd runuser -u "$TARGET_USER" -- env "HOME=$TARGET_HOME" "PATH=$user_path" "$tool" "$@"
  else
    runuser -u "$TARGET_USER" -- env "HOME=$TARGET_HOME" "PATH=$user_path" "$tool" "$@" ||
      warn "$tool cache cleanup failed for $TARGET_USER."
  fi
}

task_langcaches() {
  info "Language/tool caches (Composer/npm/pnpm/yarn/pip) for $TARGET_USER"
  run_user_cache_tool composer clear-cache
  run_user_cache_tool npm cache clean --force
  run_user_cache_tool pnpm store prune
  run_user_cache_tool yarn cache clean
  run_user_cache_tool pip cache purge
}

task_snap() {
  info "Snap: retain ${SNAP_RETAIN} revisions, remove disabled & saved snapshots"
  command -v snap >/dev/null || {
    warn "snap not installed"
    return 0
  }
  run_cmd snap set system "refresh.retain=${SNAP_RETAIN}"
  if ((DRY_RUN)); then
    snap list --all | awk '/disabled/{print "    [would] snap remove "$1" --revision="$3}'
  else
    snap list --all | awk '/disabled/{print $1" --revision="$3}' | xargs -r -L1 snap remove
  fi
  if ((DRY_RUN)); then
    snap saved | awk 'NR>1{print "    [would] snap forget "$1}'
  else
    snap saved | awk 'NR>1{print $1}' | xargs -r -L1 snap forget
  fi
}

task_flatpak() {
  info "Flatpak: remove unused & delete-data"
  command -v flatpak >/dev/null || {
    warn "flatpak not installed"
    return 0
  }
  run_cmd flatpak uninstall --unused -y
  run_cmd flatpak remove --delete-data -y --unused
}

task_docker() {
  info "Docker: prune all unused (images/containers/networks/build cache)"
  command -v docker >/dev/null || {
    warn "docker not installed"
    return 0
  }
  run_cmd_allow_fail docker system df
  if ((AGGRESSIVE)); then
    run_cmd docker system prune -af --volumes
  else
    run_cmd docker system prune -af
  fi
}

task_podman() {
  info "Podman: prune unused"
  command -v podman >/dev/null || {
    warn "podman not installed"
    return 0
  }
  run_cmd podman system prune -af
  ((AGGRESSIVE)) && run_cmd podman volume prune -f
}

task_containerd() {
  info "containerd: remove untagged images with ctr"
  command -v ctr >/dev/null || {
    warn "ctr not installed"
    return 0
  }
  if ((DRY_RUN)); then
    ctr -n default images ls | awk '/\<none\>/{print "    [would] ctr -n default images rm "$1}'
  else
    ctr -n default images ls | awk '/\<none\>/{print $1}' | xargs -r -L50 ctr -n default images rm
  fi
}

task_kernels() {
  if [[ "$(detect_package_manager)" != "apt" ]]; then
    warn "Old-kernel autoremove is currently supported only for apt; skipped."
    return 0
  fi
  info "Old kernels: apt autoremove"
  run_cmd apt-get autoremove --purge -y
}

task_coredumps() {
  info "Core/crash dumps: delete core* > 50M and /var/crash contents"
  local -a cores=(/ -xdev)
  append_exclude_prune cores
  cores+=(-type f -name 'core*' -size +50M)
  if ((SECURE_ERASE)); then
    cores+=(-exec shred -zuf -- '{}' '+')
  else
    cores+=(-exec rm -f -- '{}' '+')
  fi
  if ((DRY_RUN)); then
    print_cmd find "${cores[@]}"
  else
    low_impact_wrap find "${cores[@]}" 2>/dev/null || true
  fi

  if [[ -d /var/crash ]]; then
    while IFS= read -r -d '' entry; do
      secure_delete_tree "$entry"
    done < <(find /var/crash -mindepth 1 -maxdepth 1 -print0 2>/dev/null)
  fi
}

task_buildcache() {
  info "Build caches: ccache (if present)"
  command -v ccache >/dev/null 2>&1 || {
    warn "ccache not installed"
    return 0
  }
  run_cmd_quiet ccache --zero-stats
  run_cmd_quiet ccache --clear
}

task_browsers() {
  info "Browser caches for $TARGET_USER (Chromium/Chrome/Firefox)"
  local uhome="$TARGET_HOME" d
  for d in "$uhome/.cache/chromium" "$uhome/.cache/google-chrome" \
    "$uhome/.config/chromium/Default/Service Worker/CacheStorage" \
    "$uhome/.config/google-chrome/Default/Service Worker/CacheStorage"; do
    [[ -d "$d" ]] && secure_delete_tree "$d"
  done
  [[ -d "$uhome/.cache/mozilla/firefox" ]] && secure_delete_tree "$uhome/.cache/mozilla/firefox"
  if [[ -d "$uhome/.mozilla/firefox" ]]; then
    while IFS= read -r -d '' p; do
      secure_delete_tree "$p/cache2"
      secure_delete_tree "$p/storage/default"
    done < <(find "$uhome/.mozilla/firefox" -maxdepth 1 -type d -name '*.default*' -print0)
  fi
}

task_timeshift() {
  info "Timeshift: prune old snapshots (keep last 3 of each type)"
  command -v timeshift >/dev/null || {
    warn "timeshift not installed"
    return 0
  }
  local types=(hourly daily weekly monthly) t s
  local -a snaps=()
  for t in "${types[@]}"; do
    mapfile -t snaps < <(timeshift --list | awk -v T="$t" '$0 ~ T {print $NF}' | sort -r)
    if ((${#snaps[@]} > 3)); then
      for s in "${snaps[@]:3}"; do
        run_cmd timeshift --delete --snapshot "$s"
      done
    fi
  done
}

task_pkgbig() {
  info "Top 30 installed packages by size"
  if command -v dpkg-query >/dev/null 2>&1; then
    dpkg-query -Wf='${Installed-Size}\t${Package}\n' | sort -nr | head -30 |
      awk '{printf "%8.1f MB  %s\n", $1/1024, $2}'
  elif command -v rpm >/dev/null 2>&1; then
    rpm -qa --qf '%{SIZE}\t%{NAME}\n' | sort -nr | head -30 |
      awk '{printf "%8.1f MB  %s\n", $1/1048576, $2}'
  else
    warn "Neither dpkg-query nor rpm is available; package-size report skipped."
  fi
}

task_inode_scan() { inode_scan "$INODE_PATH" "$INODE_DEPTH" "$INODE_TOP"; }

task_fshints() {
  info "Filesystem hints (Btrfs/ZFS)"
  if command -v btrfs >/dev/null 2>&1; then
    echo "== Btrfs detected (READ-ONLY suggestions) =="
    echo "  btrfs filesystem df /"
    echo "  btrfs filesystem usage /"
    echo "  sudo btrfs balance start -dusage=75 -musage=75 /"
    echo "  sudo btrfs subvolume list / | grep snapshot"
    echo
  fi
  if command -v zfs >/dev/null 2>&1; then
    echo "== ZFS detected (READ-ONLY suggestions) =="
    echo "  zpool list; zpool status"
    echo "  zfs list -o space"
    echo "  sudo zpool trim <pool>; sudo zpool scrub <pool>"
    echo "  # Prune example: zfs destroy pool/dataset@old-snap"
    echo
  fi
}

task_all() {
  task_apt
  task_apt_residuals
  task_journal
  task_logs
  task_tmp
  task_tmpfiles
  task_usercache
  task_langcaches
  task_snap
  task_flatpak
  task_docker
  task_podman
  task_containerd
  task_kernels
  task_coredumps
  task_buildcache
  task_browsers
  task_timeshift
  task_fshints
}

'''
text = text[:start] + new_tasks + text[end:]

replace_once(
'''  local entry _pw _uid _gid _gecos home _shell
''',
'''  local entry _name _pw _uid _gid _gecos home _shell
''')
replace_once(
'''  IFS=: read -r _pw _pw _uid _gid _gecos home _shell <<<"$entry"
''',
'''  IFS=: read -r _name _pw _uid _gid _gecos home _shell <<<"$entry"
''')

replace_once(
'''  local req=(find du sort awk xargs df)
  local opt=(journalctl apt dpkg snap flatpak docker podman ctr lsof numfmt ccache timeshift btrfs zfs curl sha256sum shasum)
''',
'''  local req=(find du sort awk xargs df getent id)
  local opt=(flock runuser journalctl apt-get dnf zypper pacman dpkg snap flatpak docker podman ctr lsof numfmt ccache timeshift btrfs zfs curl sha256sum shasum)
''')
replace_once(
'''  df -hT -x squashfs -x tmpfs -x devtmpfs | sed 's/^/FS: /'
  ((missing)) && return 1 || return 0
''',
'''  echo "PKG: $(detect_package_manager)"
  df -hT -x squashfs -x tmpfs -x devtmpfs | sed 's/^/FS: /'
  ((missing)) && return 1 || return 0
''')

replace_once(
'''  '--force[ignore 98% rootfs guard]' \\
''',
'''  '--force[suppress >=98% rootfs warning]' \\
''')

insert_marker = '''# ---------- CLI parsing ----------
'''
json_helpers = r'''# ---------- JSON output ----------
json_quote() {
  local value="${1-}"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  printf '"%s"' "$value"
}

json_bool() {
  if (("$1")); then printf 'true'; else printf 'false'; fi
}

json_array() {
  local first=1 item
  printf '['
  for item in "$@"; do
    if ((first)); then first=0; else printf ','; fi
    json_quote "$item"
  done
  printf ']'
}

emit_json_report() {
  local ts mode
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  if ((DRY_RUN)); then mode="dry-run"; else mode="apply"; fi

  printf '{\n'
  printf '  "tool": '; json_quote "$TOOL_NAME"; printf ',\n'
  printf '  "version": '; json_quote "$VERSION"; printf ',\n'
  printf '  "channel": '; json_quote "$CHANNEL"; printf ',\n'
  printf '  "timestamp": '; json_quote "$ts"; printf ',\n'
  printf '  "mode": '; json_quote "$mode"; printf ',\n'
  printf '  "aggressive": '; json_bool "$AGGRESSIVE"; printf ',\n'
  printf '  "low_impact": '; json_bool "$LOW_IMPACT"; printf ',\n'
  printf '  "secure_erase": '; json_bool "$SECURE_ERASE"; printf ',\n'
  printf '  "user": '; json_quote "$TARGET_USER"; printf ',\n'
  printf '  "quota_bytes": %s,\n' "$QUOTA_BYTES"
  printf '  "quota_reached": '; json_bool "$QUOTA_REACHED"; printf ',\n'
  printf '  "before_used_bytes": %s,\n' "$BEFORE"
  printf '  "after_used_bytes": %s,\n' "$AFTER"
  printf '  "reclaimed_bytes": %s,\n' "$RECLAIMED"
  printf '  "tasks": '; json_array "${REQUESTED_TASKS[@]}"; printf ',\n'
  printf '  "excludes": '; json_array "${EXCLUDE_GLOBS[@]}"; printf ',\n'
  printf '  "includes": '; json_array "${INCLUDE_GLOBS[@]}"; printf '\n'
  printf '}\n'
}

validate_tasks() {
  local task
  for task in "$@"; do
    case "$task" in
    report | apt | packages | apt-residuals | journal | logs | tmp | tmpfiles | usercache | langcaches | snap | flatpak | docker | podman | containerd | kernels | coredumps | buildcache | browsers | timeshift | pkgbig | inode-scan | fshints | all) ;;
    *) die "Unknown task: $task" ;;
    esac
  done
}

'''
if insert_marker not in text:
    raise SystemExit("CLI marker missing")
text = text.replace(insert_marker, json_helpers + insert_marker, 1)

replace_once(
'''Tasks:
  report apt apt-residuals journal logs tmp tmpfiles usercache langcaches snap flatpak
''',
'''Tasks:
  report packages apt apt-residuals journal logs tmp tmpfiles usercache langcaches snap flatpak
''')
replace_once(
'''  --json                    print a JSON summary at the end
''',
'''  --json                    emit only JSON on stdout; operational output goes to stderr
''')

replace_once(
'''TASKS=()
# Resolve only the explicit config path early. All normal CLI options are parsed
# after config loading so command-line values always win over config files.
for arg in "$@"; do
  case "$arg" in
  --config=*) CONFIG_OVERRIDE_FILE="${arg#*=}" ;;
  esac
done
''',
'''TASKS=()
REQUESTED_TASKS=()
# Resolve the explicit config path and JSON routing early. All normal CLI options
# are parsed after config loading so command-line values always win over config files.
for arg in "$@"; do
  case "$arg" in
  --config=*) CONFIG_OVERRIDE_FILE="${arg#*=}" ;;
  --json) JSON_REPORT=1 ;;
  esac
done
''')

# Allow the test harness to source helpers without executing CLI parsing/main.
needle = '''TASKS=()
REQUESTED_TASKS=()
'''
text = text.replace(
    needle,
    '''if [[ "${CLEANX_LIBRARY_MODE:-0}" == "1" ]]; then\n  return 0 2>/dev/null || exit 0\nfi\n\n''' + needle,
    1,
)

main_start = text.index("# ---------- Main ----------")
text = text[:main_start] + r'''# ---------- Main ----------
main() {
  [[ ${#TASKS[@]} -eq 0 ]] && {
    usage
    exit 1
  }

  validate_tasks "${TASKS[@]}"
  REQUESTED_TASKS=("${TASKS[@]}")

  if ((JSON_REPORT)); then
    exec 3>&1
    exec 1>&2
  fi

  need find
  need du
  need sort
  need awk
  need xargs
  need df
  command -v numfmt >/dev/null || true

  info "Mode: $( ((DRY_RUN)) && echo 'dry-run' || echo 'apply') | aggressive: $AGGRESSIVE | low-impact: $LOW_IMPACT | secure-erase: $SECURE_ERASE | user: $TARGET_USER | channel: $CHANNEL"
  ((QUOTA_BYTES > 0)) && info "Quota target: $(human "$QUOTA_BYTES")"
  ((${#EXCLUDE_GLOBS[@]})) && info "Excludes: ${EXCLUDE_GLOBS[*]}"
  ((${#INCLUDE_GLOBS[@]})) && info "Includes: ${INCLUDE_GLOBS[*]}"
  info "Selected tasks: ${TASKS[*]}"
  echo

  # Report first and do not take the mutation lock for report-only runs.
  if printf '%s\n' "${TASKS[@]}" | grep -qx 'report'; then
    report
    local -a remaining=()
    local t
    for t in "${TASKS[@]}"; do [[ "$t" != "report" ]] && remaining+=("$t"); done
    TASKS=("${remaining[@]}")
  fi

  if ((${#TASKS[@]})); then
    asroot
    preflight
    take_lock
    info "About to execute system changes."
    confirm || die "Cancelled by user."
  fi

  BEFORE=$(root_used_bytes)
  QUOTA_START_USED="$BEFORE"
  QUOTA_REACHED=0

  local t
  for t in "${TASKS[@]}"; do
    case "$t" in
    apt | packages) task_apt ;;
    apt-residuals) task_apt_residuals ;;
    journal) task_journal ;;
    logs) task_logs ;;
    tmp) task_tmp ;;
    tmpfiles) task_tmpfiles ;;
    usercache) task_usercache ;;
    langcaches) task_langcaches ;;
    snap) task_snap ;;
    flatpak) task_flatpak ;;
    docker) task_docker ;;
    podman) task_podman ;;
    containerd) task_containerd ;;
    kernels) task_kernels ;;
    coredumps) task_coredumps ;;
    buildcache) task_buildcache ;;
    browsers) task_browsers ;;
    timeshift) task_timeshift ;;
    pkgbig) task_pkgbig ;;
    inode-scan) task_inode_scan ;;
    fshints) task_fshints ;;
    all) task_all ;;
    esac
    ok "Task '$t' done."
    echo
    if ! maybe_stop_for_quota; then break; fi
  done

  AFTER=$(root_used_bytes)
  RECLAIMED=$((BEFORE - AFTER))
  if ((DRY_RUN)); then
    info "Estimated reclaimable: $(human "${RECLAIMED#-}") (dry-run)"
  else
    info "Freed: $(human "${RECLAIMED#-}")"
  fi
  ok "Completed."

  if ((JSON_REPORT)); then
    emit_json_report >&3
    exec 3>&-
  fi
}

main
'''

path.write_text(text)
