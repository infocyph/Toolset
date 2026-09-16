#!/usr/bin/env python3
from pathlib import Path

repo = Path('.')

TOOLS = {
    'gitx': {
        'script': 'Git/gitx', 'readme': 'Git/README.md',
        'purpose': 'Repository workflow, reporting, safe interactive Git operations and optional Gemini-assisted commit generation.',
        'requirements': 'Bash and Git. Gemini-backed commands additionally need network access, `curl`, a valid API key and the JSON helpers used by that command.',
        'platform': 'Generic Linux Git workflows are distro-independent. Editor/pager and optional AI behavior follow the capabilities available on the host.',
        'quick': 'gitx status\ngitx summary HEAD~20\ngitx doctor',
        'security': 'Repository-changing commands mutate the current Git repository. Interactive path handling is NUL-safe. Gemini settings are declarative, API-key persistence is explicit opt-in, sensitive-looking staged paths are rejected by default, and AI requests are timeout/size bounded.',
        'examples': 'gitx commit\ngitx worklog HEAD~20..HEAD\ngitx ai-commit',
    },
    'phpx': {
        'script': 'PHP/phpx', 'readme': 'PHP/README.md',
        'purpose': 'PHP runtime/package/extension/service/configuration management plus diagnostics and tuning.',
        'requirements': 'Bash. Individual commands require only their own capabilities: PHP for runtime inspection, package-manager/service tools for system mutation, and Composer/PECL/build tools where applicable.',
        'platform': 'Generic PHP inspection is capability-based. Package mutation has explicit backends; unsupported package/service operations fail clearly instead of disabling unrelated commands.',
        'quick': 'phpx doctor\nphpx --help\nphpx --version',
        'security': 'Root is operation-specific. Package, service and system configuration changes are high-impact. Generated configuration is validated/atomically replaced where supported, and logging is best-effort/secret-safe.',
        'examples': 'phpx doctor\nphpx --help',
    },
    'dockex': {
        'script': 'Docker/dockex', 'readme': 'Docker/README.md',
        'purpose': 'Docker inspection, lifecycle helpers, resource updates, cleanup, benchmarking and deterministic backup/restore.',
        'requirements': 'Bash and the Docker CLI connected to a usable daemon/context. Optional commands require the capabilities they invoke.',
        'platform': 'Linux with Docker. Rootless and non-default Docker contexts are detected; access depends on the active Docker endpoint permissions.',
        'quick': 'dockex info\ndockex --help\ndockex --version',
        'security': 'Cleanup and restore are explicit high-impact operations. Environment values are redacted by default. Restore is scoped to the selected mount/volume and live-data consistency limitations are surfaced.',
        'examples': 'dockex info\ndockex --help',
    },
    'netx': {
        'script': 'Network/netx', 'readme': 'Network/README.md',
        'purpose': 'Capability-driven Linux networking diagnostics covering endpoints, DNS, TLS, HTTP, routes, firewall inspection, capture and security-oriented guards.',
        'requirements': 'Bash plus only the dependency needed by the selected subcommand, such as `ip`, `ss`, `dig`/`getent`, `curl`, `openssl`, `nft`/`iptables` or `tcpdump`.',
        'platform': 'Generic Linux. Privileged firewall/capture/namespace features are capability-gated; nftables is preferred with iptables fallback where applicable.',
        'quick': 'netx --help\nnetx ip info\nnetx route show',
        'security': 'TLS and guard execution are argv-safe, bounded network operations have finite timeout defaults, JSON paths are validated, and suspicious scoring is heuristic evidence rather than authoritative malware detection.',
        'examples': 'netx route explain 127.0.0.1\nnetx --json route explain 127.0.0.1',
    },
    'sqlitex': {
        'script': 'Sqlite/sqlitex', 'readme': 'Sqlite/README.md',
        'purpose': 'SQLite administration, queries, migrations, seeds, import/export, backup/restore and tuning.',
        'requirements': 'Bash and `sqlite3`; import/export helpers may require additional utilities documented by the selected command.',
        'platform': 'Generic Linux anywhere Bash and SQLite are available. Database/path permissions determine whether elevation is required.',
        'quick': 'sqlitex --help\nsqlitex --version',
        'security': 'Database mutation is explicit. Backups use SQLite-native consistent snapshots, migration SQL/tracking are transactional where SQLite permits, identifiers are validated/quoted, and raw SQL/expression options remain intentionally powerful.',
        'examples': 'sqlitex --help',
    },
    'cleanx': {
        'script': 'Clean/cleanx', 'readme': 'Clean/README.md',
        'purpose': 'Safe modular disk/inode cleanup with reporting, quota controls and explicit application of destructive actions.',
        'requirements': 'Bash and standard Linux filesystem/core utilities. Package/journal/container/cache cleanup commands are capability-gated.',
        'platform': 'Generic Linux for filesystem/report functions, with explicit package-manager and service-specific capabilities where available.',
        'quick': 'cleanx --report\ncleanx --report --json\ncleanx --help',
        'security': 'Dry-run is the default; actual deletion requires explicit approval. Delete roots and target users are validated, config is declarative, locking is private/atomic, and overwrite-style secure erase is not guaranteed on SSD/COW/snapshot storage.',
        'examples': 'cleanx --report\nsudo cleanx --yes logs tmp',
    },
    'chromacat': {
        'script': 'ChromaCat/chromacat', 'readme': 'ChromaCat/README.md',
        'purpose': 'Pipeline-safe terminal presentation with colouring, themes, matching, boxes, headers, streaming and optional ASCII-art rendering.',
        'requirements': 'Bash and `awk`. `tput`, `figlet`, `chafa`/`jp2a`/`img2txt` and release-update tools are optional and checked only for the feature that uses them.',
        'platform': 'Generic Linux. Plain text does not depend on TERM/tput. Non-TTY output is unstyled unless `--force` is explicitly requested.',
        'quick': 'printf "hello\\n" | chromacat\nprintf "hello\\n" | chromacat --force -T neon\ntail -f app.log | chromacat --log',
        'security': 'Presentation-only. Default non-TTY passthrough is byte-faithful; `--cat` is an explicit raw escape hatch; unknown options fail; `--no-color`/`NO_COLOR` remove SGR colour/blink/invert sequences. Unicode box width is best-effort because exact terminal cell width is locale/wcwidth dependent.',
        'examples': 'printf "hello\\n" | chromacat --no-color\nprintf "hello\\n" | chromacat --box --center --no-color',
    },
}

