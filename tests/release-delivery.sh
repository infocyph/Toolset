#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

for cmd in bash curl git install mktemp python3 sha256sum; do
  command -v "$cmd" >/dev/null 2>&1 || fail "release delivery test requires $cmd"
done

TAG="v2.0.0-rc.999"
SUITE_VERSION="${TAG#v}"
SOURCE_COMMIT="$(git rev-parse HEAD)"
TMP_ROOT="$(mktemp -d)"
DIST_DIR="$TMP_ROOT/dist"
SERVER_ROOT="$TMP_ROOT/server"
PREFIX="$TMP_ROOT/install"
SELF_PREFIX="$TMP_ROOT/self-update"
WRAPPER_BIN="$TMP_ROOT/bin"
FAIL_STATE="$TMP_ROOT/curl-failed-once"
HTTP_LOG="$TMP_ROOT/http.log"
REAL_CURL="$(command -v curl)"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf -- "$TMP_ROOT"
}
trap cleanup EXIT INT TERM

RELEASE_TAG="$TAG" \
SUITE_VERSION="$SUITE_VERSION" \
SOURCE_COMMIT="$SOURCE_COMMIT" \
DIST_DIR="$DIST_DIR" \
  bash tests/distribution.sh >/dev/null
pass "release assets build locally"

mkdir -p -- "$SERVER_ROOT" "$PREFIX" "$SELF_PREFIX" "$WRAPPER_BIN"
cp -a -- "$DIST_DIR"/. "$SERVER_ROOT"/

PORT="$(python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    print(sock.getsockname()[1])
PY
)"

python3 -m http.server "$PORT" \
  --bind 127.0.0.1 \
  --directory "$SERVER_ROOT" \
  >"$HTTP_LOG" 2>&1 &
SERVER_PID=$!
LOCAL_BASE="http://127.0.0.1:$PORT"

for _ in {1..30}; do
  if "$REAL_CURL" --fail --silent --show-error "$LOCAL_BASE/SHA256SUMS" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done
"$REAL_CURL" --fail --silent --show-error "$LOCAL_BASE/SHA256SUMS" >/dev/null
pass "local release endpoint is available"

cat >"$WRAPPER_BIN/curl" <<'WRAPPER'
#!/usr/bin/env bash
set -Eeuo pipefail
: "${REAL_CURL:?}"
: "${RELEASE_TAG:?}"
: "${LOCAL_BASE:?}"
: "${CURL_FAIL_STATE:?}"

args=("$@")
target=0
prefix="https://github.com/infocyph/Toolset/releases/download/${RELEASE_TAG}/"
for i in "${!args[@]}"; do
  if [[ "${args[$i]}" == "$prefix"* ]]; then
    target=1
    asset="${args[$i]#"$prefix"}"
    args[$i]="$LOCAL_BASE/$asset"
  fi
done

if ((target)) && [[ ! -e "$CURL_FAIL_STATE" ]]; then
  : >"$CURL_FAIL_STATE"
  exit 35
fi

exec "$REAL_CURL" "${args[@]}"
WRAPPER
chmod 0755 "$WRAPPER_BIN/curl"

release_env=(
  "PATH=$WRAPPER_BIN:$PATH"
  "REAL_CURL=$REAL_CURL"
  "RELEASE_TAG=$TAG"
  "LOCAL_BASE=$LOCAL_BASE"
  "CURL_FAIL_STATE=$FAIL_STATE"
  "TOOLSET_DOWNLOAD_ATTEMPTS=2"
)

rm -f -- "$FAIL_STATE"
env "${release_env[@]}" \
  bash "$DIST_DIR/install.sh" \
  --release "$TAG" \
  --prefix "$PREFIX" \
  --all >/dev/null
[[ -e "$FAIL_STATE" ]] || fail "installer retry fixture did not inject a transient failure"
pass "installer recovers from a simulated curl connection reset"

for tool in chromacat cleanx dockex gitx netx phpx sqlitex; do
  expected="$(sha256sum "$DIST_DIR/$tool" | awk '{print $1}')"
  actual="$(sha256sum "$PREFIX/$tool" | awk '{print $1}')"
  assert_eq "$expected" "$actual" "installed release digest: $tool"

  NO_COLOR=1 PHPX_NO_LOG=1 NETX_COLOR=never TERM=dumb \
    "$PREFIX/$tool" --version >/dev/null
  pass "exact release install: $tool"
done

for tool in gitx phpx cleanx chromacat; do
  install -m 0755 -- "$DIST_DIR/$tool" "$SELF_PREFIX/$tool"
done

verify_self_update() {
  local tool="$1"
  shift
  rm -f -- "$FAIL_STATE"
  env "${release_env[@]}" \
    TOOLSET_SELF_UPDATE_RELEASE="$TAG" \
    PHPX_NO_LOG=1 NO_COLOR=1 TERM=dumb \
    "$SELF_PREFIX/$tool" "$@" >/dev/null
  [[ -e "$FAIL_STATE" ]] || fail "$tool self-update did not exercise transient retry"

  local expected actual
  expected="$(sha256sum "$DIST_DIR/$tool" | awk '{print $1}')"
  actual="$(sha256sum "$SELF_PREFIX/$tool" | awk '{print $1}')"
  assert_eq "$expected" "$actual" "self-update release digest: $tool"
  pass "exact release self-update with retry: $tool"
}

verify_self_update gitx self-update
verify_self_update phpx self-update
verify_self_update cleanx --update
verify_self_update chromacat --self-update

printf '\nAll simulated release delivery and self-update checks passed.\n'
