# cleanx

`cleanx` is a **safe, modular, dry-run-by-default** disk & inode cleaner for Linux (Debian/Ubuntu focused).
Think “CCleaner for servers,” but **Bash-only, scriptable, and fast**.

* One file, zero exotic deps (just `bash`, `coreutils`, and common tools).
* Strict safety rails and **explicit flags**.
* Rich reports (blocks + inodes), JSON summary, quota-based runs.
* Self-update support + completions.

---

## ✨ Features

* **Dry-run by default** — prints actions; apply with `--yes`.
* **Safety preflight** — refuses to run if `/` is ≥98% used (override with `--force`).
* **Low-impact mode** — `ionice` + `nice` with `--low-impact`.
* **Tasks** for: APT, logs, journald, `/tmp`, user caches, language caches (Composer/npm/pnpm/yarn/pip), Snap/Flatpak, Docker/Podman/containerd, old kernels, coredumps, build caches, browser caches, Timeshift, package size view, FS hints.
* **Inode tooling** — inode df, hotspots, parameterized deep scans.
* **Configurable** — global & user config files + `--config=FILE`; include/exclude globs.
* **Secure erase** — `--secure-erase` to `shred` files before removal.
* **Quota** — stop when freed `SIZE`, e.g. `--quota=5G`.
* **JSON report** — `--json` prints a machine-friendly summary.
* **Self-update** — `--check-update`, `--update`, with `--channel` support.
* **Shell completions** — `--completions=bash|zsh`.
* **Doctor** — `--doctor` checks environment & prints quick FS state.
* **Locking** — prevents concurrent runs via `/tmp/.cleanfy.lock`.

---

## 📦 Install

Single-file install (matches Toolset layout):

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Clean/cleanx" \
  -o /usr/local/bin/cleanx && sudo chmod +x /usr/local/bin/cleanx
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
| `apt`           | `apt autoremove --purge -y` + `apt clean`                                                                                                                                                              |
| `apt-residuals` | Purges “rc” packages (residual configs)                                                                                                                                                                |
| `journal`       | Rotates and vacuums journald (`--vacuum-time` or `--vacuum-size` via `--journal-keep`)                                                                                                                 |
| `logs`          | Deletes rotated logs (`*.gz`) older than 14 days; truncates `*.log` over `--log-max`                                                                                                                   |
| `tmp`           | Deletes `/tmp` entries older than `--tmp-days` (via `find ... -mtime +N`)                                                                                                                              |
| `tmpfiles`      | Runs `systemd-tmpfiles --clean` if available                                                                                                                                                           |
| `usercache`     | Clears `$HOME/.cache`, thumbnails, and Trash for `--user` (default: `SUDO_USER`/`$USER`)                                                                                                               |
| `langcaches`    | Clears Composer/npm/pnpm/yarn/pip caches for target user via `su -`                                                                                                                                    |
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
  Run even if root filesystem (`/`) is ≥98% used. Without this, `cleanx` bails out as a safety precaution.

* `--secure-erase`
  Use `shred -zuf` for files before deleting directories in tasks that delete files. Slower but more privacy-friendly.

* `--quota=SIZE`
  Stop once at least `SIZE` has been reclaimed on `/`. Examples: `--quota=2G`, `--quota=800M`.
  Internally uses `df -B1 /` before & after tasks and compares.

* `--json`
  Print a JSON summary at the end with before/after usage, reclaimed bytes, tasks, etc.

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
  Extra config file to source (evaluated after global/user config, before CLI overrides).

* `--channel=NAME`
  Self-update/check channel (branch/tag). Default: `main`. Affects `--check-update` and `--update`.

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

* **RootFS guard**
  If `/` is ≥98% used, `cleanx` exits with a warning (unless `--force` is set). This prevents making a full-disk situation worse.

* **Locking**
  `cleanx` uses `/tmp/.cleanfy.lock` to guard against concurrent runs. If the lock exists, it refuses to start (you can manually remove the file if it’s stale).

* **Exclusions**
  `--exclude-glob` globs are honored across destructive `find` calls so you can protect sensitive paths.

* **Secure erase is opt-in**
  Without `--secure-erase`, files are removed with normal `rm`/`find -delete`. With it, files are overwritten with `shred` before directory removal.

---

## ⚙️ Configuration

`cleanx` sources config files **after internal defaults but before CLI args**, in this order:

1. `/etc/cleanfy.conf`
2. `~/.config/cleanfy.conf`
3. `--config=/path/to/custom.conf` (highest precedence)

These files are just shell snippets; they can set any of the global variables the script uses.

Example:

```bash
# /etc/cleanfy.conf
JOURNAL_KEEP="200M"
LOG_MAX_SIZE="50M"
TMP_DAYS=5
SNAP_RETAIN=3

EXCLUDE_GLOBS=(
  "/var/log/private/*"
  "/var/tmp/keep/*"
)
INCLUDE_GLOBS=(
  "*.log"
  "*.gz"
)

# Set default channel for self-update
CHANNEL="stable"
```

See your effective runtime config:

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
  "channel": "main",
  "timestamp": "2025-12-03T06:00:00Z",
  "mode": "apply",
  "aggressive": 0,
  "low_impact": 1,
  "secure_erase": 0,
  "user": "hasan",
  "quota_bytes": 0,
  "quota_reached": 0,
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

Update to the latest version from a channel (default: `main`):

```bash
sudo cleanx --update
```

Use an alternate branch/tag as the channel:

```bash
sudo cleanx --channel=develop --update
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
