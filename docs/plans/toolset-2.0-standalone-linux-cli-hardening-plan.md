# Toolset 2.0 — Standalone Linux CLI Hardening & Release Plan

## Status

Planning branch: `plan/toolset-linux-cli-hardening`

Baseline branch: `main`

Baseline commit reviewed: `6e93735e344ea0e63bd643550ae86181611f694b`

Recommended target: **Toolset 2.0.0**

This is a repository-wide hardening plan for Toolset itself. Toolset is **not** a Docker support library: every utility remains an independently installable Linux CLI. Docker images, LocalDevStack, and other Infocyph repositories are downstream consumers only.

---

## 1. Product Contract

Toolset is a collection of standalone Bash CLIs:

- `gitx`
- `phpx`
- `dockex`
- `netx`
- `sqlitex`
- `cleanx`
- `chromacat`

### Non-negotiable design rules

1. **Each tool remains independently installable.**
   - Installing `gitx` must not require the rest of Toolset.
   - Installing `netx` must not require `chromacat`.
   - No runtime shared shell library may become mandatory across tools.

2. **Single-file distribution remains supported.**
   - Repository internals may gain test fixtures, release tooling, or build metadata.
   - The installed runtime artifact for each tool remains a single executable Bash script unless a future tool explicitly requires otherwise.

3. **Linux host usage is primary.**
   - Docker/container usage is a supported downstream environment, not the architecture driver.
   - Generic commands should work on any reasonable Linux distribution when their external dependencies are present.
   - Distribution-specific operations must be capability-gated and clearly reported.

4. **No hidden destructive behavior.**
   - Deletion, reset, restore, cleanup, package removal, firewall modification, and similar operations must be previewable and explicitly confirmed or explicitly opted into for non-interactive use.

5. **No secret leakage by default.**
   - Environment variables, API keys, auth data, Docker environment values, URLs containing credentials, and similar information must be redacted unless the user explicitly requests raw values.

6. **Machine-readable output must actually be machine-readable.**
   - JSON modes must emit valid JSON only on stdout.
   - Human diagnostics, progress text, and warnings go to stderr when JSON output is selected.
   - ANSI styling must never leak into JSON/plain machine output.

7. **Released code is immutable.**
   - Stable install and self-update paths resolve to release assets/tags, not mutable `main`.
   - Development-channel update from `main` may exist only as an explicit opt-in.

8. **Downstream consumers pin Toolset.**
   - Docker images and other repositories use a release tag or commit SHA.
   - Toolset does not change its standalone design to accommodate one downstream stack.

---

## 2. Current Repository Inventory

Current executable sources:

| Tool | Path | Current observed script version | Current git mode | Risk class |
|---|---|---:|---:|---|
| `gitx` | `Git/gitx` | no unified embedded release version | executable | high — repository mutation + optional AI credential |
| `phpx` | `PHP/phpx` | no unified embedded release version | executable | critical — root/package/service/config mutation |
| `dockex` | `Docker/dockex` | no unified embedded release version | executable | critical — Docker lifecycle/restore/cleanup |
| `netx` | `Network/netx` | `0.4.0` | executable | high — network/security/privileged operations |
| `sqlitex` | `Sqlite/sqlitex` | no unified embedded release version | **non-executable** | critical — database mutation/backup/migrations |
| `cleanx` | `Clean/cleanx` | `1.7.0` | **non-executable** | critical — root filesystem cleanup |
| `chromacat` | `ChromaCat/chromacat` | `1.3` | executable | low — presentation/stream processing |

Repository release state at review time:

- latest GitHub release: `1.06.3`;
- per-script version values do not map cleanly to repository release tags;
- installation documentation points directly at mutable `main`;
- some self-updaters also fetch mutable `main`;
- `.github/` contains `CODEOWNERS` but no validation workflow;
- no repository test suite currently gates the seven shell CLIs.

The first 2.0 objective is therefore to establish a reliable suite/release contract before growing functionality.

---

## 3. Cross-Cutting Foundation Work

### 3.1 Add a real validation spine

Create:

```text
.github/workflows/ci.yml
.github/workflows/release.yml
tests/
  lib/
  gitx/
  phpx/
  dockex/
  netx/
  sqlitex/
  cleanx/
  chromacat/
```

CI must run at minimum:

- `bash -n` against every executable script;
- ShellCheck against every executable script;
- executable-bit verification for all distributable CLI files;
- `--help` smoke test;
- `--version` smoke test once standardized;
- non-TTY execution tests;
- no-color/plain-output tests where relevant;
- temporary-HOME tests;
- failure-path tests with optional dependencies absent;
- focused functional smoke tests per tool;
- documentation/reference consistency checks for tool names and install paths.

