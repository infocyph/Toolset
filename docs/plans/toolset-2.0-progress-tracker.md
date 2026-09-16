# Toolset 2.0 — Implementation Tracker

Branch: `plan/toolset-linux-cli-hardening`

Plan: `docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md`

Draft PR: `#47` — keep open for the full hardening cycle.

Legend: `[ ]` not started · `[-]` in progress · `[x]` done · `[!]` blocked / needs decision

## Current Focus

**Phase 3 — Security / Automation Paths**

Current task: harden `netx` first: remove user-controlled `eval`, make state creation XDG/lazy, correct endpoint/address handling, bound network operations, and add local safety fixtures before moving to `gitx`.

## Phase 1 — Repository Contract

- [x] Add baseline CI workflow for all seven tools.
  - [x] `bash -n` all executable sources.
  - [x] ShellCheck error-level gate.
  - [x] Verify executable mode on all distributable tools.
  - [x] Smoke `--help` for every tool.
  - [x] Smoke canonical `--version` for every tool.
  - [x] Non-TTY/no-color baseline checks.
  - [x] Independent jobs so one failure does not hide other findings.
  - [x] Aggregate CI gate/job summary.
  - [x] CI reports uploaded as artifacts.
  - [x] GitHub Actions workflow validation added with pinned `actionlint` 1.7.12.
- [x] Add lightweight Bash test harness under `tests/`.
- [x] Add Debian/Ubuntu/Fedora/Alpine distro syntax/pipeline smoke matrix.
- [x] Add standalone distribution packaging/checksum snapshot job.
- [x] Fix executable git modes.
  - [x] `Sqlite/sqlitex` → `100755`.
  - [x] `Clean/cleanx` → `100755`.
- [x] Standardize per-tool `--version` / help contract.
  - [x] `chromacat`
  - [x] `cleanx`
  - [x] `dockex`
  - [x] `gitx`
  - [x] `netx`
  - [x] `phpx`
  - [x] `sqlitex`
- [x] Define suite/tool version metadata policy.
  - [x] Suite release version comes from immutable `vMAJOR.MINOR.PATCH` Git tag.
  - [x] Each standalone CLI exposes its own embedded tool version.
  - [x] Tool versions may evolve independently of the suite release.
  - [x] `manifest.json` records both suite identity and each tool's version/digest.
- [x] Add immutable release workflow.
  - [x] Strict `vMAJOR.MINOR.PATCH` tag validation.
  - [x] Refuse to overwrite an existing GitHub release.
  - [x] Re-run static and CLI-contract validation from tagged source.
  - [x] Build all seven standalone assets plus the installer.
  - [x] Publish `SHA256SUMS` and `manifest.json` with assets.
  - [x] Validate workflow through PR `actionlint`/CI gate.
- [x] Generate and verify `SHA256SUMS`.
- [x] Generate deterministic `manifest.json`.
- [x] Replace stable install contract that pointed at mutable `main`.
  - [x] Add versioned `install.sh` release asset.
  - [x] Support individual tools, multiple tools, `--all`, exact `--release`, latest stable and custom prefixes.
  - [x] Verify checksums and Bash syntax before replacement.
  - [x] Keep a `.previous` rollback copy during replacement.
  - [x] Root and per-tool installation docs use release assets rather than mutable `main`.
- [x] Replace self-update stable channel that pointed at mutable `main`.
  - [x] `gitx`, `phpx`, `chromacat` and `cleanx` default to stable checksum-verified release assets.
  - [x] Mutable branch/main development channels are not the stable default.

### CI Findings — Resolved

