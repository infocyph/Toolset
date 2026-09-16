#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

command -v docker >/dev/null 2>&1 || { echo 'SKIP: docker unavailable'; exit 0; }
command -v jq >/dev/null 2>&1 || { echo 'SKIP: jq unavailable'; exit 0; }
docker info >/dev/null 2>&1 || { echo 'SKIP: Docker daemon unavailable'; exit 0; }

docker pull alpine:3.22 >/dev/null

TMP_ROOT="$(mktemp -d)"
NAME="dockex-phase2-$$"
VOLUME="dockex-phase2-vol-$$"
cleanup_test() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker volume rm -f "$VOLUME" >/dev/null 2>&1 || true
  rm -rf -- "$TMP_ROOT"
}
trap cleanup_test EXIT INT TERM

docker volume create "$VOLUME" >/dev/null
docker run -d --name "$NAME" \
  -e 'DOCKEX_SECRET=super-secret-value' \
  -v "$VOLUME:/data" \
  alpine:3.22 sh -c 'printf "original\n" >/data/value.txt; sleep 300' >/dev/null

export DOCKEX_LIBRARY_MODE=1
# shellcheck source=Docker/dockex
source Docker/dockex
unset DOCKEX_LIBRARY_MODE

ensure_docker_ready || fail 'Docker readiness check failed on active daemon'
pass "Docker context/daemon readiness: $(docker_context_name)"

validate_container "$NAME" running || fail 'exact running container was not found'
if validate_container "${NAME}.*" any >/dev/null 2>&1; then fail 'container identity accepted a grep-style pattern'; fi
pass 'container identity uses Docker-native exact inspect semantics'

redacted="$(view_container_info "$NAME")"
assert_contains "$redacted" 'DOCKEX_SECRET=<redacted>' 'default info output should redact env values'
[[ "$redacted" != *'super-secret-value'* ]] || fail 'default info leaked an environment secret'
revealed="$(view_container_info "$NAME" 1)"
assert_contains "$revealed" 'DOCKEX_SECRET=super-secret-value' 'explicit env-value opt-in'
pass 'environment values are redacted by default and opt-in only'

set +e
live_backup_output="$(cd "$TMP_ROOT" && backup_container_data "$NAME" --mount=/data 2>&1)"
live_backup_rc=$?
set -e
((live_backup_rc != 0)) || fail 'live backup unexpectedly proceeded without an explicit consistency mode'
assert_contains "$live_backup_output" 'application-inconsistent' 'live backup safety warning'
pass 'running-container backup requires explicit consistency choice'

(
  cd "$TMP_ROOT"
  backup_container_data "$NAME" --mount=/data --stop >/dev/null
)
archive="$(find "$TMP_ROOT" -maxdepth 1 -name "${NAME}-data-*.tar.gz" -print -quit)"
[[ -s "$archive" ]] || fail 'quiesced tar backup was not created'
is_container_running "$NAME" || fail 'container was not restarted after --stop backup'
pass 'quiesced mount-scoped tar backup and restart'

docker exec "$NAME" sh -c 'printf "changed\n" >/data/value.txt'
set +e
live_restore_output="$(restore_container_data "$NAME" "$archive" --mount=/data 2>&1)"
live_restore_rc=$?
set -e
((live_restore_rc != 0)) || fail 'live restore unexpectedly proceeded without an explicit consistency mode'
assert_contains "$live_restore_output" 'restoring into a running container is unsafe' 'live restore safety warning'

restore_container_data "$NAME" "$archive" --mount=/data --stop >/dev/null
restored="$(docker exec "$NAME" cat /data/value.txt)"
assert_eq 'original' "$restored" 'mount-scoped restore content'
is_container_running "$NAME" || fail 'container was not restarted after --stop restore'
pass 'restore is scoped to selected mount and preserves runtime state'

# Archive traversal is rejected before any helper container extracts it.
mkdir -p "$TMP_ROOT/bad"
printf 'bad\n' >"$TMP_ROOT/bad/file"
tar -czf "$TMP_ROOT/bad.tar.gz" --transform='s#file#../escape#' -C "$TMP_ROOT/bad" file
set +e
bad_restore_output="$(restore_container_data "$NAME" "$TMP_ROOT/bad.tar.gz" --mount=/data --live 2>&1)"
bad_restore_rc=$?
set -e
((bad_restore_rc != 0)) || fail 'path-traversal archive was accepted'
assert_contains "$bad_restore_output" 'parent-traversal' 'archive traversal error'
pass 'restore rejects archive traversal paths'

set +e
resource_output="$(update_container_resources "$NAME" 'not-a-cpu-value' '1g' 2>&1)"
resource_rc=$?
set -e
((resource_rc != 0)) || fail 'invalid resource input was accepted'
assert_contains "$resource_output" 'Invalid CPU shares' 'resource validation error'
pass 'resource update inputs are validated before mutation'

# Destructive cleanup must never infer consent from non-interactive execution.
set +e
cleanup_output="$(cleanup unused 2>&1 </dev/null)"
cleanup_rc=$?
set -e
((cleanup_rc != 0)) || fail 'non-interactive cleanup proceeded without --yes'
assert_contains "$cleanup_output" 'requires --yes' 'non-interactive cleanup confirmation error'

set +e
cleanup_all_output="$(cleanup all --yes 2>&1)"
cleanup_all_rc=$?
set -e
((cleanup_all_rc != 0)) || fail 'cleanup all proceeded without --confirm-all'
assert_contains "$cleanup_all_output" 'requires --confirm-all' 'cleanup-all second confirmation token'
pass 'cleanup requires explicit non-interactive consent and all-resource token'

printf '\nAll dockex ephemeral safety checks passed.\n'