Use current first-party GitHub Actions majors when implemented. At planning time the current official baseline includes `actions/checkout@v7`, while artifact workflows have moved beyond older v4-era examples. Re-check action majors at implementation time rather than copying stale workflow snippets.

### 3.2 Keep tests lightweight

Prefer a small Bash test harness over adding a runtime framework dependency.

A test helper may provide:

- `assert_eq`;
- `assert_contains`;
- `assert_status`;
- temporary directory creation/cleanup;
- disposable HOME;
- command stubs/mocks through a temporary PATH.

Bats may be used only if it materially improves maintainability; it must remain a development/CI dependency and must never become a runtime dependency of any Toolset command.

### 3.3 Standardize common CLI behavior without creating runtime coupling

Every tool should independently implement the same public conventions:

- `-h`, `--help` → success exit (`0`);
- `-V`, `--version` → success exit (`0`);
- unknown command/option → concise error on stderr and non-zero exit;
- `NO_COLOR` support for human output;
- do not emit ANSI when stdout is not a TTY unless an explicit force-color flag exists;
- `--yes`/`--force` semantics clearly separated;
- `--dry-run` for destructive tools where meaningful;
- `--quiet` where meaningful;
- stable exit-code categories documented for automation-sensitive commands.

Do **not** solve this by sourcing a shared runtime helper from another file. Independence is more important than eliminating a few repeated shell helpers.

### 3.4 Eliminate unsafe temporary-file patterns

Replace predictable files such as `/tmp/git_log.txt`, `/tmp/git_status.txt`, and fixed updater paths with `mktemp`/`mktemp -d` plus `trap` cleanup.

Rules:

- never follow an attacker-controlled symlink in a shared temp directory;
- create sensitive temp files with restrictive permissions;
- clean temporary artifacts on normal exit and signals;
- never reuse global filenames across concurrent invocations.

### 3.5 Remove avoidable `eval`

Current code contains command-string `eval` paths, including Git reporting helpers and TLS execution in `netx`.

Policy:

- build command arguments as Bash arrays;
- execute arrays directly;
- use `--` delimiters when a downstream CLI supports them;
- only retain shell evaluation for a feature whose explicit purpose is to execute user-provided shell code;
- such a feature must be named/documented as arbitrary code execution and isolated from internal argument construction.

### 3.6 Separate human output from data output

For tools offering JSON or script-oriented output:

- stdout = requested data;
- stderr = warnings/progress;
- no emoji/ANSI in JSON;
- valid JSON even for empty results and failures where JSON error output is part of the contract;
- never mix headers/table decoration into structured output.

### 3.7 Define dependency capability checks

Each command should check only dependencies needed by that command.

Do not fail the entire CLI at startup because an optional utility for an unrelated command is absent.

Each README should contain a compact dependency matrix:

- required core commands;
- optional commands;
- command(s) enabled by each optional dependency;
- whether root/capability is required.

### 3.8 Distribution support tiers

Toolset should distinguish **standalone portability** from **identical feature availability**.

Recommended support model:

- **Generic Linux core:** Bash + required command dependencies. `gitx`, `chromacat`, much of `netx`, `sqlitex`, and Docker-facing `dockex` should work independent of distro package manager.
- **Capability-gated Linux features:** firewall, namespace, packet capture, service management, package cleanup, etc. run only when the host exposes the required utility/capability.
- **Package-manager backends:** use explicit adapters where a tool manages system packages.

Do not claim a distro is fully supported when a major command silently assumes `apt`, systemd, or Debian filesystem layout.

---

## 4. Versioning, Installation, Self-Update & Supply Chain

### 4.1 Normalize release semantics

Use strict repository release tags going forward:

```text
v2.0.0
v2.0.1
v2.1.0
```

Keep historical tags unchanged.

Toolset 2.0 should define two levels of version identity:

1. **Suite release** — GitHub tag identifying an immutable repository snapshot.
2. **Tool version** — embedded in each standalone script and returned by `--version`.

The release manifest records both, so independently evolving tools do not need fake version changes just because another Toolset script changed.

Suggested generated release manifest:

```text
manifest.json
SHA256SUMS
```

`manifest.json` should contain for every tool:

- tool name;
- repository path;
- embedded tool version;
- suite release tag;
- SHA-256 digest;
- minimum Bash version if one is intentionally required.

### 4.2 Publish standalone release assets

`release.yml` should package the seven scripts directly as release assets:

```text
gitx
phpx
dockex
netx
sqlitex
cleanx
chromacat
SHA256SUMS
manifest.json
```

Release workflow rules:

- validate first;
- build assets only from the tagged commit;
- generate SHA-256 values in CI;
- fail if embedded metadata is invalid;
- publish only from semantic-version tags;
- release tags are treated as immutable;
- minimum `GITHUB_TOKEN` permissions by default, elevating to `contents: write` only in the release job;
- no scheduled job rewrites a release tag or release asset.