START = '<!-- TOOLSET2-CONTRACT:START -->'
END = '<!-- TOOLSET2-CONTRACT:END -->'

for name, meta in TOOLS.items():
    p = Path(meta['readme'])
    original = p.read_text()
    install = f'''## Install

Latest stable (checksum-verifying installer):

```bash
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh"
bash install.sh {name}
```

Exact reproducible release:

```bash
bash install.sh --release v2.0.0 {name}
```
'''
    block = f'''{START}
## Purpose

{meta['purpose']}

{install}
## Requirements

{meta['requirements']}

## Supported platforms/capabilities

{meta['platform']}

See [`../docs/cli-contracts.md`](../docs/cli-contracts.md) for the suite capability matrix.

## Quick start

```bash
{meta['quick']}
```

## Command reference

`{name} --help` is the authoritative live command reference. `{name} --version` prints the installed tool version. The detailed reference below expands on command-specific behavior.

## Destructive/security behavior

{meta['security']}

## Exit/output contract

Exit `0` means success; non-zero means the requested operation did not complete successfully. Machine-readable modes reserve stdout for data and send diagnostics to stderr. Do not parse undocumented human wording as a stable API.

## Self-update

Where `{name}` exposes self-update, the stable channel uses checksum-verified GitHub release assets. `TOOLSET_SELF_UPDATE_RELEASE=vX.Y.Z[-rc.N]` may pin an exact release for acceptance/rollback verification; mutable `main` is never the stable default. If the tool does not expose self-update, reinstall through the release installer.

## Examples

```bash
{meta['examples']}
```
{END}
'''
    if START in original and END in original:
        before, rest = original.split(START, 1)
        _, after = rest.split(END, 1)
        updated = before.rstrip() + '\n\n' + block + after
    else:
        lines = original.splitlines(True)
        if lines and lines[0].startswith('# '):
            updated = lines[0].rstrip() + '\n\n' + block + '\n' + ''.join(lines[1:]).lstrip()
        else:
            updated = block + '\n' + original
    p.write_text(updated)

