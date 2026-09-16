# Toolset 2.0 — Implementation Tracker

Branch: `plan/toolset-linux-cli-hardening`

Plan: `docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md`

Draft PR: `#47` — keep open for the full hardening cycle.

Legend: `[ ]` not started · `[-]` in progress · `[x]` done · `[!]` blocked / needs decision

## Current Focus

**Phase 1 — Repository contract**

Current task: resolve CI-discovered static/CLI-contract defects, then finish standardized version metadata and immutable release flow.

## Phase 1 — Repository Contract

- [-] Add baseline CI workflow for all seven tools.
  - [x] `bash -n` all executable sources.
  - [x] ShellCheck error-level gate is wired and reporting real defects.
  - [x] Verify executable mode on all distributable tools.
  - [-] Smoke `--help` for every tool.
  - [-] Smoke `--version` for every tool.
  - [x] Non-TTY/no-color baseline checks.
  - [x] Independent jobs so one failure does not hide other findings.
  - [x] Aggregate CI gate/job summary.
  - [x] CI reports uploaded as artifacts.
- [x] Add lightweight Bash test harness under `tests/`.
- [x] Add Debian/Ubuntu/Fedora/Alpine distro syntax/pipeline smoke matrix.
- [x] Add standalone distribution packaging/checksum snapshot job.
- [x] Fix executable git modes.
  - [x] `Sqlite/sqlitex` → `100755`.
  - [x] `Clean/cleanx` → `100755`.
- [-] Standardize per-tool `--version` / help contract.
  - [x] `chromacat` currently passes CI contract.
  - [x] `cleanx` currently passes CI contract.
  - [!] `dockex` — `--help` and `--version` currently exit `1`.
  - [!] `gitx` — `--help` and `--version` currently exit `1`.
  - [x] `netx` currently passes CI contract.
  - [x] `phpx` currently passes CI contract; metadata semantics still need review.
  - [!] `sqlitex` — `--help` and `--version` currently exit `1`.
- [ ] Define suite/tool version metadata policy.
- [ ] Add release workflow.
- [ ] Publish/check generated `SHA256SUMS`.
- [ ] Publish/check generated `manifest.json`.
- [ ] Replace stable install contract that points at mutable `main`.
- [ ] Replace self-update stable channel that points at mutable `main`.

### CI Findings — Current

- [!] `Network/netx`: ShellCheck `SC1087` at the `port find` regex; `$port` must be braced before `[[:space:]]`.
- [!] `PHP/phpx`: ShellCheck `SC2275` near the progress renderer; a carriage-return explanation line is malformed and parsed as a command.
- [!] `dockex`: public `--help` / `--version` contract missing or returns non-zero.
- [!] `gitx`: public `--help` / `--version` contract missing or returns non-zero.
- [!] `sqlitex`: public `--help` / `--version` contract missing or returns non-zero.
- [x] Debian 13 distro smoke passes.
- [x] Ubuntu 24.04 distro smoke passes.
- [x] Fedora 42 distro smoke passes.
- [x] Alpine 3.22 (with Bash installed) distro smoke passes.
- [x] Baseline non-TTY/no-color smoke passes.
- [x] Standalone packaging plus `SHA256SUMS` verification passes.

### Phase 1 Gate

- [ ] Syntax/static/smoke CI passes completely.
- [x] All seven CLI artifacts are executable.
- [ ] All seven expose stable help/version behavior.
- [ ] Release assets can be built from an immutable tag.

## Phase 2 — Critical Destructive/Data Paths

### `cleanx`

- [ ] Migrate legacy `cleanfy` identity/config paths to `cleanx` with compatibility handling.
- [ ] Replace race-prone `/tmp/.cleanfy.lock` with `flock`/safe fallback.
- [ ] Remove string-built destructive shell execution.
- [ ] Replace shell-sourced config with declarative parsing or safe compatibility boundary.
- [ ] Fix full-disk preflight so reclaim-only operations remain possible.
- [ ] Add package-manager capability backends / explicit skips.
- [ ] Harden target-user/home validation.
- [ ] Make JSON output machine-clean.
- [ ] Harden stable self-update.
- [ ] Add disposable-filesystem tests.

### `phpx`

- [ ] Separate generic PHP capability from distro package management.
- [ ] Formalize package-manager backends/capability reporting.
- [ ] Formalize service-manager detection/backends.
- [ ] Harden Sury/Ondřej repository/key setup.
- [ ] Make Composer install/update semantics reproducible and explicit.
- [ ] Harden PECL/source extension build/rollback.
- [ ] Make generated config writes atomic + validated.
- [ ] Make logging non-fatal for read-only commands and secret-safe.
- [ ] Make root requirement operation-specific.
- [ ] Harden stable self-update.
- [ ] Add disposable distro-container tests.