- [x] `Network/netx`: fixed ShellCheck `SC1087` by bracing the port expansion.
- [x] `PHP/phpx`: fixed ShellCheck `SC2275` in the progress renderer by using explicit `\r` / `\033[2K` escapes.
- [x] `dockex`: added dependency-independent successful `--help` / `--version` handling.
- [x] `gitx`: made usage informational, added canonical `--version`, and separated unknown-command failure.
- [x] `sqlitex`: added pre-database/pre-SQLite successful `--help` / `--version` handling.
- [x] `phpx`: caught and fixed a CI false positive where `--version` returned exit 0 but printed full usage text.
- [x] Version contract now requires exactly one canonical `<tool> <version>` stdout line and no stderr.
- [x] Fixed incorrect `actionlint -color never` invocation; pinned `actionlint` workflow validation now passes.
- [x] Debian 13 distro smoke passes.
- [x] Ubuntu 24.04 distro smoke passes.
- [x] Fedora 42 distro smoke passes.
- [x] Alpine 3.22 (with Bash installed) distro smoke passes.
- [x] Baseline non-TTY/no-color smoke passes.
- [x] Standalone packaging plus `SHA256SUMS` and `manifest.json` verification passes.
- [x] Full CI matrix and aggregate gate pass on the completed Phase 1 branch state.

### Phase 1 Gate

- [x] Syntax/static/workflow/smoke CI passes completely.
- [x] All seven CLI artifacts are executable.
- [x] All seven expose stable help/version behavior.
- [x] Immutable semantic-tag release workflow builds/publishes versioned assets with checksums and manifest; actual `v2.0.0` publication remains intentionally deferred until the full hardening cycle is complete.
- [x] Stable installation and stable self-update no longer depend on mutable `main`.

## Phase 2 — Critical Destructive/Data Paths

### `cleanx`

- [x] Migrate legacy `cleanfy` identity/config paths to `cleanx` with compatibility handling.
- [x] Replace race-prone `/tmp/.cleanfy.lock` with `flock`/safe fallback.
- [x] Remove string-built destructive shell execution.
- [x] Replace shell-sourced config with declarative parsing or safe compatibility boundary.
- [x] Fix full-disk preflight so reclaim-only operations remain possible.
- [x] Add package-manager capability backends / explicit skips.
- [x] Harden target-user/home validation.
- [x] Make JSON output machine-clean.
- [x] Harden stable self-update baseline through the Phase 1 release channel; review tool-specific behavior during `cleanx` hardening.
- [x] Add disposable-filesystem tests.

### `phpx`

- [x] Separate generic PHP capability from distro package management.
- [x] Formalize package-manager backends/capability reporting.
- [x] Formalize service-manager detection/backends.
- [x] Harden Sury/Ondřej repository/key setup.
- [x] Make Composer install/update semantics reproducible and explicit.
- [x] Harden PECL/source extension build/rollback.
- [x] Make generated config writes atomic + validated.
- [x] Make logging non-fatal for read-only commands and secret-safe.
- [x] Make root requirement operation-specific.
- [x] Harden stable self-update baseline through the Phase 1 release channel; review tool-specific behavior during `phpx` hardening.
- [x] Add disposable distro-container tests.

### `dockex`

- [x] Harden daemon/context/rootless detection.
- [x] Replace grep-based container identity matching with Docker-native inspect/filter logic.
- [x] Redact environment values by default.
- [x] Redesign backup/restore around deterministic tar archive flow.
- [x] Scope restore to selected mount/volume; never blind-extract to `/`.
- [x] Add explicit live-data consistency warning/quiesce behavior.
- [x] Harden cleanup confirmation / non-interactive semantics.
- [x] Validate resource update inputs.
- [x] Harden benchmark/stats dependency and timeout behavior.
- [x] Add ephemeral-Docker tests.

### `sqlitex`

- [x] Replace raw DB `cp` backup with SQLite-native consistent backup.
- [x] Make migration + tracking record transactional where SQLite permits.
- [x] Add deterministic migration ordering/history sequence.
- [x] Clarify/rename busy-timeout vs real locking semantics.
- [x] Validate/quote table identifiers.
- [x] Fix CSV/JSON import header/null/column behavior.
- [x] Harden reset for WAL/SHM and recovery.
- [x] Make export flag semantics consistent.
- [x] Make dry-run side-effect-free.
- [x] Harden optimize/tune backup/integrity flow.
- [x] Add WAL, failure, migration, seed, backup tests.

### Phase 2 Gate

- [x] High-impact tools have disposable functional safety tests.
- [x] No known unsafe default destructive behavior remains.