# Add exact-release override to the four self-update-capable tools. This keeps
# default behavior unchanged while allowing a published RC to exercise the same
# updater path reproducibly.
for file in ('Git/gitx', 'PHP/phpx', 'Clean/cleanx', 'ChromaCat/chromacat'):
    p = Path(file)
    t = p.read_text()
    old = '''  local current_path prefix tmp_dir checksum_line
  local base="https://github.com/infocyph/Toolset/releases/latest/download"
'''
    new = '''  local current_path prefix tmp_dir checksum_line
  local release="${TOOLSET_SELF_UPDATE_RELEASE:-latest}"
  local base
  local -a install_args

  if [[ "$release" == "latest" || "$release" == "stable" ]]; then
    base="https://github.com/infocyph/Toolset/releases/latest/download"
    install_args=(--latest)
  else
    [[ "$release" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+(-rc\\.[0-9]+)?$ ]] || {
      printf '%s: invalid TOOLSET_SELF_UPDATE_RELEASE: %s\\n' "$tool" "$release" >&2
      return 2
    }
    base="https://github.com/infocyph/Toolset/releases/download/$release"
    install_args=(--release "$release")
  fi
'''
    if old not in t:
        raise SystemExit(f'missing self-update base anchor in {file}')
    t = t.replace(old, new, 1)
    old_install = '  bash "$tmp_dir/install.sh" --latest --prefix "$prefix" "$tool"\n'
    new_install = '  bash "$tmp_dir/install.sh" "${install_args[@]}" --prefix "$prefix" "$tool"\n'
    if old_install not in t:
        raise SystemExit(f'missing self-update installer anchor in {file}')
    t = t.replace(old_install, new_install, 1)
    t = t.replace('checksum is missing from latest stable release.', 'checksum is missing from the selected release.', 1)
    p.write_text(t)

# Root README: retain detailed installation content and add the acceptance-facing
# support/security/release contract links.
p = Path('README.md')
t = p.read_text()
root_start = '<!-- TOOLSET2-ROOT-CONTRACT:START -->'
root_end = '<!-- TOOLSET2-ROOT-CONTRACT:END -->'
root_block = '''<!-- TOOLSET2-ROOT-CONTRACT:START -->
## Support, Safety & Automation Contracts

- [CLI dependency/capability, security and output contracts](docs/cli-contracts.md)
- [Toolset 2.0 implementation plan](docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md)
- [Live 2.0 implementation tracker](docs/plans/toolset-2.0-progress-tracker.md)
- [2.0 security review](docs/security-review.md)

Toolset targets Linux with capability-gated features rather than claiming identical behavior on every distribution. CI smoke-covers Debian 13, Ubuntu 24.04, Fedora 42 and Alpine 3.22 with Bash. High-impact operations remain tool-specific and are documented in each tool README and the suite contract.

Released consumers should pin an immutable release tag or commit SHA. Release candidates are GitHub prereleases used for acceptance/downstream integration; stable `vMAJOR.MINOR.PATCH` assets remain immutable.
<!-- TOOLSET2-ROOT-CONTRACT:END -->'''
if root_start in t and root_end in t:
    before, rest = t.split(root_start, 1)
    _, after = rest.split(root_end, 1)
    t = before.rstrip() + '\n\n' + root_block + after
else:
    marker = '\n---\n\n## Development Builds'
    if marker not in t:
        raise SystemExit('root README insertion anchor missing')
    t = t.replace(marker, '\n\n' + root_block + marker, 1)
p.write_text(t)
