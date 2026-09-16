# cleanx

<!-- TOOLSET2-CONTRACT:START -->
## Purpose

Safe modular disk/inode cleanup with reporting, quota controls and explicit application of destructive actions.

## Install

Latest stable (checksum-verifying installer):

```bash
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh"
bash install.sh cleanx
```

Exact reproducible release:

```bash
bash install.sh --release 2.0 cleanx
```

## Requirements

Bash and standard Linux filesystem/core utilities. Package/journal/container/cache cleanup commands are capability-gated.

## Supported platforms/capabilities

Generic Linux for filesystem/report functions, with explicit package-manager and service-specific capabilities where available.

See [`../docs/cli-contracts.md`](../docs/cli-contracts.md) for the suite capability matrix.

## Quick start

```bash
cleanx --report
cleanx --report --json
cleanx --help
```

## Command reference

`cleanx --help` is the authoritative live command reference. `cleanx --version` prints the installed tool version. The detailed reference below expands on command-specific behavior.

## Destructive/security behavior

Dry-run is the default; actual deletion requires explicit approval. Delete roots and target users are validated, config is declarative, locking is private/atomic, and overwrite-style secure erase is not guaranteed on SSD/COW/snapshot storage.

## Exit/output contract

Exit `0` means success; non-zero means the requested operation did not complete successfully. Machine-readable modes reserve stdout for data and send diagnostics to stderr. Do not parse undocumented human wording as a stable API.

## Self-update

Where `cleanx` exposes self-update, the stable channel uses checksum-verified GitHub release assets. `TOOLSET_SELF_UPDATE_RELEASE=2.0` may pin an exact release for acceptance/rollback verification; mutable `main` is never the stable default. If the tool does not expose self-update, reinstall through the release installer.

## Examples

```bash
cleanx --report
sudo cleanx --yes logs tmp
```
<!-- TOOLSET2-CONTRACT:END -->

`cleanx` is a **safe, modular, dry-run-by-default** disk & inode cleaner for Linux.
Think “CCleaner for servers,” but **Bash-only, scriptable, and fast**.

* One file, zero exotic deps (just `bash`, `coreutils`, and common tools).
* Strict safety rails and **explicit flags**.
* Rich reports (blocks + inodes), JSON summary, quota-based runs.
* Self-update support + completions.

---

## ✨ Features

* **Dry-run by default** — prints actions; apply with `--yes`.
* **Safety preflight** — warns when `/` is ≥98% used but still permits reclaim operations; `--force` suppresses that warning.
* **Low-impact mode** — `ionice` + `nice` with `--low-impact`.
* **Tasks** for: package cleanup (APT/DNF/Zypper with explicit safe skips elsewhere), logs, journald, `/tmp`, user caches, language caches (Composer/npm/pnpm/yarn/pip), Snap/Flatpak, Docker/Podman/containerd, old kernels where supported, coredumps, build caches, browser caches, Timeshift, package size view, FS hints.
* **Inode tooling** — inode df, hotspots, parameterized deep scans.
* **Configurable** — declarative `KEY=VALUE` global/user config + `--config=FILE`; config files are never sourced as shell code.
* **Secure erase** — `--secure-erase` to `shred` files before removal.
* **Quota** — stop when freed `SIZE`, e.g. `--quota=5G`.
* **JSON report** — `--json` reserves stdout for one parseable JSON document; operational output is sent to stderr.
* **Self-update** — `--update` uses the checksum-verified latest stable release; `--channel` can be used for explicit branch/tag version checks.
* **Shell completions** — `--completions=bash|zsh`.
* **Doctor** — `--doctor` checks environment & prints quick FS state.
* **Locking** — prevents concurrent mutation runs with `flock` in the runtime/lock directory and an atomic private-directory fallback.

---

## 📦 Install

Single-file install (matches Toolset layout):

```bash
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh"
bash install.sh cleanx
```

---

## 🚀 Quick Start