## Phase 3 — Security / Automation Paths

### `netx`

- [ ] Remove TLS `eval` command construction.
- [ ] Redesign `guard --exec` argv/shell boundary.
- [ ] Correct IPv4/IPv6 endpoint parsing.
- [ ] Harden private/public address classification.
- [ ] Remove state-directory creation from stateless startup paths.
- [ ] Adopt XDG state/config paths where appropriate.
- [ ] Add per-command privilege/capability diagnostics.
- [ ] Add finite timeout defaults to bounded network operations.
- [ ] Validate every JSON path.
- [ ] Document heuristic nature of suspicious scoring.
- [ ] Prefer nftables with iptables fallback.
- [ ] Add local endpoint/network namespace tests.

### `gitx`

- [ ] Make path/file selection NUL-safe.
- [ ] Replace predictable `/tmp` files with secure temp state.
- [ ] Remove avoidable internal `eval`.
- [ ] Harden remote/main-branch/worktree behavior.
- [ ] Harden cherry-pick/revert conflict/recovery behavior.
- [ ] Add fixture validation for report/worklog/summary/range commands.
- [ ] Stop sourcing arbitrary settings file for Gemini config.
- [ ] Make API-key persistence explicit opt-in.
- [ ] Add API timeouts/response validation/payload limits.
- [ ] Exclude/confirm likely secret/binary staged content for AI commit.
- [x] Harden stable self-update baseline through the Phase 1 release channel; review tool-specific behavior during `gitx` hardening.
- [ ] Add temporary Git repository/bare-remote tests.

### Phase 3 Gate

- [ ] No unintended `eval` remains around user-controlled values.
- [ ] No predictable shared temp state remains for sensitive/interactively generated data.
- [ ] Network/AI automation paths have bounded failures.

## Phase 4 — Presentation Path

### `chromacat`

- [ ] Preserve faithful non-TTY/plain pipeline behavior.
- [ ] Make unknown options fail clearly instead of implicit `cat` fallback.
- [ ] Guarantee `--no-color` / `NO_COLOR` ANSI-free output.
- [ ] Review Unicode display-width behavior.
- [ ] Keep streaming modes bounded and efficient.
- [ ] Harden missing TERM/tput behavior.
- [x] Harden stable self-update baseline through the Phase 1 release channel; review tool-specific behavior during `chromacat` hardening.
- [ ] Add golden pipeline/no-color/stream tests.

### Phase 4 Gate

- [ ] Pipeline, non-TTY, no-color and streaming tests pass.

## Phase 5 — Documentation & Downstream Pins

- [x] Update root README to stable release installation model.
- [-] Normalize per-tool README sections; installation paths now use stable release assets, broader normalization remains.
- [ ] Add dependency/capability matrix per tool.
- [ ] Document destructive/security boundaries per tool.
- [ ] Document output/exit contracts.
- [ ] Verify docs against actual `--help`.
- [ ] Build Toolset 2.0 release candidate.
- [ ] Verify published release asset checksums and self-update behavior against the RC.
- [ ] Select immutable Toolset ref for downstream Docker ecosystem.
- [ ] Update LocalDevStack shared-foundations tracking with accepted Toolset ref.

## Cross-Cutting Security Checklist

- [ ] Review all `eval` occurrences.
- [ ] Review all `source` of writable/user-controlled config.
- [ ] Review all fixed `/tmp` paths.
- [ ] Review all `rm -rf` / `find -delete` paths.
- [ ] Review remote downloads/checksum policy.
- [ ] Review secret/environment output.
- [ ] Review unquoted expansion / missing `--` path delimiters.
- [ ] Review `bash -c` command construction.
- [-] Review mutable `main`/`master` URLs; stable install/self-update paths are fixed, development/documentation leftovers will be reviewed in their owning phases.
- [ ] Review root/sudo assumptions.
- [ ] Review background processes/trap cleanup.

## Decisions Locked

