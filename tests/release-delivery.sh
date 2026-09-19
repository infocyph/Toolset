#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh
for cmd in bash curl git install mktemp python3 sha256sum; do command -v "$cmd" >/dev/null 2>&1 || fail "release delivery test requires $cmd"; done
TAG="2.0.1"; SUITE_VERSION="$TAG"; SOURCE_COMMIT="$(git rev-parse HEAD)"
TMP_ROOT="$(mktemp -d)"; DIST_DIR="$TMP_ROOT/dist"; SERVER_ROOT="$TMP_ROOT/server"; PREFIX="$TMP_ROOT/install"; SELF_PREFIX="$TMP_ROOT/self-update"; FAIL_STATE="$TMP_ROOT/fail-next-request"; SERVER="$TMP_ROOT/server.py"; SERVER_PID=""
cleanup(){ [[ -z "$SERVER_PID" ]] || { kill "$SERVER_PID" >/dev/null 2>&1 || true; wait "$SERVER_PID" 2>/dev/null || true; }; rm -rf -- "$TMP_ROOT"; }; trap cleanup EXIT INT TERM
RELEASE_TAG="$TAG" SUITE_VERSION="$SUITE_VERSION" SOURCE_COMMIT="$SOURCE_COMMIT" DIST_DIR="$DIST_DIR" bash tests/distribution.sh >/dev/null
pass "release assets build locally"; mkdir -p -- "$SERVER_ROOT" "$PREFIX" "$SELF_PREFIX"; cp -a -- "$DIST_DIR"/. "$SERVER_ROOT"/
PORT="$(python3 - <<'PY'
import socket
with socket.socket() as s: s.bind(('127.0.0.1',0)); print(s.getsockname()[1])
PY
)"
cat >"$SERVER" <<'PY'
import http.server,socket,sys
from pathlib import Path
root,port,state=sys.argv[1],int(sys.argv[2]),Path(sys.argv[3])
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**k): super().__init__(*a,directory=root,**k)
    def log_message(self,*a): pass
    def do_GET(self):
        if state.exists():
            state.unlink(missing_ok=True)
            try: self.connection.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            self.connection.close(); return
        super().do_GET()
http.server.ThreadingHTTPServer(('127.0.0.1',port),H).serve_forever()
PY
python3 "$SERVER" "$SERVER_ROOT" "$PORT" "$FAIL_STATE" >/dev/null 2>&1 & SERVER_PID=$!
BASE="http://127.0.0.1:$PORT"
for _ in {1..30}; do curl -fsS "$BASE/SHA256SUMS" >/dev/null 2>&1 && break; sleep .1; done
curl -fsS "$BASE/SHA256SUMS" >/dev/null; pass "local release endpoint is available"
envargs=("TOOLSET_RELEASE_BASE_URL=$BASE" "TOOLSET_DOWNLOAD_ATTEMPTS=2")
: >"$FAIL_STATE"; env "${envargs[@]}" bash "$DIST_DIR/install.sh" --release "$TAG" --prefix "$PREFIX" --all >/dev/null
[[ ! -e "$FAIL_STATE" ]] || fail "installer did not consume transient failure"; pass "installer retries transient connection reset"
for tool in chromacat cleanx dockex gitx netx phpx sqlitex; do e="$(sha256sum "$DIST_DIR/$tool"|awk '{print $1}')"; a="$(sha256sum "$PREFIX/$tool"|awk '{print $1}')"; assert_eq "$e" "$a" "install digest $tool"; NO_COLOR=1 PHPX_NO_LOG=1 NETX_COLOR=never TERM=dumb "$PREFIX/$tool" --version >/dev/null; pass "exact 2.0.1 install: $tool"; done
for tool in gitx phpx cleanx chromacat; do install -m 0755 -- "$DIST_DIR/$tool" "$SELF_PREFIX/$tool"; done
upd(){ local tool="$1"; shift; : >"$FAIL_STATE"; env "${envargs[@]}" TOOLSET_SELF_UPDATE_RELEASE="$TAG" PHPX_NO_LOG=1 NO_COLOR=1 TERM=dumb "$SELF_PREFIX/$tool" "$@" >/dev/null; [[ ! -e "$FAIL_STATE" ]] || fail "$tool did not retry transient failure"; e="$(sha256sum "$DIST_DIR/$tool"|awk '{print $1}')"; a="$(sha256sum "$SELF_PREFIX/$tool"|awk '{print $1}')"; assert_eq "$e" "$a" "self-update digest $tool"; pass "exact 2.0.1 self-update: $tool"; }
upd gitx self-update; upd phpx self-update; upd cleanx --update; upd chromacat --self-update
printf '\nAll simulated Toolset 2.0.1 release delivery and self-update checks passed.\n'
