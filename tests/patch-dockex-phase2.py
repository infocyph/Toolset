#!/usr/bin/env python3
from pathlib import Path
import re

path = Path('Docker/dockex')
text = path.read_text()


def replace_section(start: str, end: str, body: str) -> None:
    global text
    pattern = re.escape(start) + r'.*?' + re.escape(end)
    repl = start + '\n' + body.rstrip() + '\n\n' + end
    text2, count = re.subn(pattern, repl, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'failed replacing {start!r}')
    text = text2


replace_section(
    '# ------------------ container helpers ------------------- #',
    '# Display container information',
    r'''docker_context_name() {
  docker context show 2>/dev/null || printf 'default'
}

docker_is_rootless() {
  docker info --format '{{json .SecurityOptions}}' 2>/dev/null | grep -q 'name=rootless'
}

ensure_docker_ready() {
  local context
  context="$(docker_context_name)"
  if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker daemon/context '$context' is not reachable." >&2
    echo "Check 'docker context show', daemon availability, and socket permissions." >&2
    return 1
  fi
}

run_bounded() {
  local seconds="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout --signal=TERM --kill-after=5 "${seconds}s" "$@"
  else
    "$@"
  fi
}

validate_positive_int() {
  [[ "${1:-}" =~ ^[1-9][0-9]*$ ]]
}

validate_memory_limit() {
  [[ "${1:-}" == 0 || "${1:-}" =~ ^[1-9][0-9]*([bBkKmMgG])?$ ]]
}

validate_container() {
  local container_name="${1:-}" requirement="${2:-any}"
  [[ -n "$container_name" ]] || { echo 'Error: container name is required.' >&2; return 1; }
  if ! docker container inspect "$container_name" >/dev/null 2>&1; then
    echo "Error: Container '$container_name' does not exist." >&2
    return 1
  fi
  if [[ "$requirement" == running ]] && [[ "$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null)" != true ]]; then
    echo "Error: Container '$container_name' is not running." >&2
    return 1
  fi
}

is_container_running() {
  local container_name="$1"
  [[ "$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null || true)" == true ]]
}

mount_exists() {
  local container_name="$1" destination="$2"
  docker inspect "$container_name" | jq -e --arg dest "$destination" '.[0].Mounts | any(.Destination == $dest)' >/dev/null
}

choose_mount_destination() {
  local container_name="$1" requested="${2:-}" destinations=()
  if [[ -n "$requested" ]]; then
    mount_exists "$container_name" "$requested" || { echo "Error: '$requested' is not a mount destination on '$container_name'." >&2; return 1; }
    printf '%s' "$requested"
    return 0
  fi
  mapfile -t destinations < <(docker inspect "$container_name" | jq -r '.[0].Mounts[]?.Destination')
  ((${#destinations[@]})) || { echo "Error: container '$container_name' has no mounts." >&2; return 1; }
  if ((${#destinations[@]} == 1)); then printf '%s' "${destinations[0]}"; return 0; fi
  [[ -t 0 ]] || { echo 'Error: multiple mounts exist; specify --mount=/container/path.' >&2; return 2; }
  local i choice
  echo 'Mounted destinations:' >&2
  for i in "${!destinations[@]}"; do printf '%d) %s\n' "$((i+1))" "${destinations[$i]}" >&2; done
  read -r -p 'Select a mount: ' choice
  validate_positive_int "$choice" && ((choice <= ${#destinations[@]})) || return 2
  printf '%s' "${destinations[$((choice-1))]}"
}''')

# info supports opt-in secret display; default is key-only/redacted.
text = text.replace('view_container_info() {\n  local container_name=$1\n', 'view_container_info() {\n  local container_name=$1\n  local show_env_values="${2:-0}"\n', 1)
text = text.replace(
    "  container_env=$(echo \"$inspect\" | jq -r '.[0].Config.Env[]?' 2>/dev/null || true)\n",
    "  if [[ \"$show_env_values\" == 1 ]]; then\n    container_env=$(echo \"$inspect\" | jq -r '.[0].Config.Env[]?' 2>/dev/null || true)\n  else\n    container_env=$(echo \"$inspect\" | jq -r '.[0].Config.Env[]? | (split(\"=\")[0] + \"=<redacted>\")' 2>/dev/null || true)\n  fi\n",
    1,
)

