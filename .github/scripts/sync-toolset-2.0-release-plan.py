#!/usr/bin/env python3
from pathlib import Path
import re


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


def replace_once(path, old, new):
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence, found {count}: {old[:80]!r}")
    write(path, text.replace(old, new, 1))


def replace_all(path, old, new):
    text = read(path)
    if old in text:
        write(path, text.replace(old, new))


def regex_once(path, pattern, repl, flags=re.S):
    text = read(path)
    new, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"{path}: regex target not found: {pattern[:100]!r}")
    write(path, new)


# ---------------------------------------------------------------------------
# Stable release tag contract: the maintainer will tag the merged commit `2.0`.
# ---------------------------------------------------------------------------
replace_once(
    'install.sh',
    '  --release <version>   Install an exact suite release (for example v2.0.0 or v2.0.0-rc.1).',
    '  --release <version>   Install an exact suite release tag (for example 2.0).'
)
replace_all('install.sh', 'bash install.sh --release v2.0.0 gitx netx', 'bash install.sh --release 2.0 gitx netx')
replace_all('install.sh', 'bash install.sh --release v2.0.0-rc.1 --all', 'bash install.sh --release 2.0 --all')
replace_once(
    'install.sh',
    '''if [[ "$RELEASE" != "latest" ]]; then
  RELEASE="v${RELEASE#v}"
  [[ "$RELEASE" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+(-rc\\.[0-9]+)?$ ]] || {
    printf 'install.sh: release must use MAJOR.MINOR.PATCH, vMAJOR.MINOR.PATCH, or an -rc.N prerelease\\n' >&2
    exit 2
  }
fi
''',
    '''if [[ "$RELEASE" != "latest" ]]; then
  [[ "$RELEASE" =~ ^v?[0-9]+\\.[0-9]+(\\.[0-9]+)?(-rc\\.[0-9]+)?$ ]] || {
    printf 'install.sh: release must be an exact numeric tag such as 2.0, 2.0.1, or v2.0.1\\n' >&2
    exit 2
  }
fi
'''
)

for path in ['Git/gitx', 'PHP/phpx', 'Clean/cleanx', 'ChromaCat/chromacat']:
    replace_once(
        path,
        '    [[ "$release" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+(-rc\\.[0-9]+)?$ ]] || {',
        '    [[ "$release" =~ ^v?[0-9]+\\.[0-9]+(\\.[0-9]+)?(-rc\\.[0-9]+)?$ ]] || {'
    )

release = read('.github/workflows/release.yml')
release = release.replace("      - 'v*.*.*'", "      - '*.*'")
release = release.replace(
    '          if ! [[ "$tag" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+(-rc\\.[0-9]+)?$ ]]; then\n'
    '            echo "Release tag must use vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH-rc.N format: $tag" >&2\n',
    '          if ! [[ "$tag" =~ ^[0-9]+\\.[0-9]+$ ]]; then\n'
    '            echo "Stable Toolset release tags must use MAJOR.MINOR format (for example 2.0): $tag" >&2\n'
)
release = release.replace('          SUITE_VERSION="${RELEASE_TAG#v}"', '          SUITE_VERSION="$RELEASE_TAG"')
release = release.replace("          expected_version = os.environ['RELEASE_TAG'].removeprefix('v')", "          expected_version = os.environ['RELEASE_TAG']")
release = release.replace('          version="${GITHUB_REF_NAME#v}"', '          version="$GITHUB_REF_NAME"')
release = release.replace(
    '''          if [[ "$GITHUB_REF_NAME" == *-rc.* ]]; then
            args+=(--prerelease)
          fi

''',
    ''
)
write('.github/workflows/release.yml', release)

replace_once('tests/release-delivery.sh', 'TAG="v2.0.0-rc.999"', 'TAG="2.0"')

# ---------------------------------------------------------------------------
# Permanent CI: simulated exact-release delivery must pass before merge.
# ---------------------------------------------------------------------------
ci = read('.github/workflows/ci.yml')
anchor = '''  distribution:
    name: Standalone distribution artifacts
'''
release_job = '''  release_delivery:
    name: Simulated 2.0 release delivery
    runs-on: ubuntu-24.04
    timeout-minutes: 10

    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Verify exact 2.0 install/self-update delivery with transient retry
        run: bash tests/release-delivery.sh

'''
if release_job not in ci:
    ci = ci.replace(anchor, release_job + anchor, 1)
