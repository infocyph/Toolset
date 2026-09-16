#!/usr/bin/env python3
from pathlib import Path
import re


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


install = read('install.sh')
install = install.replace('  --release <version>   Install an exact suite release (for example v2.0.0 or v2.0.0-rc.1).','  --release <version>   Install an exact suite release tag (for example 2.0).')
install = install.replace('bash install.sh --release v2.0.0 gitx netx','bash install.sh --release 2.0 gitx netx')
install = install.replace('bash install.sh --release v2.0.0-rc.1 --all','bash install.sh --release 2.0 --all')
install = install.replace('''if [[ "$RELEASE" != "latest" ]]; then
  RELEASE="v${RELEASE#v}"
  [[ "$RELEASE" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$ ]] || {
    printf 'install.sh: release must use MAJOR.MINOR.PATCH, vMAJOR.MINOR.PATCH, or an -rc.N prerelease\n' >&2
    exit 2
  }
fi
''','''if [[ "$RELEASE" != "latest" ]]; then
  [[ "$RELEASE" =~ ^v?[0-9]+\.[0-9]+(\.[0-9]+)?(-rc\.[0-9]+)?$ ]] || {
    printf 'install.sh: release must be an exact numeric tag such as 2.0, 2.0.1, or v2.0.1\n' >&2
    exit 2
  }
fi
''')
if 'TOOLSET_RELEASE_BASE_URL' not in install:
    install = install.replace('''else
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

mkdir -p -- "$PREFIX"''')
write('install.sh', install)

for path in ['Git/gitx','PHP/phpx','Clean/cleanx','ChromaCat/chromacat']:
    text = read(path)
    text = text.replace('[[ "$release" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+(-rc\\.[0-9]+)?$ ]]','[[ "$release" =~ ^v?[0-9]+\\.[0-9]+(\\.[0-9]+)?(-rc\\.[0-9]+)?$ ]]')
    marker='''    base="https://github.com/infocyph/Toolset/releases/download/$release"
    install_args=(--release "$release")
  fi

  for cmd in curl sha256sum mktemp install mv awk; do'''
    if marker in text:
        text=text.replace(marker,'''    base="https://github.com/infocyph/Toolset/releases/download/$release"
    install_args=(--release "$release")
  fi
  if [[ -n "${TOOLSET_RELEASE_BASE_URL:-}" ]]; then
    base="${TOOLSET_RELEASE_BASE_URL%/}"
  fi

  for cmd in curl sha256sum mktemp install mv awk; do''',1)
    write(path,text)

release=read('.github/workflows/release.yml')
release=release.replace("      - 'v*.*.*'","      - '*.*'")
release=release.replace('if ! [[ "$tag" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+(-rc\\.[0-9]+)?$ ]]; then','if ! [[ "$tag" =~ ^[0-9]+\\.[0-9]+$ ]]; then')
release=release.replace('Release tag must use vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH-rc.N format:','Stable Toolset release tags must use MAJOR.MINOR format (for example 2.0):')
release=release.replace('SUITE_VERSION="${RELEASE_TAG#v}"','SUITE_VERSION="$RELEASE_TAG"')
release=release.replace("os.environ['RELEASE_TAG'].removeprefix('v')","os.environ['RELEASE_TAG']")
release=release.replace('version="${GITHUB_REF_NAME#v}"','version="$GITHUB_REF_NAME"')
release=re.sub(r'\n\s*if \[\[ "\$GITHUB_REF_NAME" == \*-rc\.\* \]\]; then\n\s*args\+=\(--prerelease\)\n\s*fi\n','\n',release)
write('.github/workflows/release.yml',release)