replace_section(
    '# Update container resources (CPU and memory limits)',
    '# Backup container volume data and zip it',
    r'''update_container_resources() {
  local container_name=$1
  validate_container "$container_name" any || return 1

  local current_cpu_shares current_mem_raw current_memory_limit
  current_cpu_shares=$(docker inspect -f '{{.HostConfig.CpuShares}}' "$container_name")
  current_mem_raw=$(docker inspect -f '{{.HostConfig.Memory}}' "$container_name")
  if [[ "$current_mem_raw" =~ ^[0-9]+$ ]] && ((current_mem_raw == 0)); then current_memory_limit='Unlimited'; else current_memory_limit="$(awk "BEGIN {print $current_mem_raw/1024/1024}") MB"; fi
  echo "Current CPU shares: $current_cpu_shares"
  echo "Current memory limit: $current_memory_limit"

  local cpu_input="${2:-}" memory_limit="${3:-}"
  if [[ -z "$cpu_input" && -z "$memory_limit" ]]; then
    [[ -t 0 ]] || { echo 'Error: non-interactive use requires CPU and/or memory values.' >&2; return 2; }
    read -r -p 'New CPU shares (empty keeps current): ' cpu_input
    read -r -p 'New memory limit (e.g. 512m, 1g, 0=unlimited; empty keeps current): ' memory_limit
  fi

  local cpu_flag=() mem_flag=() shares pct cores
  if [[ -n "$cpu_input" ]]; then
    if [[ "$cpu_input" =~ ^([0-9]+)%$ ]]; then
      pct="${BASH_REMATCH[1]}"; ((pct >= 1 && pct <= 1000)) || { echo 'Invalid CPU percentage.' >&2; return 2; }
      shares=$((1024 * pct / 100)); ((shares < 2)) && shares=2
    elif [[ "$cpu_input" =~ ^([1-9][0-9]*)c$ ]]; then
      cores="${BASH_REMATCH[1]}"; shares=$((cores * 1024))
    elif validate_positive_int "$cpu_input"; then
      shares="$cpu_input"
    else
      echo "Invalid CPU shares: $cpu_input" >&2; return 2
    fi
    ((shares >= 2 && shares <= 262144)) || { echo 'CPU shares must be between 2 and 262144.' >&2; return 2; }
    cpu_flag=(--cpu-shares "$shares")
  fi
  if [[ -n "$memory_limit" ]]; then
    validate_memory_limit "$memory_limit" || { echo "Invalid memory limit: $memory_limit" >&2; return 2; }
    mem_flag=(--memory "$memory_limit")
  fi
  ((${#cpu_flag[@]} || ${#mem_flag[@]})) || { echo 'Nothing to update.'; return 0; }
  docker update "${cpu_flag[@]}" "${mem_flag[@]}" "$container_name"
}''')