```bash
# Read-only system report (blocks, inodes, hotspots, deleted-but-open files)
cleanx --report

# Safe baseline cleanup (low I/O pressure)
sudo cleanx --yes --low-impact apt apt-residuals logs tmp tmpfiles usercache langcaches journal

# Free space until 5GB is reclaimed (applies changes)
sudo cleanx --yes --quota=5G logs tmp usercache

# Containers-heavy host
sudo cleanx --yes --low-impact --aggressive docker podman containerd

# Secure erase sensitive caches & truncate huge logs
sudo cleanx --yes --secure-erase usercache logs
```

> `report` is **read-only** and runs before any mutating tasks, even when combined with others.

---

## 🔧 Usage

```bash
cleanx [options] <tasks...>
```

If you pass **no tasks**, `cleanx` shows `--help` and exits.

---

## 🧱 Tasks

All tasks can be combined, e.g.:

```bash
sudo cleanx --yes logs tmp usercache
```

| Task            | What it does                                                                                                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `report`        | Prints FS usage (blocks & inodes), top dirs by size & inode count, hotspots, deleted-but-open files                                                                                                    |
| `packages` / `apt` | Package cleanup backend: APT (`autoremove` + `clean`), DNF (`autoremove` + `clean all`), Zypper cache cleanup, or an explicit safe skip when no supported automatic policy exists                                                                                                                                                              |
| `apt-residuals` | Purges “rc” packages (residual configs)                                                                                                                                                                |
| `journal`       | Rotates and vacuums journald (`--vacuum-time` or `--vacuum-size` via `--journal-keep`)                                                                                                                 |
| `logs`          | Deletes rotated logs (`*.gz`) older than 14 days; truncates `*.log` over `--log-max`                                                                                                                   |
| `tmp`           | Deletes `/tmp` entries older than `--tmp-days` (via `find ... -mtime +N`)                                                                                                                              |
| `tmpfiles`      | Runs `systemd-tmpfiles --clean` if available                                                                                                                                                           |
| `usercache`     | Clears `$HOME/.cache`, thumbnails, and Trash for `--user` (default: `SUDO_USER`/`$USER`)                                                                                                               |
| `langcaches`    | Clears Composer/npm/pnpm/yarn/pip caches for the validated target user via `runuser` when available                                                                                                                                    |
| `snap`          | Retains `--snap-retain` revisions; removes disabled snaps & saved snapshots                                                                                                                            |
| `flatpak`       | `flatpak uninstall --unused` and `flatpak remove --delete-data -y --unused`                                                                                                                            |
| `docker`        | `docker system prune -af`; with `--aggressive` also prunes `--volumes`                                                                                                                                 |
| `podman`        | `podman system prune -af`; with `--aggressive` also runs `podman volume prune -f`                                                                                                                      |
| `containerd`    | Removes untagged images via `ctr -n default images rm`                                                                                                                                                 |
| `kernels`       | Removes old kernels via `apt autoremove --purge -y`                                                                                                                                                    |
| `coredumps`     | Removes `core* > 50M` (whole FS) and `/var/crash/*`; with `--secure-erase` uses `shred`                                                                                                                |
| `buildcache`    | Clears `ccache` stats & cache (if present)                                                                                                                                                             |
| `browsers`      | Clears Chromium/Chrome/Firefox caches for target user                                                                                                                                                  |
| `timeshift`     | Keeps last 3 of each Timeshift snapshot type (hourly/daily/weekly/monthly)                                                                                                                             |
| `pkgbig`        | Lists top 30 packages by installed size (read-only)                                                                                                                                                    |
| `inode-scan`    | Parameterized inode hotspot scan (`--inode-path`, `--inode-depth`, `--inode-top`)                                                                                                                      |
| `fshints`       | Prints **read-only** Btrfs/ZFS maintenance *suggestions* (no commands run)                                                                                                                             |
| `all`           | Runs a curated sweep: apt, apt-residuals, journal, logs, tmp, tmpfiles, usercache, langcaches, snap, flatpak, docker, podman, containerd, kernels, coredumps, buildcache, browsers, timeshift, fshints |