write('tests/release-delivery.sh',r'''#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source tests/lib/assert.sh
for cmd in bash curl git install mktemp python3 sha256sum; do command -v "$cmd" >/dev/null 2>&1 || fail "release delivery test requires $cmd"; done
TAG="2.0"; SUITE_VERSION="$TAG"; SOURCE_COMMIT="$(git rev-parse HEAD)"
TMP_ROOT="$(mktemp -d)"; DIST_DIR="$TMP_ROOT/dist"; SERVER_ROOT="$TMP_ROOT/server"; PREFIX="$TMP_ROOT/install"; SELF_PREFIX="$TMP_ROOT/self-update"; FAIL_STATE="$TMP_ROOT/fail-next-request"; SERVER_SCRIPT="$TMP_ROOT/flaky_server.py"; SERVER_PID=""
cleanup(){ if [[ -n "$SERVER_PID" ]]; then kill "$SERVER_PID" >/dev/null 2>&1 || true; wait "$SERVER_PID" 2>/dev/null || true; fi; rm -rf -- "$TMP_ROOT"; }
trap cleanup EXIT INT TERM
RELEASE_TAG="$TAG" SUITE_VERSION="$SUITE_VERSION" SOURCE_COMMIT="$SOURCE_COMMIT" DIST_DIR="$DIST_DIR" bash tests/distribution.sh >/dev/null
pass "release assets build locally"
mkdir -p -- "$SERVER_ROOT" "$PREFIX" "$SELF_PREFIX"; cp -a -- "$DIST_DIR"/. "$SERVER_ROOT"/
PORT="$(python3 - <<'PY'
import socket
with socket.socket() as s:
    s.bind(('127.0.0.1',0)); print(s.getsockname()[1])
PY
)"
cat >"$SERVER_SCRIPT" <<'PY'
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
python3 "$SERVER_SCRIPT" "$SERVER_ROOT" "$PORT" "$FAIL_STATE" >/dev/null 2>&1 & SERVER_PID=$!
LOCAL_BASE="http://127.0.0.1:$PORT"
for _ in {1..30}; do curl --fail --silent --show-error "$LOCAL_BASE/SHA256SUMS" >/dev/null 2>&1 && break; sleep 0.1; done
curl --fail --silent --show-error "$LOCAL_BASE/SHA256SUMS" >/dev/null
pass "local release endpoint is available"
release_env=("TOOLSET_RELEASE_BASE_URL=$LOCAL_BASE" "TOOLSET_DOWNLOAD_ATTEMPTS=2")
: >"$FAIL_STATE"
env "${release_env[@]}" bash "$DIST_DIR/install.sh" --release "$TAG" --prefix "$PREFIX" --all >/dev/null
[[ ! -e "$FAIL_STATE" ]] || fail "installer did not consume the injected transient failure"
pass "installer recovers from a simulated connection reset"
for tool in chromacat cleanx dockex gitx netx phpx sqlitex; do
  expected="$(sha256sum "$DIST_DIR/$tool"|awk '{print $1}')"; actual="$(sha256sum "$PREFIX/$tool"|awk '{print $1}')"; assert_eq "$expected" "$actual" "installed release digest: $tool"; NO_COLOR=1 PHPX_NO_LOG=1 NETX_COLOR=never TERM=dumb "$PREFIX/$tool" --version >/dev/null; pass "exact 2.0 install: $tool"
done
for tool in gitx phpx cleanx chromacat; do install -m 0755 -- "$DIST_DIR/$tool" "$SELF_PREFIX/$tool"; done
verify_self_update(){ local tool="$1"; shift; : >"$FAIL_STATE"; env "${release_env[@]}" TOOLSET_SELF_UPDATE_RELEASE="$TAG" PHPX_NO_LOG=1 NO_COLOR=1 TERM=dumb "$SELF_PREFIX/$tool" "$@" >/dev/null; [[ ! -e "$FAIL_STATE" ]] || fail "$tool self-update did not consume transient failure"; local e a; e="$(sha256sum "$DIST_DIR/$tool"|awk '{print $1}')"; a="$(sha256sum "$SELF_PREFIX/$tool"|awk '{print $1}')"; assert_eq "$e" "$a" "self-update release digest: $tool"; pass "exact 2.0 self-update with retry: $tool"; }
verify_self_update gitx self-update
verify_self_update phpx self-update
verify_self_update cleanx --update
verify_self_update chromacat --self-update
printf '\nAll simulated Toolset 2.0 release delivery and self-update checks passed.\n'
''')

ci=read('.github/workflows/ci.yml')
job='''  release_delivery:\n    name: Simulated 2.0 release delivery\n    runs-on: ubuntu-24.04\n    timeout-minutes: 10\n    steps:\n      - name: Checkout\n        uses: actions/checkout@v7\n      - name: Verify exact 2.0 install/self-update delivery with transient retry\n        run: bash tests/release-delivery.sh\n\n'''
if '  release_delivery:\n' not in ci: ci=ci.replace('  distribution:\n    name: Standalone distribution artifacts\n',job+'  distribution:\n    name: Standalone distribution artifacts\n',1)
if '      - release_delivery\n' not in ci: ci=ci.replace('      - distribution\n','      - distribution\n      - release_delivery\n',1)
if 'RELEASE_DELIVERY_RESULT:' not in ci:
    ci=ci.replace('          DISTRIBUTION_RESULT: ${{ needs.distribution.result }}\n','          DISTRIBUTION_RESULT: ${{ needs.distribution.result }}\n          RELEASE_DELIVERY_RESULT: ${{ needs.release_delivery.result }}\n',1)
    ci=ci.replace('            echo "| Distribution | $DISTRIBUTION_RESULT |"\n','            echo "| Distribution | $DISTRIBUTION_RESULT |"\n            echo "| Simulated 2.0 release delivery | $RELEASE_DELIVERY_RESULT |"\n',1)
    ci=ci.replace('            "$DISTRIBUTION_RESULT"; do\n','            "$DISTRIBUTION_RESULT" \\\n            "$RELEASE_DELIVERY_RESULT"; do\n',1)