replace_section(
    '# Backup container volume data and zip it',
    '# ---------------- docker listings ----------------- #',
    r'''backup_container_data() {
  local container_name=$1; shift || true
  validate_container "$container_name" any || return 1
  local mount="" consistency="" helper="${DOCKEX_HELPER_IMAGE:-alpine:3.22}"
  while (($#)); do
    case "$1" in
    --mount=*) mount="${1#*=}" ;;
    --mount) shift; mount="${1:-}" ;;
    --live) consistency=live ;;
    --stop) consistency=stop ;;
    *) echo "Error: unknown backup option '$1'." >&2; return 2 ;;
    esac
    shift
  done
  mount="$(choose_mount_destination "$container_name" "$mount")" || return $?

  local was_running=0
  is_container_running "$container_name" && was_running=1
  if ((was_running)) && [[ -z "$consistency" ]]; then
    echo 'Error: live container backups may be application-inconsistent.' >&2
    echo 'Use --stop for a quiesced backup or --live to explicitly accept that risk.' >&2
    return 2
  fi
  if ((was_running)) && [[ "$consistency" == stop ]]; then docker stop "$container_name" >/dev/null || return 1; fi

  docker image inspect "$helper" >/dev/null 2>&1 || { echo "Error: helper image '$helper' is not local; pull it explicitly first." >&2; ((was_running)) && [[ "$consistency" == stop ]] && docker start "$container_name" >/dev/null || true; return 1; }
  local safe_mount archive output_dir restart_rc=0
  safe_mount="${mount#/}"; safe_mount="${safe_mount//\//_}"; safe_mount="${safe_mount//[^A-Za-z0-9_.-]/_}"
  archive="${container_name}-${safe_mount:-root}-$(date +%Y%m%d_%H%M%S).tar.gz"
  output_dir="$PWD"
  if ! docker run --rm --volumes-from "$container_name":ro -v "$output_dir:/backup" "$helper" \
      sh -c 'cd "$1" && tar -czf "/backup/$2" .' _ "$mount" "$archive"; then
    restart_rc=1
  fi
  if ((was_running)) && [[ "$consistency" == stop ]]; then docker start "$container_name" >/dev/null || restart_rc=1; fi
  ((restart_rc == 0)) || return 1
  printf 'container=%s\nmount=%s\nmode=%s\n' "$container_name" "$mount" "${consistency:-stopped}" >"${archive}.meta"
  echo "Backup completed: $output_dir/$archive"
}

restore_container_data() {
  local container_name=$1 backup_file=$2; shift 2 || true
  validate_container "$container_name" any || return 1
  [[ -f "$backup_file" ]] || { echo "Error: backup file '$backup_file' not found." >&2; return 1; }
  local mount="" consistency="" helper="${DOCKEX_HELPER_IMAGE:-alpine:3.22}"
  while (($#)); do
    case "$1" in
    --mount=*) mount="${1#*=}" ;;
    --mount) shift; mount="${1:-}" ;;
    --live) consistency=live ;;
    --stop) consistency=stop ;;
    *) echo "Error: unknown restore option '$1'." >&2; return 2 ;;
    esac
    shift
  done
  mount="$(choose_mount_destination "$container_name" "$mount")" || return $?
  command -v tar >/dev/null 2>&1 || { echo 'Error: host tar is required to validate archives.' >&2; return 1; }
  if ! tar -tzf "$backup_file" | awk 'BEGIN{bad=0} /^\// || /(^|\/)\.\.($|\/)/ {bad=1} END{exit bad}'; then
    echo 'Error: archive contains absolute or parent-traversal paths.' >&2; return 1
  fi

  local was_running=0
  is_container_running "$container_name" && was_running=1
  if ((was_running)) && [[ -z "$consistency" ]]; then
    echo 'Error: restoring into a running container is unsafe.' >&2
    echo 'Use --stop to quiesce it or --live to explicitly accept the risk.' >&2
    return 2
  fi
  if ((was_running)) && [[ "$consistency" == stop ]]; then docker stop "$container_name" >/dev/null || return 1; fi
  docker image inspect "$helper" >/dev/null 2>&1 || { echo "Error: helper image '$helper' is not local; pull it explicitly first." >&2; ((was_running)) && [[ "$consistency" == stop ]] && docker start "$container_name" >/dev/null || true; return 1; }

  local archive_dir archive_base rc=0
  archive_dir="$(cd -- "$(dirname -- "$backup_file")" && pwd)"; archive_base="$(basename -- "$backup_file")"
  docker run --rm --volumes-from "$container_name" -v "$archive_dir:/backup:ro" "$helper" \
    sh -c 'mkdir -p "$1" && tar -xzf "/backup/$2" -C "$1"' _ "$mount" "$archive_base" || rc=1
  if ((was_running)) && [[ "$consistency" == stop ]]; then docker start "$container_name" >/dev/null || rc=1; fi
  ((rc == 0)) || return 1
  echo "Restore completed into container mount: $mount"
}''')