- [x] Toolset remains a suite of **independent, standalone Linux CLI scripts**.
- [x] No mandatory shared runtime shell library.
- [x] Docker/LocalDevStack are downstream consumers, not Toolset's architectural center.
- [x] Single-file installability remains a release requirement.
- [x] Stable releases must be immutable and checksum-verifiable.
- [x] Development `main` update paths, if retained, are explicit opt-in only.
- [x] Risk-first implementation order is preferred over Docker dependency order.
- [x] Keep draft PR `#47` open throughout implementation so CI/review findings stay visible.
- [x] Suite version and individual tool versions are separate identities.
- [x] Release manifest is deterministic: no build timestamp or other volatile field.

## Findings / Follow-ups

- [x] Current repo has seven standalone tools.
- [x] Current repo originally had no validation workflow beyond `CODEOWNERS`.
- [x] `Sqlite/sqlitex` was non-executable in git; fixed on implementation branch.
- [x] `Clean/cleanx` was non-executable in git; fixed on implementation branch.
- [x] Root/per-tool stable install paths formerly used mutable `main`; migrated to release assets.
- [x] `gitx`, `phpx`, `chromacat`, and `cleanx` stable self-update behavior formerly depended on mutable branch paths; migrated to release assets.
- [x] `gitx` uses predictable `/tmp` files in interactive flows; retained for Phase 3 hardening.
- [x] `gitx` sources a settings file containing Gemini configuration; retained for Phase 3 hardening.
- [x] `netx` has TLS command construction through `eval`; retained for Phase 3 hardening.
- [x] `netx guard --exec` currently executes through `eval`; retained for Phase 3 hardening.
- [x] `dockex info` currently exposes raw container environment values; queued for Phase 2.
- [x] `dockex` backup/restore currently installs zip/unzip dynamically in an Alpine helper container; queued for Phase 2.
- [x] `sqlitex` current backup is a raw file copy; queued for Phase 2.
- [x] `cleanx` legacy `cleanfy` config paths now have data-only compatibility, preferred `cleanx` paths, safe runtime locking, argv-safe deletion, validated target identity and permanent disposable safety tests.

## Work Log

| Date | Change | Status |
|---|---|---|
| 2026-09-16 | Full Toolset audit and 2.0 hardening plan created. | done |
| 2026-09-16 | Progress tracker created; Phase 1 started. | done |
| 2026-09-16 | Fixed executable git modes for `cleanx` and `sqlitex`. | done |
| 2026-09-16 | Added lightweight assertion/static/smoke harness. | done |
| 2026-09-16 | Opened draft PR #47 for continuous CI/review visibility. | done |
| 2026-09-16 | Expanded CI into static, CLI-contract, 4-distro smoke, distribution artifact and aggregate gate jobs. | done |
| 2026-09-16 | Initial expanded CI found 2 ShellCheck blockers and 3 tools missing successful help/version contracts. | done |
| 2026-09-16 | Fixed `netx`/`phpx` static defects and normalized `dockex`/`gitx`/`sqlitex` CLI contracts. | done |
| 2026-09-16 | Strengthened version tests; discovered `phpx --version` false-positive usage output and fixed it. | done |
| 2026-09-16 | Added deterministic release `manifest.json`, release installer and SHA-256 verification. | done |
| 2026-09-16 | Added immutable semantic-tag release workflow and pinned `actionlint` workflow validation. | done |
| 2026-09-16 | Migrated stable installation and updater paths away from mutable `main`. | done |
| 2026-09-16 | Fixed actionlint invocation and completed the full green Phase 1 CI gate. | done |
| 2026-09-16 | Phase 1 closed; Phase 2 started with `cleanx`. | done |
| 2026-09-16 | Completed `cleanx` Phase 2 hardening: declarative config, safe locking/deletion, package capability handling, clean JSON, resilient reports, docs and permanent safety tests. | done |
| 2026-09-16 | Started `phpx` Phase 2 capability and mutation-path hardening. | in progress |

## Next Task

Harden `netx`: eliminate TLS/guard `eval`, adopt lazy XDG state, correct IPv4/IPv6 endpoint and address classification, bound network operations, validate JSON output, and add local endpoint/network-namespace fixtures.