write('.github/workflows/ci.yml',ci)

for path in ['README.md','Git/README.md','PHP/README.md','Docker/README.md','Network/README.md','Sqlite/README.md','Clean/README.md','ChromaCat/README.md']:
    t=read(path).replace('v2.0.0-rc.1','2.0').replace('v2.0.0','2.0').replace('TOOLSET_SELF_UPDATE_RELEASE=vX.Y.Z[-rc.N]','TOOLSET_SELF_UPDATE_RELEASE=2.0'); write(path,t)
root=read('README.md').replace('Release tags follow strict `vMAJOR.MINOR.PATCH` versioning. Published release assets are treated as immutable.','Stable Toolset suite tags use `MAJOR.MINOR`; Toolset 2.0 is published from immutable tag `2.0`.').replace('Released consumers should pin an immutable release tag or commit SHA. Release candidates are GitHub prereleases used for acceptance/downstream integration; stable `vMAJOR.MINOR.PATCH` assets remain immutable.','Released consumers should pin immutable stable tag `2.0` or the tagged commit SHA; published assets are immutable.'); write('README.md',root)
contracts=read('docs/cli-contracts.md').replace('Stable tags are immutable. Release candidates use prerelease tags and are intended for acceptance/downstream integration testing. Released downstream consumers should pin an exact tag or commit SHA rather than `main`.','Stable suite tags are immutable. Toolset 2.0 uses canonical tag `2.0`. Released downstream consumers should pin that exact tag or a commit SHA rather than `main`.').replace('- Stable installation and self-update use checksum-verified release assets. Mutable `main` is not a stable channel.','- Stable installation and self-update use checksum-verified release assets. Mutable `main` is not a stable channel. `TOOLSET_RELEASE_BASE_URL` is an explicit trusted mirror/test override and never disables checksum verification.'); write('docs/cli-contracts.md',contracts)
security=read('docs/security-review.md').replace('Release tags/assets are treated as immutable. Release candidates use explicit `-rc.N` prerelease tags so acceptance testing can exercise the same checksum/install/self-update path without becoming `releases/latest`.','Release tags/assets are immutable. Before merge, `tests/release-delivery.sh` exercises exact tag `2.0` through a trusted local mirror and injects a transient connection reset; after merge, the maintainer creates tag `2.0` and the release workflow repeats live verification.').replace('Toolset 2.0/RC is security-ready only when all of the following remain green on the exact candidate source:','Toolset 2.0 is pre-merge security/release-ready only when all of the following remain green on the exact candidate source:').replace('8. published RC asset download, checksum, installer and exact-release self-update verification.','8. simulated exact-`2.0` checksum/install/self-update delivery with transient retry; after tag `2.0` exists, the release workflow repeats these checks against published GitHub assets.'); write('docs/security-review.md',security)