> Many tasks are **no-op** if the underlying tool isn’t installed (e.g., `snap`, `docker`, `flatpak`).

---

## ⚙️ Options

### Execution & Safety

These affect *how* cleanx runs:

* `--dry-run`
  Default. Show planned commands; do **not** modify the system.

* `--yes`
  Apply changes (disables `--dry-run`). Still asks for confirmation once.

* `--aggressive`
  Stronger cleanup where supported (e.g., `docker system prune -af --volumes`, podman volumes).

* `--low-impact`
  Wraps actions in `ionice -c3 nice -n 10` to reduce IO/CPU pressure.

* `--force`
  Suppress the ≥98% root-filesystem warning. Reclaim tasks are allowed to continue without this flag so a full filesystem does not disable the cleaner.

* `--secure-erase`
  Use `shred -zuf` for files before deleting directories in tasks that delete files. Slower but more privacy-friendly.

* `--quota=SIZE`
  Stop once at least `SIZE` has been reclaimed on `/`. Examples: `--quota=2G`, `--quota=800M`.
  Internally uses `df -B1 /` before & after tasks and compares.

* `--json`
  Emit exactly one JSON document on stdout with before/after usage, reclaimed bytes, tasks, etc. Human/progress output is redirected to stderr.

### Scope & Tuning

These control *what* is targeted and thresholds:

* `--journal-keep=VAL`
  How much journald to keep: time (e.g. `7d`, `12h`) or size (e.g. `200M`).
  Default: `7d`.

* `--log-max=SIZE`
  Truncate `*.log` files in `/var/log` larger than this.
  Default: `100M`.

* `--tmp-days=N`
  Delete `/tmp` entries older than `N` days.
  Default: `7`.

* `--snap-retain=N`
  How many Snap revisions to keep.
  Default: `2`.

* `--user=NAME`
  Target user for cache & browser cleaning (affects `usercache`, `langcaches`, `browsers`).
  Default: `SUDO_USER`, falling back to `$USER`.

* `--inode-path=PATH`
  Root path for `inode-scan`. Default: `.`

* `--inode-depth=N`
  Depth for `inode-scan` (`find ... -maxdepth N`). Default: `3`.

* `--inode-top=N`
  How many top directories by inode count to show in `inode-scan`. Default: `50`.

* `--exclude-glob=GLOB` (repeatable)
  Exclude paths globally in destructive `find` calls (e.g., logs/tmp).
  Internally turned into `find ... \( -path GLOB1 -o -path GLOB2 ... \) -prune -o`.

* `--include-glob=GLOB` (repeatable)
  Restrict some operations to specific names (e.g., log truncation).
  Used as additional `-name GLOB` filters where it makes sense.

### Config, Update & Utility

* `--config=PATH`
  Extra declarative `KEY=VALUE` config file. It is parsed, never sourced; command-line options retain highest precedence.

* `--channel=NAME`
  Version-check channel (branch/tag) for `--check-update`. Default: `stable`. `--update` intentionally remains on the checksum-verified stable release path.

* `--version`
  Print version and exit.

* `--check-update`
  Fetch remote script, parse its `VERSION`, compare, and print:

  ```text
  local:  1.7.0
  remote: 1.8.0  (channel: main)
  update_available: yes
  ```

  Exit code `10` when an update is available, `0` otherwise.

* `--update`
  Self-update from the repo (`RAW_BASE/<channel>/Clean/cleanx`), optional SHA256 verification if `.sha256` exists. Creates a backup: `cleanx.bak.<timestamp>`.

* `--print-config`
  Print effective configuration (after config files and CLI overrides):

  ```text
  cleanx v1.7.0 effective configuration
  ---------------------------------------------
  CHANNEL           = main
  JOURNAL_KEEP      = 7d
  LOG_MAX_SIZE      = 100M
  TMP_DAYS          = 7
  SNAP_RETAIN       = 2
  TARGET_USER       = hasan
  TARGET_HOME       = /home/hasan
  ...
  EXCLUDE_GLOBS     = /var/log/private/*
  INCLUDE_GLOBS     = *.log *.gz
  ```