replace_section(
    '# --------------- create container ----------------- #',
    '# ---------------- benchmark ------------------------ #',
    r'''create_new_container() {
  local image_name=$1 container_name=${2:-}
  [[ -n "$container_name" ]] || { [[ -t 0 ]] || { echo 'Error: container name required in non-interactive mode.' >&2; return 2; }; read -r -p 'Container name: ' container_name; }
  [[ "$container_name" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || { echo 'Error: invalid container name.' >&2; return 2; }
  docker image inspect "$image_name" >/dev/null 2>&1 || { echo "Error: image '$image_name' is not local; pull it explicitly first." >&2; return 1; }

  local port_mappings="" env_vars="" volume_mappings="" network_name="" answer
  read -r -p 'Map ports? (y/N): ' answer; [[ "$answer" =~ ^[yY]$ ]] && read -r -p 'host:container mappings (comma-separated): ' port_mappings || true
  read -r -p 'Add environment variables? (y/N): ' answer; [[ "$answer" =~ ^[yY]$ ]] && read -r -p 'KEY=value entries (comma-separated): ' env_vars || true
  read -r -p 'Mount volumes? (y/N): ' answer; [[ "$answer" =~ ^[yY]$ ]] && read -r -p 'source:destination mappings (comma-separated): ' volume_mappings || true
  read -r -p 'Use a specific network? (y/N): ' answer; [[ "$answer" =~ ^[yY]$ ]] && read -r -p 'Network name: ' network_name || true

  local cmd=(docker run -d --name "$container_name") item
  local -a values=()
  if [[ -n "$port_mappings" ]]; then IFS=',' read -r -a values <<<"$port_mappings"; for item in "${values[@]}"; do [[ "$item" =~ ^[0-9]+:[0-9]+(/(tcp|udp))?$ ]] || { echo "Invalid port mapping: $item" >&2; return 2; }; cmd+=(-p "$item"); done; fi
  if [[ -n "$env_vars" ]]; then IFS=',' read -r -a values <<<"$env_vars"; for item in "${values[@]}"; do [[ "$item" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || { echo 'Invalid environment assignment.' >&2; return 2; }; cmd+=(-e "$item"); done; fi
  if [[ -n "$volume_mappings" ]]; then IFS=',' read -r -a values <<<"$volume_mappings"; for item in "${values[@]}"; do [[ "$item" == *:* ]] || { echo "Invalid volume mapping: $item" >&2; return 2; }; cmd+=(-v "$item"); done; fi
  if [[ -n "$network_name" ]]; then docker network inspect "$network_name" >/dev/null 2>&1 || { echo "Unknown Docker network: $network_name" >&2; return 2; }; cmd+=(--network "$network_name"); fi
  cmd+=("$image_name")
  echo "Creating '$container_name' from '$image_name' (environment values are not echoed)."
  "${cmd[@]}"
}''')

# Benchmark input/dependency boundaries.
text = text.replace(
    '  # Check for host \'ab\'\n  local have_host_ab=0\n',
    '  validate_positive_int "$instances" && validate_positive_int "$requests" && validate_positive_int "$concurrency" || { echo "Error: benchmark counts must be positive integers." >&2; return 2; }\n  ((concurrency <= requests)) || { echo "Error: concurrency cannot exceed requests." >&2; return 2; }\n\n  # Check for host \'ab\'\n  local have_host_ab=0\n',
    1,
)
text = text.replace("    echo \"Host 'ab' not found; using Docker image 'jordi/ab'.\"\n", "    local ab_image=\"${DOCKEX_AB_IMAGE:-jordi/ab}\"\n    docker image inspect \"$ab_image\" >/dev/null 2>&1 || { echo \"Error: host 'ab' is unavailable and benchmark image '$ab_image' is not local; install/pull one explicitly.\" >&2; return 1; }\n    echo \"Host 'ab' not found; using local Docker image '$ab_image'.\"\n", 1)
text = text.replace('      jordi/ab -n "$requests" -c "$concurrency" "$docker_url" 2>&1', '      "$ab_image" -n "$requests" -c "$concurrency" "$docker_url" 2>&1', 1)
text = text.replace('        jordi/ab -n "$requests" -c "$concurrency" "$docker_url" >"$tmp_dir/node_$i.out" 2>&1 &', '        "$ab_image" -n "$requests" -c "$concurrency" "$docker_url" >"$tmp_dir/node_$i.out" 2>&1 &', 1)
# Bound ApacheBench invocations when GNU timeout exists.
text = text.replace('    ab -n "$requests" -c "$concurrency" "$url" 2>&1', '    run_bounded 120 ab -n "$requests" -c "$concurrency" "$url" 2>&1', 1)
text = text.replace('      ab -n "$requests" -c "$concurrency" "$url" >"$tmp_dir/node_$i.out" 2>&1 &', '      run_bounded 120 ab -n "$requests" -c "$concurrency" "$url" >"$tmp_dir/node_$i.out" 2>&1 &', 1)