ci = ci.replace('      - distribution\n', '      - distribution\n      - release_delivery\n', 1)
ci = ci.replace('          DISTRIBUTION_RESULT: ${{ needs.distribution.result }}\n', '          DISTRIBUTION_RESULT: ${{ needs.distribution.result }}\n          RELEASE_DELIVERY_RESULT: ${{ needs.release_delivery.result }}\n', 1)
ci = ci.replace('            echo "| Distribution | $DISTRIBUTION_RESULT |"\n', '            echo "| Distribution | $DISTRIBUTION_RESULT |"\n            echo "| Simulated 2.0 release delivery | $RELEASE_DELIVERY_RESULT |"\n', 1)
ci = ci.replace('            "$DISTRIBUTION_RESULT"; do\n', '            "$DISTRIBUTION_RESULT" \\\n            "$RELEASE_DELIVERY_RESULT"; do\n', 1)
write('.github/workflows/ci.yml', ci)

# ---------------------------------------------------------------------------
# Public docs: exact stable tag is 2.0.
# ---------------------------------------------------------------------------
readmes = [
    'README.md', 'Git/README.md', 'PHP/README.md', 'Docker/README.md',
    'Network/README.md', 'Sqlite/README.md', 'Clean/README.md', 'ChromaCat/README.md'
]
for path in readmes:
    replace_all(path, 'v2.0.0-rc.1', '2.0')
    replace_all(path, 'v2.0.0', '2.0')
    replace_all(path, 'TOOLSET_SELF_UPDATE_RELEASE=vX.Y.Z[-rc.N]', 'TOOLSET_SELF_UPDATE_RELEASE=2.0')

replace_once(
    'README.md',
    'Release tags follow strict `vMAJOR.MINOR.PATCH` versioning. Published release assets are treated as immutable.',
    'Stable Toolset suite tags use `MAJOR.MINOR`; Toolset 2.0 is published from the immutable tag `2.0`.'
)
replace_once(
    'README.md',
    'Released consumers should pin an immutable release tag or commit SHA. Release candidates are GitHub prereleases used for acceptance/downstream integration; stable `vMAJOR.MINOR.PATCH` assets remain immutable.',
    'Released consumers should pin the immutable stable suite tag or commit SHA. For this release line the canonical stable tag is `2.0`; published assets are immutable.'
)

contracts = read('docs/cli-contracts.md')
contracts = contracts.replace(
    'Stable tags are immutable. Release candidates use prerelease tags and are intended for acceptance/downstream integration testing. Released downstream consumers should pin an exact tag or commit SHA rather than `main`.',
    'Stable suite tags are immutable. Toolset 2.0 uses the canonical tag `2.0`. Released downstream consumers should pin that exact tag or a commit SHA rather than `main`.'
)
write('docs/cli-contracts.md', contracts)

security = read('docs/security-review.md')
security = security.replace(
    'Release tags/assets are treated as immutable. Release candidates use explicit `-rc.N` prerelease tags so acceptance testing can exercise the same checksum/install/self-update path without becoming `releases/latest`.',
    'Release tags/assets are treated as immutable. Before merge, `tests/release-delivery.sh` exercises the exact `2.0` URL/install/self-update contract against local release assets with an injected transient curl failure. After merge, the maintainer creates tag `2.0`; the permanent release workflow then performs the live GitHub asset verification.'
)
security = security.replace(
    'Toolset 2.0/RC is security-ready only when all of the following remain green on the exact candidate source:',
    'Toolset 2.0 is pre-merge security/release-ready only when all of the following remain green on the exact candidate source:'
)
security = security.replace(
    '8. published RC asset download, checksum, installer and exact-release self-update verification.',
    '8. simulated exact-`2.0` asset download, checksum, installer and self-update verification, including transient transport retry. After the maintainer tags the merged commit `2.0`, the release workflow repeats these checks against the published GitHub assets.'
)
write('docs/security-review.md', security)