### 4.3 Installation contract

Documentation should show two modes.

**Reproducible install (recommended):** exact release version + checksum verification.

**Latest stable install (convenience):** GitHub `releases/latest/download/<tool>`.

Do not present raw `main` as the normal installation command.

An optional root-level installer may be added:

```text
install.sh
```

It may install one or more selected tools, but it must remain optional. Direct installation of a single release asset continues to work.

Installer requirements:

- download to temp;
- verify checksum;
- validate Bash syntax before installation;
- install atomically;
- support `--prefix` / user-local bin path;
- preserve existing installation as a rollback backup when replacing;
- never require `sudo` when target path is user-writable.

### 4.4 Self-update contract

Where self-update is supported:

- default channel = latest stable GitHub release;
- download release asset to a secure temp path;
- fetch/verify checksum;
- run `bash -n` on downloaded script;
- confirm tool identity/version;
- atomically replace current executable;
- preserve executable mode and ownership where possible;
- keep a rollback copy;
- do not hard-code `/usr/local/bin/<tool>` when the running executable is elsewhere;
- do not require root solely because the tool *might* have been system-installed;
- `--channel main` or equivalent development update is explicit opt-in and must be labeled non-reproducible.

### 4.5 Downstream immutable refs

The Docker ecosystem plan requires immutable Toolset consumption. Toolset should make that easy, but no Docker-specific behavior belongs in Toolset itself.

Downstream images should consume either:

```text
https://raw.githubusercontent.com/infocyph/Toolset/<tag-or-sha>/<path>
```

or an exact-version release asset.

Consumers must not use `Toolset/main/...` for released images.

---

## 5. `gitx` Plan

`gitx` is one of the largest scripts and mixes read-only reporting, destructive repository operations, interactive flows, release helpers, and optional Gemini-backed commit generation.

### 5.1 File/path safety

Fix all interactive file selection so filenames with spaces, tabs, leading dashes, renames, or unusual characters remain correct.

Current line-oriented patterns such as parsing `git status -s` with `awk '{print $2}'` are not sufficient.

Target:

- use Git NUL-delimited output (`-z`) where available;
- store selections in Bash arrays;
- pass paths after `--`;
- never rely on whitespace tokenization for paths.

### 5.2 Secure temporary state

Replace fixed `/tmp/git_log.txt`, `/tmp/git_status.txt`, and similar paths with secure temp files/directories.

### 5.3 Remove internal `eval`

Large-file/report commands should execute pipelines directly or through explicit functions instead of constructing a shell command string and evaluating it.

### 5.4 Branch/remote handling

Keep automatic main-branch detection, but remove hidden assumptions where possible.

Add/standardize:

- remote selection (`--remote`, default `origin` when present);
- main branch discovery from remote HEAD, then `main`, then `master` fallback;
- clear behavior for repositories without remotes;
- detached-HEAD handling;
- worktree awareness for branch deletion/cleanup;
- protected branch set (`main`, `master`, current branch, configured branches);
- no destructive branch deletion without preview/confirmation unless explicit non-interactive flag is provided.

`sync alpha/develop` should remain an opinionated command, but should skip nonexistent branches cleanly rather than making those branch names a repository-wide assumption.

### 5.5 Commit/cherry-pick/revert flows

- validate numeric menu input;
- preserve commit ordering intentionally;
- handle merge commits explicitly;
- print recovery commands on conflict (`--continue`, `--abort`);
- do not leave temp menu state behind;
- use return codes instead of deep `exit` from reusable helper functions where practical.

### 5.6 Reporting correctness

Add fixtures for:

- root commit ranges;
- one-commit ranges;
- date windows;
- merge commits;
- renamed files;
- authors with same name/different email;
- binary files;
- shallow clones;
- repositories with no tags;
- repositories with no upstream.

Validate `worklog`, `summary`, `report`, `commit-report`, `changelog`, `diff`, and change counters against known fixture repositories.

### 5.7 AI commit remains optional and standalone

Do **not** make `gitx` depend on `docker-llm-sm`, Ollama, LocalDevStack, or any other Toolset command.

Current Gemini support may remain, but harden it:

- environment variable is the preferred API-key source;
- do not persist API keys by default;
- if explicit key persistence is retained, use a dedicated command/flag and `0600` permissions;
- stop `source`-executing the settings file merely to read key/value data;
- parse a constrained config format instead;
- set API request timeouts;
- validate HTTP status and JSON response shape;
- cap staged diff payload size;
- detect likely secret files/binary data and exclude or require confirmation;
- sanitize model/API errors so credentials cannot appear in output;
- provide deterministic fallback/manual flow when AI is unavailable.