# Stats input and per-sample Docker call are bounded.
text = text.replace(
    '  validate_container "$container_name" "running"\n\n  if [ "$duration" -le 0 ] 2>/dev/null; then\n    duration=30\n  fi\n  if [ "$interval" -le 0 ] 2>/dev/null; then\n    interval=2\n  fi\n',
    '  validate_container "$container_name" "running"\n  validate_positive_int "$duration" && validate_positive_int "$interval" || { echo "Error: duration and interval must be positive integers." >&2; return 2; }\n',
    1,
)
text = text.replace("    line=$(docker stats --no-stream --format '{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.MemPerc}}' \"$container_name\" 2>/dev/null || true)", "    line=$(run_bounded 10 docker stats --no-stream --format '{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.MemPerc}}' \"$container_name\" 2>/dev/null || true)", 1)

replace_section(
    '# ---------------- cleanup -------------------------- #',
    '# ---------------- main dispatch -------------------- #',
    r'''cleanup() {
  local cleanup_type="${1:-unused}"; shift || true
  local assume_yes=0 confirm_all=0
  while (($#)); do
    case "$1" in --yes|-y) assume_yes=1 ;; --confirm-all) confirm_all=1 ;; *) echo "Invalid cleanup option: $1" >&2; return 2 ;; esac
    shift
  done
  case "$cleanup_type" in unused|aggressive|all) ;; *) echo 'Usage: cleanup [unused|aggressive|all] [--yes] [--confirm-all]' >&2; return 2 ;; esac
  if [[ "$cleanup_type" == all && "$confirm_all" -ne 1 ]]; then
    echo 'Error: cleanup all requires --confirm-all in addition to confirmation.' >&2; return 2
  fi
  if ((assume_yes == 0)); then
    [[ -t 0 ]] || { echo 'Error: cleanup is destructive; non-interactive use requires --yes.' >&2; return 2; }
    local confirm
    read -r -p "Proceed with '$cleanup_type' cleanup? (y/N): " confirm
    [[ "$confirm" =~ ^[yY]$ ]] || { echo 'Cleanup aborted.'; return 0; }
  fi

  case "$cleanup_type" in
  unused)
    docker container prune -f
    docker image prune -f
    docker volume prune -f
    docker network prune -f
    ;;
  aggressive)
    docker container prune -f
    docker image prune -a -f
    docker volume prune -f
    docker network prune -f
    ;;
  all)
    local -a ids=()
    mapfile -t ids < <(docker ps -q); ((${#ids[@]})) && docker stop "${ids[@]}" || true
    mapfile -t ids < <(docker ps -aq); ((${#ids[@]})) && docker container rm -f "${ids[@]}" || true
    mapfile -t ids < <(docker images -q | sort -u); ((${#ids[@]})) && docker rmi -f "${ids[@]}" || true
    mapfile -t ids < <(docker volume ls -q); ((${#ids[@]})) && docker volume rm -f "${ids[@]}" || true
    mapfile -t ids < <(docker network ls --filter type=custom -q); ((${#ids[@]})) && docker network rm "${ids[@]}" || true
    ;;
  esac
  echo 'Cleanup complete.'
}''')

# Main boundary: sourcing for tests must not dispatch, normal commands require a reachable context.
main_marker = '# ---------------- main dispatch -------------------- #\n'
text = text.replace(main_marker, main_marker + '\nif [[ "${DOCKEX_LIBRARY_MODE:-0}" == "1" ]]; then\n  return 0 2>/dev/null || exit 0\nfi\n\nensure_docker_ready || exit 1\n', 1)

# Info opt-in and new backup/restore argument pass-through.
text = text.replace('  view_container_info "$container_name"\n', '  show_env_values=0\n  [[ "${3:-}" == "--show-env-values" ]] && show_env_values=1\n  view_container_info "$container_name" "$show_env_values"\n', 1)
text = text.replace('  backup_container_data "$container_name"\n', '  shift 2\n  backup_container_data "$container_name" "$@"\n', 1)
text = text.replace('  restore_container_data "$container_name" "${3:-}"\n', '  backup_file="${3:-}"\n  [[ -n "$backup_file" ]] || { echo "Error: backup tar.gz is required." >&2; exit 1; }\n  shift 3\n  restore_container_data "$container_name" "$backup_file" "$@"\n', 1)
text = text.replace('  cleanup "${2:-unused}"\n', '  shift\n  cleanup "$@"\n', 1)

path.write_text(text)