# ---------------------------------------------------------------------------
# Tracker: remove stale Phase 4/5/security state and distinguish pre/post merge.
# ---------------------------------------------------------------------------
tracker = read('docs/plans/toolset-2.0-progress-tracker.md')
tracker = tracker.replace(
    '**Phase 4 — Presentation Path**\n\nCurrent task: harden `chromacat`: preserve faithful non-TTY/plain pipeline output, tighten option/no-color/Unicode/TERM behavior, keep streaming bounded, and add golden pipeline/stream fixtures.',
    '**Release Readiness — final pre-merge gate**\n\nCurrent task: align the stable suite tag to `2.0`, pass simulated exact-release delivery/self-update verification, and leave PR #47 ready for maintainer merge. Merge and tag creation remain maintainer actions.'
)
tracker = tracker.replace('Suite release version comes from immutable `vMAJOR.MINOR.PATCH` Git tag.', 'Suite release version comes from the immutable stable suite tag; Toolset 2.0 uses `2.0`.')
tracker = tracker.replace('Strict `vMAJOR.MINOR.PATCH` tag validation.', 'Strict stable `MAJOR.MINOR` tag validation; Toolset 2.0 expects `2.0`.')
tracker = tracker.replace('Immutable semantic-tag release workflow builds/publishes versioned assets with checksums and manifest; actual `v2.0.0` publication remains intentionally deferred until the full hardening cycle is complete.', 'Immutable release workflow builds/publishes versioned assets with checksums and manifest; the maintainer will create stable tag `2.0` only after PR #47 is merged.')

