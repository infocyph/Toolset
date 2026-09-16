# Toolset 2.0 CLI Contracts

Toolset is seven independent Linux Bash CLIs. Each distributed tool remains a single executable script and does not require a shared Toolset runtime.

## Common contract

- `--help` succeeds and describes the installed tool.
- `--version` succeeds and prints one canonical `<tool> <version>` line.
- Unknown options/commands fail non-zero with a diagnostic on stderr.
- Human ANSI decoration is suppressed for non-TTY output unless a tool exposes an explicit force-color path.
- `NO_COLOR` is honored by presentation/human-output paths.
- Machine-readable modes keep stdout reserved for the requested data; warnings/progress go to stderr.
- Stable installation and self-update use checksum-verified release assets. Mutable `main` is not a stable channel.
- Exit `0` means success. Any non-zero exit means the requested operation did not complete successfully. Tool-specific subcodes are not a cross-suite API unless that tool documents them explicitly.

## Dependency and capability matrix

| Tool | Required core | Optional capabilities | Elevated privilege | Primary mutation/security boundary |
|---|---|---|---|---|
| `gitx` | Bash, Git | `curl` + JSON tooling/network for Gemini AI; editor/pager as configured by Git | No for normal repository work | Mutates repositories; AI commit can transmit the staged textual diff only after staged-path safety checks. API-key persistence is explicit opt-in. |
| `phpx` | Bash; PHP only for commands that inspect/use PHP | `apt`/`dnf`, service manager, Composer/PECL/build tools depending on operation | Required only for package/service/system configuration mutation | Package, service and PHP configuration changes. Read-only/help/version paths do not require root. |
| `dockex` | Bash, Docker CLI/daemon | Docker features/backends available on the active daemon/context | Depends on Docker socket/context permissions | Container/image/volume lifecycle, cleanup, backup and restore. Environment values are redacted by default. |
| `netx` | Bash plus the command required by the selected subcommand | `ip`, `ss`, `dig`/`getent`, `curl`, `openssl`, `nft`/`iptables`, `tcpdump`, Docker, namespace tools | Only for capabilities such as packet capture/firewall/namespace operations | Network probing and optional privileged inspection. Security scoring is heuristic, not malware detection. |
| `sqlitex` | Bash, `sqlite3` | JSON/CSV/helper utilities when the selected operation needs them | No, unless the database/path itself requires it | Database mutation, migrations, reset, tuning and restore. Backup uses SQLite-native consistency paths. |
| `cleanx` | Bash and standard Linux filesystem/core utilities | Package-manager, journal/container/cache-specific commands when selected | System cleanup generally requires root; report/user-local paths may not | Destructive filesystem cleanup. Dry-run is the default; apply requires explicit approval. Secure erase is best-effort and not guaranteed on SSD/COW/snapshot storage. |
| `chromacat` | Bash, `awk` | `tput`, `figlet`, `chafa`/`jp2a`/`img2txt`; `curl` + SHA-256 tool for self-update | No, except writing to a privileged install prefix | Presentation only. Default non-TTY passthrough is byte-faithful; `--no-color`/`NO_COLOR` remove SGR styling. |

## Platform model

Toolset targets Linux. Generic functionality is capability-driven rather than tied to a package manager. Debian/Ubuntu, Fedora-family and Alpine-with-Bash are CI smoke targets, but feature availability still depends on the external commands and kernel capabilities used by the selected subcommand.

Unsupported capability-specific operations must fail or skip explicitly; they must not make unrelated commands unusable.

## Destructive and security boundaries

### `cleanx`

Dry-run remains the default. Actual deletion requires explicit approval/non-interactive opt-in. Target users and destructive roots are validated, recursive deletion uses argv-safe execution, and temporary/lock state is created privately. Overwrite-style secure erase cannot promise physical erasure on modern storage.

### `phpx`

Root is operation-specific. Package/service/config writes use explicit capability backends and validated/atomic configuration replacement where applicable. Logging is best-effort and must not make read-only commands fail.

### `dockex`

Cleanup and restore are explicit high-impact operations. Restore is scoped to the selected data target instead of blindly extracting into `/`. Live-data consistency limitations are surfaced. Raw container environment values are not printed by default.

### `sqlitex`

Backups use SQLite-native snapshot behavior. Migration SQL and migration tracking are paired transactionally where SQLite permits. Raw SQL/expression options remain intentionally powerful and are not a substitute for application-level parameterization.

### `netx`

TLS and guard execution use argv-safe boundaries. Network operations intended to be bounded have finite timeout defaults. Firewall inspection prefers nftables with iptables fallback. “Suspicious” listener/outbound output is heuristic evidence only.

### `gitx`

Interactive path handling is NUL-safe and temporary state is private. Gemini settings are declarative rather than sourced as shell. Credentials persist only by explicit opt-in. AI commit rejects sensitive-looking staged paths by default, avoids binary payloads and enforces request/response size and timeout bounds.

### `chromacat`

Presentation is secondary to text integrity. Default non-TTY use without a structural transform executes a raw cat-style path, preserving UTF-8, existing ANSI and exact trailing-newline state. `--cat` is an explicit byte-for-byte escape hatch. `--no-color`/`NO_COLOR` strip SGR color/blink/invert sequences.

Box alignment for Unicode is best-effort because terminal cell width depends on locale, combining characters and wcwidth behavior. Content is preserved even when perfect visual alignment cannot be guaranteed without adding a heavier runtime dependency.

## Output contract

| Output type | stdout | stderr |
|---|---|---|
| Human/read-only | Human result | Warnings/errors as appropriate |
| JSON/machine | Valid requested data only | Diagnostics/progress |
| Dry-run/preview | Planned actions/result according to tool help | Warnings/errors |
| `--version` | Exactly one `<tool> <version>` line | Empty |

Consumers should treat any undocumented human wording as non-stable. Automation should prefer structured modes and documented fields when available.

## Release and installation contract

A Toolset suite release publishes:

- `gitx`
- `phpx`
- `dockex`
- `netx`
- `sqlitex`
- `cleanx`
- `chromacat`
- `install.sh`
- `SHA256SUMS`
- `manifest.json`

Stable tags are immutable. Release candidates use prerelease tags and are intended for acceptance/downstream integration testing. Released downstream consumers should pin an exact tag or commit SHA rather than `main`.