A future generic provider interface may be added, but it must remain optional and must not create a runtime dependency on a local LLM product.

### 5.8 Self-update

Move from raw `main` to the shared stable release/update contract.

---

## 6. `phpx` Plan

`phpx` is currently documented as Debian/Ubuntu-oriented and performs package, repository, service, FPM, Apache, config, PECL, and Composer operations. It must remain independently useful on Linux without pretending every distro supports the same package lifecycle.

### 6.1 Split generic PHP capability from distro package management

Internally organize behavior into capabilities:

- PHP binary discovery;
- PHP version inspection;
- syntax linting;
- built-in server;
- script execution;
- extension inspection;
- config inspection/generation;
- FPM detection;
- package-manager operations;
- service-manager operations;
- repository setup.

Generic commands should work whenever the needed PHP binary exists, even on a distro where automated PHP package installation is unsupported.

### 6.2 Package-manager backends

Preserve Debian/Ubuntu as the strongest backend, but make the boundary explicit.

Implement capability adapters in this order:

1. `apt`/`dpkg` — full existing feature set;
2. `dnf`/`rpm` — common Fedora/RHEL-family operations where reliable;
3. `pacman` — supported operations only;
4. `apk` — supported operations only.

Do not promise parallel multi-version switching on a distro whose native packaging does not support it cleanly. Report unsupported operations precisely while leaving generic `phpx` commands functional.

### 6.3 Service-manager support

Do not assume systemd for every Linux host.

- systemd backend where available;
- OpenRC detection where practical;
- otherwise show exact manual action instead of failing unrelated PHP operations.

### 6.4 Repository/key setup hardening

For Sury/Ondřej setup:

- use current official repository/keyring procedure;
- download to `mktemp` path;
- validate download before `dpkg -i`;
- remove temporary package afterward;
- do not leave stale repo/key files from failed setup;
- make repository changes idempotent;
- report exactly which files were created/modified.

### 6.5 Composer behavior

Do not automatically turn a reproducible `install composer` action into an unconditional upgrade to unknown future `latest`.

Provide explicit semantics such as:

- `phpx install composer` → install stable if absent;
- `phpx composer update` / explicit update flag → update;
- optional version/channel input when requested.

Verify Composer installer signatures/checksums using the official supported mechanism.

### 6.6 PECL/source extension safety

- validate extension/package names;
- isolate build temp directories;
- clean build dependencies only when Toolset installed them and only when safe;
- avoid deleting user-managed packages/config;
- validate resulting extension with the intended PHP binary;
- do not enable an extension globally until load validation succeeds;
- support rollback of newly generated `.ini` changes on failure.

### 6.7 Config generation

- write to temp then atomically replace;
- back up existing config;
- validate generated PHP config before committing it;
- validate FPM config (`php-fpm -t`/equivalent) where available;
- avoid overwriting unrelated pool files;
- keep environment presets documented and deterministic.

### 6.8 Logging

- logging failure must not prevent read-only commands from running;
- keep user-local logs user-owned;
- avoid logging credentials, full URLs containing auth, or sensitive environment values;
- add log retention guidance rather than silently growing one log per day forever.

### 6.9 Root semantics

Root should be required per operation, not globally.

Self-update should update the actual executable path and require privilege only when that path is not writable.

### 6.10 Self-update

Replace raw `main` updater with stable release asset + checksum verification.

---

## 7. `dockex` Plan

`dockex` performs both inspection and high-impact Docker mutations. Its 2.0 contract should make the safe path obvious.

### 7.1 Dependency and daemon checks

- require Docker only when executing Docker commands;
- make `jq` requirement explicit for commands that parse inspect JSON;
- detect daemon/context connection failure separately from “container not found”;
- work with rootless Docker and non-default Docker contexts;
- do not assume direct access to `/var/run/docker.sock`.

### 7.2 Container identification

Use Docker inspect/filter APIs instead of `docker ps | grep -w` when possible.

Names containing regex-sensitive characters must not affect matching.

### 7.3 Secret redaction

`dockex info` currently prints container environment values. Change default behavior:

- show variable names with values redacted;
- optionally identify likely secret variables (`*_PASSWORD`, `*_TOKEN`, `*_KEY`, auth URLs) without printing values;
- require explicit `--show-env-values` to reveal raw values;
- document the security implication.

### 7.4 Backup/restore redesign

Current flow creates ZIP archives through a temporary `alpine` container and installs packages at runtime. Replace this with a deterministic archive strategy.

Requirements:

- prefer `tar` so no package installation/network access is needed in the helper container;
- pin any helper image used by release policy or allow configurable helper image;
- preserve uid/gid, mode, symlinks, timestamps where possible;
- record metadata: source container, mount destination, volume/bind identity, timestamp;
- distinguish named volumes from bind mounts;
- warn that live database/filesystem backup may be inconsistent;
- offer an explicit quiesce/stop mode rather than silently stopping containers;
- validate archive paths before restore;
- restore only to the selected mount/volume root, never blindly extract an untrusted archive to `/`;
- preview restore target and require confirmation unless explicit non-interactive approval is provided;
- test filenames with spaces, symlinks, ownership, and nested paths.

### 7.5 Cleanup safety

For `cleanup unused|aggressive|all`:

- show exactly what class of objects will be removed;
- `unused` remains conservative;
- aggressive/all require explicit confirmation;
- non-interactive destructive mode requires `--yes` plus the requested mode;
- `all` should require an additional unmistakable confirmation token or `--force-all`;
- never remove default Docker networks;
- report reclaimed space from Docker output.

### 7.6 Resource updates

Validate CPU/memory inputs before calling Docker.

Handle cgroup/rootless limitations as capability errors, not malformed Docker calls.

### 7.7 Benchmark/stat commands

- clearly separate host-side and container-side dependencies;
- do not silently install benchmark tools into the target application container;
- use bounded timeouts;
- return meaningful non-zero status when target is unreachable;
- provide machine-readable summary option if retained.

### 7.8 Command naming compatibility

Prefer hyphenated public command names (`stream-logs`, `update-resources`) while retaining existing underscore aliases during 2.0 migration if compatibility is desired.

---

## 8. `netx` Plan

`netx` is broad and security-sensitive. Its current TLS helper constructs shell command strings and evaluates them; this must be fixed before treating it as hardened.

### 8.1 Remove TLS command injection paths

Replace constructs equivalent to:

```bash
cmd="openssl s_client ... $host ..."
eval "$cmd"
```

with arrays/direct argument execution.

User-supplied hostnames, ports, filenames, interface names, and BPF arguments must never become shell syntax accidentally.

### 8.2 Redesign `guard --exec`

Executing a user hook is intentionally arbitrary code execution, so make that contract explicit.

Preferred design:

- `--exec <executable>` plus arguments after `--`, executed as an argv array; or
- a clearly named `--exec-shell '<command>'` for users who intentionally want shell evaluation.

Feed event data through stdin or defined environment variables. Do not use `eval` for ordinary hook execution.

### 8.3 IPv4/IPv6 endpoint parsing

Current host/port splitting logic must be reviewed for IPv6.

Add tested helpers for:

- IPv4 address + port;
- hostname + port;
- `[IPv6]:port`;
- bare IPv6;
- wildcard/listening addresses;
- Unix sockets where surfaced by `ss`.

Security scoring must not perform arithmetic on an unvalidated/non-numeric port.

### 8.4 Private/public classification

Replace fragile prefix heuristics with well-tested CIDR handling for:

- RFC1918;
- loopback;
- link-local;
- IPv6 ULA;
- IPv6 link-local;
- unspecified/multicast where relevant.

Keep dependency footprint low; implement tested helpers or use an optional known system utility when present.

### 8.5 Avoid startup side effects

Do not create `$HOME/.netx` merely to run `netx --help` or a stateless read-only command.

Create state directories only for commands that persist snapshots/records.