phase4 = '''## Phase 4 — Presentation Path

### `chromacat`

- [x] Preserve faithful non-TTY/plain pipeline behavior.
- [x] Make unknown options fail clearly instead of implicit `cat` fallback.
- [x] Guarantee `--no-color` / `NO_COLOR` ANSI-free output.
- [x] Review Unicode display-width behavior; preserve content and document best-effort width without a heavy wcwidth dependency.
- [x] Keep streaming modes bounded and efficient.
- [x] Harden missing TERM/tput behavior.
- [x] Harden stable self-update through the release channel.
- [x] Add golden pipeline/no-color/stream tests.

### Phase 4 Gate

- [x] Pipeline, non-TTY, no-color and streaming tests pass in permanent CI.

## Phase 5 — Documentation, Release Readiness & Downstream Pins

- [x] Update root README to stable release installation model.
- [x] Normalize per-tool README sections.
- [x] Add dependency/capability matrix per tool in `docs/cli-contracts.md`.
- [x] Document destructive/security boundaries per tool.
- [x] Document output/exit contracts.
- [x] Verify docs against actual `--help` / `--version` in permanent CI.
- [x] Build deterministic release assets, `SHA256SUMS`, and `manifest.json` from the candidate source.
- [x] Add portable bounded retries to `install.sh` and all four built-in self-updaters.
- [x] Add permanent simulated exact-`2.0` release delivery/self-update test with an injected transient curl failure.
- [x] Select canonical stable Toolset suite tag: `2.0`.
- [ ] **Maintainer:** merge PR #47 into `main`.
- [ ] **Maintainer:** create/push tag `2.0` on the merged commit.
- [ ] Release workflow publishes `2.0` assets and verifies live checksums, install-all, and self-update paths.
- [ ] Update LocalDevStack/downstream Docker tracking to pin immutable Toolset tag `2.0` after that tag exists.

## Cross-Cutting Security Checklist

- [x] Review all `eval` occurrences; no internal user-controlled `eval` remains.
- [x] Review all `source` of writable/user-controlled config; writable settings/config are declarative rather than shell-sourced.
- [x] Review all fixed `/tmp` paths; sensitive/interactively generated state uses private temp/XDG paths.
- [x] Review all `rm -rf` / `find -delete` paths; retained recursive deletion is scoped/documented and `find -delete` is absent from runtime sources.
- [x] Review remote downloads/checksum policy; stable Toolset delivery is checksum-verified and bounded.
- [x] Review secret/environment output; Docker/Gemini/logging boundaries redact or require explicit opt-in.
- [x] Review quoting/path delimiter boundaries in high-impact file operations; ShellCheck plus tool-specific safety fixtures cover the retained paths and `--` is used where supported.
- [x] Review `bash -c` / `sh -c` command construction; retained fixed worker programs pass data positionally and interpolated command strings are blocked by CI.
- [x] Review mutable `main`/`master` URLs; stable Toolset install/self-update paths do not use mutable raw branches.
- [x] Review root/sudo assumptions; privilege is operation-specific and documented.
- [x] Review background processes/trap cleanup; retained bounded workers and cleanup traps are documented in `docs/security-review.md`.
'''
regex_once(
    'docs/plans/toolset-2.0-progress-tracker.md',
    r'## Phase 4 — Presentation Path\n.*?## Decisions Locked\n',
    phase4 + '\n## Decisions Locked\n'
)
tracker = read('docs/plans/toolset-2.0-progress-tracker.md')
tracker = tracker.replace('- [x] `dockex info` currently exposes raw container environment values; queued for Phase 2.', '- [x] `dockex info` formerly exposed raw container environment values; values are now redacted by default with explicit opt-in for raw output.')
tracker = tracker.replace('- [x] `dockex` backup/restore currently installs zip/unzip dynamically in an Alpine helper container; queued for Phase 2.', '- [x] `dockex` backup/restore moved from runtime zip/unzip installation to deterministic, scoped tar-based backup/restore.')
tracker = tracker.replace('- [x] `sqlitex` current backup is a raw file copy; queued for Phase 2.', '- [x] `sqlitex` raw file-copy backup was replaced by SQLite-native consistent backup with integrity coverage.')
tracker = tracker.replace('| 2026-09-16 | Started `phpx` Phase 2 capability and mutation-path hardening. | in progress |', '| 2026-09-16 | Completed `phpx`, `dockex`, and `sqlitex` Phase 2 hardening with permanent safety fixtures. | done |')
tracker = re.sub(
    r'## Next Task\n\n.*\Z',
    '## Next Task\n\nPass the final clean PR CI gate with the canonical `2.0` release contract and simulated release-delivery fixture. After that, the branch is ready for maintainer merge; the maintainer will tag the merged commit `2.0`, and only then will downstream repositories pin that immutable tag.\n',
    tracker,
    flags=re.S,
)
# Add latest work-log rows immediately after the table header.
marker = '| Date | Change | Status |\n|---|---|---|\n'
rows = (
    '| 2026-09-16 | Completed Phase 4 ChromaCat hardening and permanent presentation integration tests. | done |\n'
    '| 2026-09-16 | Completed Phase 5 docs/live-help governance and repository-wide security review. | done |\n'
    '| 2026-09-16 | Hardened release downloads with portable bounded retry after RC1 exposed a transient connection reset. | done |\n'
    '| 2026-09-16 | Aligned the intended post-merge stable suite tag and download path to `2.0`; added simulated exact-release delivery/self-update verification. | done |\n'
)
if rows not in tracker:
    tracker = tracker.replace(marker, marker + rows, 1)
write('docs/plans/toolset-2.0-progress-tracker.md', tracker)