* `--doctor`
  Environment/requirements check. Verifies required tools (`find`, `du`, `sort`, `awk`, `xargs`, `df`), reports missing optional ones, and prints `df -hT` prefixed with `FS:`.

* `--completions=bash|zsh`
  Print shell completions to stdout. You can redirect to the appropriate file.

* `--help` / `-h`
  Show usage and exit.

---

## 🧱 Safety Model

* **Dry-run first**
  Every run is read-only unless you explicitly add `--yes`.

* **Full-filesystem behavior**
  If `/` is ≥98% used, `cleanx` warns but continues with reclaim tasks. `--force` suppresses the warning; it is not required to recover disk space.

* **Locking**
  Mutating runs use non-blocking `flock` in `$XDG_RUNTIME_DIR`, `/run/lock`, or a private per-UID temporary directory. If `flock` is unavailable, an atomic lock directory is used. Read-only report-only runs do not take the mutation lock.

* **Exclusions**
  `--exclude-glob` globs are honored across destructive `find` calls so you can protect sensitive paths.

* **Secure erase is opt-in**
  Without `--secure-erase`, files are removed with normal `rm`/`find -delete`. With it, files are overwritten with `shred` before directory removal.

---

## ⚙️ Configuration

`cleanx` parses configuration as data; it never `source`s configuration files. Files use one `KEY=VALUE` assignment per line. Empty lines and `#` comments are ignored, unknown keys are warned and ignored, and shell syntax is never evaluated.

Configuration is loaded in this order, with later entries overriding earlier scalar values:

1. `/etc/cleanfy.conf` — legacy compatibility
2. `~/.config/cleanfy.conf` — legacy compatibility
3. `/etc/cleanx.conf` — preferred system path
4. `~/.config/cleanx.conf` (or `$XDG_CONFIG_HOME/cleanx.conf`) — preferred user path
5. `--config=/path/to/custom.conf`
6. command-line options — highest precedence

Legacy shell-array assignments are deliberately not executed. Use repeated singular entries for include/exclude patterns:

```text
# /etc/cleanx.conf
JOURNAL_KEEP=200M
LOG_MAX_SIZE=50M
TMP_DAYS=5
SNAP_RETAIN=3
CHANNEL=stable

EXCLUDE_GLOB=/var/log/private/*
EXCLUDE_GLOB=/var/tmp/keep/*
INCLUDE_GLOB=*.log
INCLUDE_GLOB=*.gz
```

`TARGET_HOME` cannot be supplied by config. `cleanx` resolves the home directory from the system account database for the validated `TARGET_USER` and refuses nonexistent users, non-absolute homes, or `/` as a target home.

See the effective runtime config:

```bash
cleanx --print-config
```

---

## 📊 JSON Report

Add `--json` to emit a JSON summary at the end:

```bash
sudo cleanx --yes --json logs tmp usercache
```

Example structure:

```json
{
  "tool": "cleanx",
  "version": "1.7.0",
  "channel": "stable",
  "timestamp": "2025-12-03T06:00:00Z",
  "mode": "apply",
  "aggressive": false,
  "low_impact": true,
  "secure_erase": false,
  "user": "hasan",
  "quota_bytes": 0,
  "quota_reached": false,
  "before_used_bytes": 1234567890,
  "after_used_bytes": 987654321,
  "reclaimed_bytes": 247914569,
  "tasks": ["logs", "tmp", "usercache"],
  "excludes": ["/var/log/private/*"],
  "includes": ["*.log", "*.gz"]
}
```

Fields:

* `mode` — dry-run vs apply
* `quota_bytes` / `quota_reached` — whether the quota target was hit
* `before_used_bytes` / `after_used_bytes` / `reclaimed_bytes` — based on `df -B1 /`
* `tasks` — executed tasks in order
* `excludes` / `includes` — globs in effect

---

## 🔄 Self-Update & Channels

Check remote version vs local:

```bash
cleanx --check-update        # exit 10 if newer version exists
```