Follow XDG paths where practical:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/netx
${XDG_CONFIG_HOME:-$HOME/.config}/netx
```

### 8.6 Privileged features

Packet capture, namespace operations, firewall inspection, DNS cache flushing, and process metadata may require root/capabilities.

- detect required capability per command;
- never auto-sudo;
- explain the exact missing privilege/tool;
- preserve read-only fallback when possible.

### 8.7 Timeouts

Every network operation that can block must have a finite default timeout or an explicit documented streaming mode.

This includes:

- DNS queries;
- TLS handshakes;
- HTTP probes;
- port checks;
- route/path tools;
- public-IP lookup;
- Docker-assisted inspection where applicable.

### 8.8 JSON correctness

Audit every `--json` path. Add golden tests proving:

- valid JSON;
- no ANSI;
- no headings/progress on stdout;
- arrays remain arrays for multiple answers;
- errors have documented status behavior.

### 8.9 Security heuristics

Outbound/listener “suspicious” scoring must be described as heuristic, not authoritative malware detection.

Expose the concrete observations that produced a score so users can assess it themselves.

### 8.10 Firewall portability

Prefer `nft` where available on modern Linux, with iptables fallback. Report which backend is in use.

---

## 9. `sqlitex` Plan

`sqlitex` manages real data. Correctness and recoverability take priority over adding commands.

### 9.1 Fix executable mode

Commit `Sqlite/sqlitex` as executable (`100755`). CI must prevent regressions.

### 9.2 Replace file-copy backup with SQLite-native backup

A raw `cp` of the main database file can be inconsistent when WAL/journal state is active.

Use SQLite’s backup mechanisms, e.g. `.backup` or another SQLite-native consistent snapshot path.

Backup requirements:

- verify destination was created and is readable;
- run `PRAGMA integrity_check` optionally/for critical flows;
- use collision-resistant timestamp/name;
- atomic final rename;
- document whether open writers are supported;
- never claim success before validation.

### 9.3 Transactional migrations

Current migration application runs the migration SQL and migration-table insert as separate operations. Make supported migrations atomic:

- begin transaction;
- apply migration;
- insert migration record;
- commit;
- rollback on failure.

If a migration contains statements incompatible with transactional execution, detect/document an explicit escape hatch rather than silently losing tracking consistency.

Rollback should likewise pair down-migration + tracking deletion atomically when possible.

### 9.4 Deterministic migration ordering/history

Add a stable ordering rule for migration filenames and a deterministic history key.

Do not rely only on second-resolution `applied_at` to identify “last migration”.

Recommended tracking schema includes an integer sequence/id plus migration name and timestamp.

### 9.5 Clarify lock semantics

Current `--use-lock` is a SQLite busy timeout, not an application lock.

For 2.0 either:

- rename/document it as `--busy-timeout`; retain `--use-lock` as deprecated alias; or
- add a real optional `flock` guard while retaining SQLite busy timeout separately.

Do not describe `.timeout` as an exclusive lock.

### 9.6 Safe identifiers and raw SQL boundary

Commands that accept a table name should validate/quote it as an identifier instead of concatenating arbitrary text.

Keep `exec --sql` explicitly raw and powerful.

For `--where`, `--set`, and `--values`, documentation must state that these are SQL expressions, not sanitized user-input APIs.

### 9.7 CSV/JSON import correctness

Current JSON conversion emits a header row before using SQLite `.import`; verify/fix header semantics so the header never becomes application data.

Define explicit behavior for CSV files:

- header expected/auto-detected/flag-controlled;
- column mapping;
- empty values/null handling;
- quoted newlines/commas;
- UTF-8 errors.

Use temp files with cleanup traps.

### 9.8 Reset correctness

Reset must account for WAL/SHM state and active connections.

Preferred flow:

- create validated backup;
- require explicit confirmation unless non-interactive approval is given;
- safely recreate database through SQLite;
- migrate;
- seed;
- surface failure with backup location and recovery instruction.

### 9.9 Export contract

Reconcile current behavior and documentation for `select --export`:

- if `--export csv|json` means “write file”, both formats must write predictable files;
- if JSON is stdout-oriented, expose a separate `--format json`/`--json` path and document it clearly.

Do not have CSV and JSON use materially different meaning for the same `--export` flag.

### 9.10 Dry-run accuracy

Dry-run must not create:

- DB files;
- backup directories;
- export directories;
- migration files;
- lock/state files.

It should print the ordered actions that would occur.

### 9.11 Doctor/optimize/tune

Before `VACUUM`, tuning, or journal-mode changes:

- show current settings;
- validate free disk requirements where relevant;
- create a consistent backup for high-impact changes;
- verify integrity after operation;
- document persistence/connection implications of each PRAGMA profile.

---

## 10. `cleanx` Plan

`cleanx` is the highest host-filesystem risk in the suite. Dry-run-by-default is correct and must remain.

### 10.1 Fix executable mode

Commit `Clean/cleanx` as executable (`100755`). CI must prevent regressions.

### 10.2 Rename legacy internal identity

Current config/lock naming still uses `cleanfy`:

```text
/etc/cleanfy.conf
~/.config/cleanfy.conf
/tmp/.cleanfy.lock
```

Normalize new 2.0 paths to `cleanx` while providing backward-compatible discovery/migration for legacy config.

Recommended paths:

```text
/etc/cleanx.conf
${XDG_CONFIG_HOME:-$HOME/.config}/cleanx/config
```

### 10.3 Replace race-prone lock file

Current “exists then write PID” `/tmp` lock is not atomic and can become stale.

Use `flock` where available, with a safe fallback such as atomic `mkdir` locking.

Lock scope must distinguish user-only/report mode from root system cleanup if necessary.

### 10.4 Remove string-built shell execution

Current `run()` ultimately executes a constructed string through `bash -c`, while exclusions/includes/config values can affect those strings.

Refactor destructive operations into argv arrays/direct functions.

Avoid building `find` expressions as shell text. Build arrays.

### 10.5 Config trust boundary

Sourcing configuration as shell code is powerful and dangerous, especially under `sudo`.

Preferred 2.0 direction:

- introduce a declarative config parser for supported keys/arrays;
- do not execute arbitrary config shell code.

If legacy sourced config must remain temporarily:

- reject unsafe ownership/permissions for root runs;
- clearly mark it deprecated;
- never source a user-writable config as root without explicit opt-in.

### 10.6 Full-disk behavior

Current preflight refuses cleanup when root filesystem usage is at/above 98% unless forced. That blocks one of the main situations in which a cleanup tool is needed.

Replace this with task-aware safety:

- permit reclaim-only operations when disk is critically full;
- skip/warn for tasks needing temporary workspace;
- avoid creating large backups/temp files when space is exhausted;
- provide emergency-safe cleanup guidance.

### 10.7 Cross-distro cleanup capabilities

Do not make generic cleanup depend on apt.

Package-cache adapters may support:

- apt;
- dnf/yum;
- pacman;
- apk.

Unsupported package-manager tasks should be skipped with a precise message while generic log/tmp/user-cache/inode reporting remains functional.

### 10.8 Secure erase semantics

Document that overwrite-based “secure erase” is not reliably secure on SSDs, copy-on-write filesystems, snapshots, journaling filesystems, or thin-provisioned storage.

Do not imply guaranteed erasure.

### 10.9 Target-user safety

Validate `SUDO_USER`, passwd lookup, target home, and path containment before deleting user caches.

Never fall back to a surprising home path for destructive operations.

### 10.10 JSON/no-color

`--json` must suppress all decorative ANSI/emoji human output on stdout.

Add tests for report-only and dry-run JSON paths.

### 10.11 Self-update

Replace branch-oriented default update (`main`) and optional checksum behavior with stable release asset + mandatory checksum verification for stable updates.

Development channel remains explicit opt-in.

---

## 11. `chromacat` Plan

`chromacat` is presentation-only and should remain safe to put in pipelines.

### 11.1 Cat/pipeline contract

When no formatting feature is requested and output is non-TTY/no-color, preserve input content faithfully.

Tests must cover:

- stdin;
- one file;
- multiple files;
- empty input;
- long streams;
- UTF-8;
- input already containing ANSI;
- broken downstream pipe (`head`, etc.).

### 11.2 Unknown option behavior

Current behavior falls back to `cat` with the original arguments on an unknown option. This can hide typos and produce surprising interpretation of Toolset-specific options.

For 2.0:

- unknown `chromacat` options should fail clearly;
- if raw cat passthrough is desired, expose an explicit `--cat`/`--` contract.

### 11.3 No-color contract

`--no-color` and `NO_COLOR` must guarantee no ANSI color/blink/invert escape sequences.

Presentation features that do not require color (e.g. optional box/header) should have documented behavior in no-color mode.

### 11.4 Unicode width

Review box centering/padding against multi-byte and wide characters. Byte length is not terminal display width.

If exact Unicode width would require a heavy dependency, degrade safely and document the limitation rather than corrupting layout.

### 11.5 Streaming/performance

`--stream`/`--log` must avoid buffering unbounded input.

Keep hot paths in a small number of AWK/process invocations rather than spawning per character/line.

Add a simple benchmark fixture to catch major regressions on large logs.

### 11.6 Terminal capability handling

`tput`/TERM absence must not break plain output.

Colors/animation are enhancements; text output remains primary.

### 11.7 Self-update

Replace raw `main` updater with stable release asset + checksum verification.

---

## 12. Documentation Plan

### Root `README.md`

Rewrite installation section around stable releases, not mutable `main`.

Include:

- one-line purpose per independent CLI;
- stable/reproducible install example;
- latest-stable convenience install;
- optional installer usage if added;
- distro/support matrix;
- no claim that all commands have identical support on every Linux distribution;
- security note for high-impact tools;
- link to release/checksum policy.

Fix existing Markdown fence inconsistencies while touching installation docs.

### Per-tool READMEs

Every README should contain the same compact headings:

1. Purpose
2. Install
3. Requirements
4. Supported platforms/capabilities
5. Quick start
6. Command reference
7. Destructive/security behavior
8. Exit/output contract
9. Self-update
10. Examples

Documentation must be generated/reviewed against actual `--help`; CI should at least detect obviously stale command names.

---

## 13. Linux Test Matrix

Do not require every command to mutate the GitHub-hosted runner itself. Use disposable containers/temp namespaces for system-modifying tests.

### Generic script matrix

Test Bash behavior across representative Linux families:

- Debian;
- Ubuntu;
- Fedora/RHEL-family image;
- Alpine with Bash explicitly installed.

The exact currently supported image versions should be pinned/updated intentionally in CI.

### Tool-specific smoke coverage

#### `gitx`

Create temporary fixture repositories and local bare remotes. No network required for most tests.

#### `phpx`

Use privileged/disposable distro containers for package/service config tests. Keep host runner untouched. Separate generic-PHP tests from package-manager backend tests.

#### `dockex`

Use an ephemeral Docker daemon/job where available. Never run `cleanup all` against a shared runner daemon.

#### `netx`

Use localhost listeners, temporary HTTP/TLS endpoints, and network namespaces when capability is available. Internet-dependent tests are optional/non-blocking unless testing that specific integration.

#### `sqlitex`

Use temporary SQLite databases including WAL mode, migrations, failed migrations, CSV/JSON seeds, concurrent lock tests, backup/restore integrity, and unusual filenames.

#### `cleanx`

Test only against fabricated temporary filesystem trees or disposable containers. Never point CI cleanup tests at the runner root filesystem.

#### `chromacat`

Golden-output tests for plain/no-color modes plus bounded performance test for a large generated stream.

---

## 14. Security Review Gates

Before 2.0 release, explicitly search/review the repository for:

- `eval`;
- `source` of writable/user-controlled config;
- fixed `/tmp` paths;
- `rm -rf`;
- destructive `find -delete`;
- raw `curl | shell` patterns;
- downloads without checksum/signature validation;
- `chmod 777`/over-broad permissions;
- environment/secret printing;
- unquoted variable expansion;
- path arguments without `--`;
- command strings passed to `bash -c`;
- hard-coded `main`/`master` update URLs;
- implicit `sudo`/root assumptions;
- background processes without cleanup traps.

Any retained occurrence should have a clear reason and tests around its boundary.

---

## 15. Implementation Order

Toolset scripts do not depend on one another, so implementation order should be **risk-first**, not product-stack order.

### Phase 1 — Repository contract

1. Add CI and test harness.
2. Fix executable bits.
3. Add standardized `--version` metadata.
4. Establish release manifest/assets/checksums.
5. Replace mutable stable install/update contract.

Gate: no tool-specific behavior rewrite merges until baseline CI can catch syntax and smoke regressions.

### Phase 2 — Critical destructive/data paths

1. `cleanx`
2. `phpx`
3. `dockex`
4. `sqlitex`

Gate: destructive operations must have disposable functional tests before release.

### Phase 3 — Security/automation paths

1. `netx`
2. `gitx`

Gate: remove unintended `eval`, unsafe temp paths, secret persistence/output hazards, and filename parsing defects.

### Phase 4 — Presentation path

1. `chromacat`

Gate: pipeline/no-color/non-TTY compatibility tests pass.

### Phase 5 — Documentation & downstream pins

1. Update root/per-tool docs.
2. Publish 2.0 release candidate.
3. Verify release assets/checksums/self-update.
4. Give downstream Docker repos an immutable accepted Toolset ref.
5. Update LocalDevStack/docker ecosystem only after Toolset’s release contract is stable.

---

## 16. Explicit Non-Goals

This plan does **not**:

- merge all tools into one binary;
- require users to install the whole Toolset suite;
- add a mandatory shared runtime library;
- make `chromacat` a dependency of the other CLIs;
- make Toolset depend on Scriptomatic;
- make `gitx` depend on an LLM container;
- add Docker-specific assumptions to generic tools;
- force identical package-management behavior across all Linux distributions;
- rewrite all scripts into another language;
- add features merely for symmetry when there is no real use case.

---

## 17. 2.0 Acceptance Criteria

Toolset 2.0 is ready only when all of the following are true:

1. All seven CLIs pass `bash -n` and the agreed ShellCheck policy.
2. Every distributable CLI is committed executable.
3. Every CLI has working `--help` and `--version`.
4. Each tool remains independently installable as a single script.
5. Stable install paths use immutable releases or latest-stable release assets, not raw `main`.
6. Stable self-update verifies checksums and performs atomic replacement.
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
18. The GitHub release contains all seven standalone scripts, `SHA256SUMS`, and release metadata.
19. Downstream Docker repositories can pin a Toolset tag/commit without any dependency on `main`.
20. Root and per-tool documentation describe the actual behavior validated by tests.

---

## 18. Relationship to the LocalDevStack Docker Ecosystem Plan

The existing LocalDevStack shared-foundations plan remains valid but is intentionally narrower than this document.

For that ecosystem, the critical Toolset outputs are currently:

- `gitx`;
- `chromacat`;
- `sqlitex`;
- `netx`;
- potentially other tools only when a concrete downstream consumer adopts them.

The contract Toolset provides to those repositories is simple:

1. a stable standalone script;
2. an immutable ref/release artifact;
3. checksum/release metadata;
4. tested non-interactive behavior.

Toolset itself remains a general Linux CLI suite. The downstream Docker architecture must adapt to Toolset’s public release contract—not the other way around.