### `dockex`

- [ ] Harden daemon/context/rootless detection.
- [ ] Replace grep-based container identity matching with Docker-native inspect/filter logic.
- [ ] Redact environment values by default.
- [ ] Redesign backup/restore around deterministic tar archive flow.
- [ ] Scope restore to selected mount/volume; never blind-extract to `/`.
- [ ] Add explicit live-data consistency warning/quiesce behavior.
- [ ] Harden cleanup confirmation / non-interactive semantics.
- [ ] Validate resource update inputs.
- [ ] Harden benchmark/stats dependency and timeout behavior.
- [ ] Add ephemeral-Docker tests.

### `sqlitex`

- [ ] Replace raw DB `cp` backup with SQLite-native consistent backup.
- [ ] Make migration + tracking record transactional where SQLite permits.
- [ ] Add deterministic migration ordering/history sequence.
- [ ] Clarify/rename busy-timeout vs real locking semantics.
- [ ] Validate/quote table identifiers.
- [ ] Fix CSV/JSON import header/null/column behavior.
- [ ] Harden reset for WAL/SHM and recovery.
- [ ] Make export flag semantics consistent.
- [ ] Make dry-run side-effect-free.
- [ ] Harden optimize/tune backup/integrity flow.
- [ ] Add WAL, failure, migration, seed, backup tests.

### Phase 2 Gate

- [ ] High-impact tools have disposable functional safety tests.
- [ ] No known unsafe default destructive behavior remains.

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
- [ ] Harden stable self-update.
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
- [ ] Harden stable self-update.
- [ ] Add golden pipeline/no-color/stream tests.

### Phase 4 Gate

- [ ] Pipeline, non-TTY, no-color and streaming tests pass.

## Phase 5 — Documentation & Downstream Pins

- [ ] Update root README to stable release installation model.
- [ ] Normalize per-tool README sections.
- [ ] Add dependency/capability matrix per tool.
- [ ] Document destructive/security boundaries per tool.
- [ ] Document output/exit contracts.
- [ ] Verify docs against actual `--help`.
- [ ] Build Toolset 2.0 release candidate.
- [ ] Verify release asset checksums and self-update behavior.
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
- [ ] Review mutable `main`/`master` URLs.
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

## Findings / Follow-ups

- [x] Current repo has seven standalone tools.
- [x] Current repo originally had no validation workflow beyond `CODEOWNERS`.
- [x] `Sqlite/sqlitex` was non-executable in git; fixed on implementation branch.
- [x] `Clean/cleanx` was non-executable in git; fixed on implementation branch.
- [x] Root/per-tool install docs currently use mutable `main` URLs.
- [x] `gitx`, `phpx`, and `chromacat` currently self-update from mutable `main`.
- [x] `gitx` uses predictable `/tmp` files in interactive flows.
- [x] `gitx` sources a settings file containing Gemini configuration.
- [x] `netx` has TLS command construction through `eval`.
- [x] `netx guard --exec` currently executes through `eval`.
- [x] `dockex info` currently exposes raw container environment values.
- [x] `dockex` backup/restore currently installs zip/unzip dynamically in an Alpine helper container.
- [x] `sqlitex` current backup is a raw file copy.
- [x] `cleanx` still carries legacy `cleanfy` config/lock naming.

## Work Log

| Date | Change | Status |
|---|---|---|
| 2026-09-16 | Full Toolset audit and 2.0 hardening plan created. | done |
| 2026-09-16 | Progress tracker created; Phase 1 started. | done |
| 2026-09-16 | Fixed executable git modes for `cleanx` and `sqlitex`. | done |
| 2026-09-16 | Added lightweight assertion/static/smoke harness. | done |
| 2026-09-16 | Opened draft PR #47 for continuous CI/review visibility. | done |
| 2026-09-16 | Expanded CI into static, CLI-contract, 4-distro smoke, distribution artifact and aggregate gate jobs. | done |
| 2026-09-16 | Initial expanded CI found 2 ShellCheck blockers and 3 tools missing successful help/version contracts. | in progress |

## Next Task

Fix the two ShellCheck blockers (`netx`, `phpx`) and standardize `dockex`, `gitx`, and `sqlitex` `--help`/`--version` behavior so the foundational CI gate can turn green before deeper behavioral hardening begins.