tracker=read('docs/plans/toolset-2.0-progress-tracker.md')
tracker=tracker.replace('**Phase 4 — Presentation Path**\n\nCurrent task: harden `chromacat`: preserve faithful non-TTY/plain pipeline output, tighten option/no-color/Unicode/TERM behavior, keep streaming bounded, and add golden pipeline/stream fixtures.','**Release Readiness — final pre-merge gate**\n\nCurrent task: pass exact `2.0` delivery/self-update verification and leave PR #47 ready for maintainer merge. Merge and tag creation are maintainer actions.')
tracker=tracker.replace('Suite release version comes from immutable `vMAJOR.MINOR.PATCH` Git tag.','Suite release version comes from immutable stable tag `2.0`.').replace('Strict `vMAJOR.MINOR.PATCH` tag validation.','Strict stable `MAJOR.MINOR` tag validation; Toolset 2.0 expects `2.0`.').replace('Immutable semantic-tag release workflow builds/publishes versioned assets with checksums and manifest; actual `v2.0.0` publication remains intentionally deferred until the full hardening cycle is complete.','Immutable release workflow publishes checksummed assets/manifest; maintainer creates tag `2.0` only after PR #47 is merged.')
phase='''## Phase 4 — Presentation Path\n\n- [x] `chromacat` faithful non-TTY/plain pipeline behavior.\n- [x] Unknown options fail clearly; explicit passthrough remains available.\n- [x] `--no-color` / `NO_COLOR` output is ANSI-free.\n- [x] Unicode width behavior reviewed/documented.\n- [x] Streaming remains bounded/efficient.\n- [x] Missing TERM/tput handled safely.\n- [x] Stable self-update hardened.\n- [x] Golden pipeline/no-color/stream tests added.\n\n### Phase 4 Gate\n- [x] Presentation integration suite passes in permanent CI.\n\n## Phase 5 — Documentation, Release Readiness & Downstream Pins\n\n- [x] Root/per-tool docs normalized to stable release model.\n- [x] Dependency/capability matrix documented.\n- [x] Destructive/security and output/exit contracts documented.\n- [x] Docs verified against live help/version in CI.\n- [x] Deterministic release assets/checksums/manifest implemented.\n- [x] Portable bounded download retries implemented.\n- [x] Simulated exact `2.0` install/self-update delivery test added.\n- [x] Canonical stable tag selected: `2.0` (no `v`).\n- [ ] **Maintainer:** merge PR #47.\n- [ ] **Maintainer:** create/push tag `2.0` on merged commit.\n- [ ] Release workflow publishes/live-verifies `2.0` assets.\n- [ ] Downstream Docker/LocalDevStack pins immutable tag `2.0` after it exists.\n\n## Cross-Cutting Security Checklist\n\n- [x] `eval` review.\n- [x] Writable config sourcing review.\n- [x] Fixed `/tmp` review.\n- [x] Recursive deletion / `find -delete` review.\n- [x] Remote download/checksum review.\n- [x] Secret/environment output review.\n- [x] Quoting/path delimiter review.\n- [x] `bash -c` / `sh -c` review.\n- [x] Mutable `main`/`master` URL review.\n- [x] Root/sudo assumption review.\n- [x] Background process/trap cleanup review.\n'''
tracker=re.sub(r'## Phase 4 — Presentation Path\n.*?## Decisions Locked\n',phase+'\n## Decisions Locked\n',tracker,count=1,flags=re.S)
tracker=tracker.replace('| 2026-09-16 | Started `phpx` Phase 2 capability and mutation-path hardening. | in progress |','| 2026-09-16 | Completed `phpx`, `dockex`, and `sqlitex` Phase 2 hardening with permanent safety fixtures. | done |')
tracker=re.sub(r'## Next Task\n\n.*\Z','## Next Task\n\nPass final clean PR CI with exact tag `2.0`, then delete both planning files before maintainer merge. After merge, maintainer creates tag `2.0`; downstream pinning follows only after the tag exists.\n',tracker,flags=re.S)
write('docs/plans/toolset-2.0-progress-tracker.md',tracker)

plan=read('docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md').replace('Recommended target: **Toolset 2.0.0**','Target release: **Toolset 2.0** (stable tag: `2.0`)')
plan=re.sub(r'Use strict repository release tags going forward:\n\n```text\n.*?```\n\nKeep historical tags unchanged\.','Use immutable suite release tags. Toolset 2.0 uses canonical stable tag `2.0` with no `v` prefix. Maintainer creates that tag only after PR #47 is merged. Historical tags remain unchanged.',plan,count=1,flags=re.S)
plan=plan.replace('- publish only from semantic-version tags;','- publish only from validated stable `MAJOR.MINOR` suite tags; Toolset 2.0 uses `2.0`;')
plan=re.sub(r'### Phase 5 — Documentation & downstream pins\n\n1\..*?contract is stable\.','''### Phase 5 — Documentation, release readiness & downstream pins\n\n1. Update/verify docs.\n2. Simulate exact `2.0` release delivery with transient retry.\n3. Pass complete clean PR CI/security/distribution gates.\n4. Delete completed plan/tracker files from merge candidate.\n5. Maintainer merges PR #47.\n6. Maintainer creates/pushes stable tag `2.0`.\n7. Permanent release workflow publishes/live-verifies GitHub assets.\n8. Downstream consumers then pin immutable tag `2.0`.''',plan,count=1,flags=re.S)
write('docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md',plan)

Path('.github/scripts/sync-toolset-2.0-release-plan.py').unlink(missing_ok=True)
Path('.github/workflows/sync-toolset-2.0-release-plan.yml').unlink(missing_ok=True)