# ---------------------------------------------------------------------------
# Governing plan: retain architecture, update release semantics/process.
# ---------------------------------------------------------------------------
plan = read('docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md')
plan = plan.replace('Recommended target: **Toolset 2.0.0**', 'Target release: **Toolset 2.0** (stable tag: `2.0`)')
plan = plan.replace(
    '''Use strict repository release tags going forward:

```text
v2.0.0
v2.0.1
v2.1.0
```

Keep historical tags unchanged.
''',
    '''Use immutable suite release tags. For this release line the canonical stable tag is:

```text
2.0
```

The maintainer creates the stable tag only after the hardening PR is merged. Historical tags remain unchanged. The installer may accept explicit historical numeric/v-prefixed tags for compatibility, but the Toolset 2.0 release workflow validates the stable `MAJOR.MINOR` suite-tag contract.
'''
)
plan = plan.replace('- publish only from semantic-version tags;', '- publish only from validated stable `MAJOR.MINOR` suite tags (Toolset 2.0 uses `2.0`);')
plan = plan.replace(
    '''### Phase 5 — Documentation & downstream pins

1. Update root/per-tool docs.
2. Publish 2.0 release candidate.
3. Verify release assets/checksums/self-update.
4. Give downstream Docker repos an immutable accepted Toolset ref.
5. Update LocalDevStack/docker ecosystem only after Toolset’s release contract is stable.
''',
    '''### Phase 5 — Documentation, release readiness & downstream pins

1. Update root/per-tool docs and verify them against live help/version output.
2. Build deterministic release assets and run simulated exact-`2.0` installer/self-update delivery, including transient transport retry, without publishing or tagging.
3. Pass the complete PR CI/security/distribution gate on the clean branch.
4. Maintainer merges PR #47 into `main`.
5. Maintainer creates/pushes stable tag `2.0` on the merged commit.
6. The permanent release workflow publishes the GitHub assets and repeats live checksum/install/self-update verification.
7. Only after tag `2.0` exists, update LocalDevStack/downstream Docker repositories to pin that immutable tag.
'''
)
# Replace acceptance section with explicit pre/post-merge boundary.
acceptance = '''## 17. Toolset 2.0 Acceptance Criteria

### Pre-merge release-readiness gate

PR #47 is ready for maintainer merge only when all of the following are true:

1. All seven CLIs pass `bash -n` and the agreed ShellCheck policy.
2. Every distributable CLI is committed executable.
3. Every CLI has working `--help` and `--version`.
4. Each tool remains independently installable as a single script.
5. Stable install paths use immutable releases or latest-stable release assets, not raw `main`.
6. Stable self-update verifies checksums, uses bounded transport retry, and performs atomic replacement.
7. CI covers representative Linux families and tool-specific smoke paths.
8. No unintentional `eval` remains around user-supplied values.
9. No predictable shared `/tmp` state remains for sensitive/interactively generated data.
10. `cleanx`, `dockex`, `phpx`, and `sqlitex` destructive operations have explicit safety tests.
11. `sqlitex` backup is SQLite-consistent and migrations are transactionally tracked where SQLite permits it.
12. `dockex` does not expose container environment secrets by default.
13. `netx` TLS/host handling is injection-safe and IPv6-tested.
14. `gitx` handles filenames safely and does not execute its settings file as arbitrary shell merely to load configuration.
15. `chromacat` has reliable no-color/non-TTY/stream behavior.
16. JSON modes emit valid machine-only stdout.
17. Distribution-specific capabilities fail/skip explicitly instead of making the whole standalone CLI unusable.
18. Root and per-tool documentation describe the behavior validated by tests.
19. The release snapshot contains all seven standalone scripts, `install.sh`, `SHA256SUMS`, and deterministic `manifest.json`.
20. `tests/release-delivery.sh` proves the exact stable tag/download contract for `2.0`, all-seven installation, the four built-in self-updaters, checksum identity, and recovery from an injected transient curl failure without publishing a tag.
21. The permanent release workflow is validated by `actionlint` and is configured to publish only the maintainer-created stable `MAJOR.MINOR` tag; Toolset 2.0 expects `2.0`.

### Post-merge release-completion gate

After the maintainer merges PR #47:

1. The maintainer creates/pushes tag `2.0` on the merged commit.
2. The permanent release workflow publishes all seven standalone scripts, `install.sh`, `SHA256SUMS`, and `manifest.json` from that exact tag.
3. The workflow verifies published checksums/manifest identity, exact-release installation of all seven tools, and exact-release self-update paths for `gitx`, `phpx`, `cleanx`, and `chromacat`.
4. LocalDevStack and released Docker consumers pin immutable Toolset tag `2.0` (or the tagged commit SHA), never `main`.

---
'''
regex_once(
    'docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md',
    r'## 17\. 2\.0 Acceptance Criteria\n.*?---\n\n## 18\.',
    acceptance + '\n## 18.'
)

# Ensure relationship/downstream wording reflects the selected stable tag.
plan = read('docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md')
plan = plan.replace('2. an immutable ref/release artifact;', '2. an immutable ref/release artifact (`2.0` after the maintainer tags the merged release);')
write('docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md', plan)

# Remove one-shot files from the resulting candidate commit.
Path('.github/scripts/sync-toolset-2.0-release-plan.py').unlink(missing_ok=True)
Path('.github/workflows/sync-toolset-2.0-release-plan.yml').unlink(missing_ok=True)
