#!/usr/bin/env python3
from pathlib import Path
import re


def read(path): return Path(path).read_text()
def write(path, text): Path(path).write_text(text)

# Installer exact-tag parsing and optional trusted mirror/test base.
p='install.sh'; t=read(p)
t=re.sub(r'if \[\[ "\$RELEASE" != "latest" \]\]; then\n.*?\nfi\n\nrequire_cmd bash', '''if [[ "$RELEASE" != "latest" ]]; then
  [[ "$RELEASE" =~ ^v?[0-9]+\.[0-9]+(\.[0-9]+)?(-rc\.[0-9]+)?$ ]] || {
    printf 'install.sh: release must be an exact numeric tag such as 2.0, 2.0.1, or v2.0.1\n' >&2
    exit 2
  }
fi

require_cmd bash''', t, count=1, flags=re.S)
if 'TOOLSET_RELEASE_BASE_URL' not in t:
    t=t.replace('''else
  BASE_URL="https://github.com/${REPOSITORY}/releases/download/${RELEASE}"
  RELEASE_LABEL="$RELEASE"
fi

mkdir -p -- "$PREFIX"''','''else
  BASE_URL="https://github.com/${REPOSITORY}/releases/download/${RELEASE}"
  RELEASE_LABEL="$RELEASE"
fi
if [[ -n "${TOOLSET_RELEASE_BASE_URL:-}" ]]; then
  BASE_URL="${TOOLSET_RELEASE_BASE_URL%/}"
fi

mkdir -p -- "$PREFIX"''',1)
write(p,t)

# Self-updaters use exact 2.0 and can be pointed at a trusted mirror for testing.
for p in ['Git/gitx','PHP/phpx','Clean/cleanx','ChromaCat/chromacat']:
    t=read(p)
    t=re.sub(r'\[\[ "\$release" =~ \^v\[0-9\]\+\\\.\[0-9\]\+\\\.\[0-9\]\+\(-rc\\\.\[0-9\]\+\)\?\$ \]\]', '[[ "$release" =~ ^v?[0-9]+\\.[0-9]+(\\.[0-9]+)?(-rc\\.[0-9]+)?$ ]]', t, count=1)
    marker='''    base="https://github.com/infocyph/Toolset/releases/download/$release"
    install_args=(--release "$release")
  fi

  for cmd in curl sha256sum mktemp install mv awk; do'''
    if marker in t:
        t=t.replace(marker,'''    base="https://github.com/infocyph/Toolset/releases/download/$release"
    install_args=(--release "$release")
  fi
  if [[ -n "${TOOLSET_RELEASE_BASE_URL:-}" ]]; then
    base="${TOOLSET_RELEASE_BASE_URL%/}"
  fi

  for cmd in curl sha256sum mktemp install mv awk; do''',1)
    write(p,t)

# Stable release workflow must trigger only on MAJOR.MINOR (2.0).
p='.github/workflows/release.yml'; t=read(p)
t=t.replace("      - 'v*.*.*'","      - '*.*'")
t=re.sub(r'if ! \[\[ "\$tag" =~ \^v\[0-9\]\+\\\.\[0-9\]\+\\\.\[0-9\]\+\(-rc\\\.\[0-9\]\+\)\?\$ \]\]; then', 'if ! [[ "$tag" =~ ^[0-9]+\\.[0-9]+$ ]]; then', t)
t=t.replace('Release tag must use vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH-rc.N format:', 'Stable Toolset release tags must use MAJOR.MINOR format (for example 2.0):')
t=t.replace('SUITE_VERSION="${RELEASE_TAG#v}"','SUITE_VERSION="$RELEASE_TAG"')
t=t.replace("os.environ['RELEASE_TAG'].removeprefix('v')","os.environ['RELEASE_TAG']")
t=t.replace('version="${GITHUB_REF_NAME#v}"','version="$GITHUB_REF_NAME"')
t=re.sub(r'\n\s*if \[\[ "\$GITHUB_REF_NAME" == \*-rc\.\* \]\]; then\n\s*args\+=\(--prerelease\)\n\s*fi\n','\n',t)
write(p,t)

# Permanent delivery fixture: real curl against a flaky local release mirror.
write('tests/release-delivery.sh', r'''#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh
for cmd in bash curl git install mktemp python3 sha256sum; do command -v "$cmd" >/dev/null 2>&1 || fail "release delivery test requires $cmd"; done
TAG="2.0"; SUITE_VERSION="$TAG"; SOURCE_COMMIT="$(git rev-parse HEAD)"
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
for tool in chromacat cleanx dockex gitx netx phpx sqlitex; do e="$(sha256sum "$DIST_DIR/$tool"|awk '{print $1}')"; a="$(sha256sum "$PREFIX/$tool"|awk '{print $1}')"; assert_eq "$e" "$a" "install digest $tool"; NO_COLOR=1 PHPX_NO_LOG=1 NETX_COLOR=never TERM=dumb "$PREFIX/$tool" --version >/dev/null; pass "exact 2.0 install: $tool"; done
for tool in gitx phpx cleanx chromacat; do install -m 0755 -- "$DIST_DIR/$tool" "$SELF_PREFIX/$tool"; done
upd(){ local tool="$1"; shift; : >"$FAIL_STATE"; env "${envargs[@]}" TOOLSET_SELF_UPDATE_RELEASE="$TAG" PHPX_NO_LOG=1 NO_COLOR=1 TERM=dumb "$SELF_PREFIX/$tool" "$@" >/dev/null; [[ ! -e "$FAIL_STATE" ]] || fail "$tool did not retry transient failure"; e="$(sha256sum "$DIST_DIR/$tool"|awk '{print $1}')"; a="$(sha256sum "$SELF_PREFIX/$tool"|awk '{print $1}')"; assert_eq "$e" "$a" "self-update digest $tool"; pass "exact 2.0 self-update: $tool"; }
upd gitx self-update; upd phpx self-update; upd cleanx --update; upd chromacat --self-update
printf '\nAll simulated Toolset 2.0 release delivery and self-update checks passed.\n'
''')

# Clean one-shot machinery in resulting candidate.
Path('.github/scripts/finalize-exact-2.0.py').unlink(missing_ok=True)
Path('.github/scripts/sync-toolset-2.0-release-plan.py').unlink(missing_ok=True)
Path('.github/workflows/sync-toolset-2.0-release-plan.yml').unlink(missing_ok=True)