Update to the latest checksum-verified stable release:

```bash
sudo cleanx --update
```

Compare against an explicit development branch/tag without changing the stable updater path:

```bash
cleanx --channel=develop --check-update
```

---

## ⌨️ Shell Completions

Generate completions and install:

```bash
# Bash
cleanx --completions=bash | sudo tee /etc/bash_completion.d/cleanx > /dev/null

# Zsh
cleanx --completions=zsh | sudo tee /usr/local/share/zsh/site-functions/_cleanx > /dev/null
```

Reload your shell or `source` the files to activate.

---

## ⏱️ systemd Timer (optional)

Run weekly at low impact:

**`/etc/systemd/system/cleanx.service`**

```ini
[Unit]
Description=cleanx cleanup

[Service]
Type=oneshot
ExecStart=/usr/local/bin/cleanx --yes --low-impact apt apt-residuals logs tmp tmpfiles usercache langcaches journal
Nice=10
IOSchedulingClass=idle
```

**`/etc/systemd/system/cleanx.timer`**

```ini
[Unit]
Description=Run cleanx weekly

[Timer]
OnCalendar=Sun *-*-* 03:15
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cleanx.timer
```

---

## 🧪 Doctor

```bash
cleanx --doctor
```

* Ensures required tools: `find`, `du`, `sort`, `awk`, `xargs`, `df`.
* Lists missing optional tools: `journalctl`, `apt`, `dpkg`, `snap`, `flatpak`, `docker`, `podman`, `ctr`, `lsof`, `numfmt`, `ccache`, `timeshift`, `btrfs`, `zfs`, `curl`, `sha256sum`, `shasum`.
* Prints `df -hT` (excluding squashfs/tmpfs/devtmpfs) as quick FS health.

---

## 🛠️ Advanced Examples

**1) Clean logs except a private tree; only touch `.log` & `.gz`:**

```bash
sudo cleanx --yes \
  --exclude-glob="/var/log/private/*" \
  --include-glob="*.log" \
  --include-glob="*.gz" \
  logs
```

**2) Inode meltdown debugging under `/var`:**

```bash
cleanx --report inode-scan \
  --inode-path=/var \
  --inode-depth=4 \
  --inode-top=100
```

**3) Minimal container host reclaim (fast & safe):**

```bash
sudo cleanx --yes docker containerd pkgbig
```

**4) Secure erase user caches + cap runtime with quota:**

```bash
sudo cleanx --yes --secure-erase --quota=2G usercache logs
```

**5) Full sweep for a workstation:**

```bash
sudo cleanx --yes --low-impact \
  apt apt-residuals logs tmp tmpfiles usercache langcaches \
  snap flatpak docker podman containerd browsers timeshift
```

---

## 🔐 Notes on Secure Erase

* `--secure-erase` uses `shred -zuf` on files before removing directories.
* It’s significantly slower than simple `rm`/`find -delete`.
* On CoW filesystems like Btrfs/ZFS, overwrite semantics are nuanced; see `fshints` for FS-native commands (printed read-only).

---

## 🧩 Compatibility

* Targeted at modern Debian/Ubuntu derivatives.
* Required tools are minimal; optional tasks quietly degrade if their tools aren’t present.

Examples of optional binaries:

* `journalctl`, `apt`, `dpkg`, `snap`, `flatpak`, `docker`, `podman`, `ctr`, `lsof`, `ccache`, `timeshift`, `btrfs`, `zfs`.

---

## 🧾 Exit Codes

* `0` — success
* `1` — generic error (missing tool, lock active, cancelled confirmation, checksum failure, etc.)
* `10` — `--check-update` found a newer version

---

## 🐎 Performance Tips

* Use `--low-impact` on busy nodes to be friendlier to latency-sensitive workloads.
* Prefer targeted runs (`logs tmp usercache`) for speed rather than always using `all`.
* Use `--quota=SIZE` when you “just need N GB back” and don’t care which task gets you there.
* Avoid `--secure-erase` unless you explicitly need overwrite semantics.
