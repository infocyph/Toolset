# cleanx

`cleanx` is a **safe, modular, dry-run-by-default** disk & inode cleaner for Linux (Debian/Ubuntu focused).
Think “CCleaner for servers,” but **Bash-only, scriptable, and fast**.

* One file, zero deps (only coreutils + tools already on most hosts).
* Strict safety rails and **explicit flags**.
* Rich reports (blocks + inodes), JSON summary, quota-based runs.
* Self-update support + completions.

---

## ✨ Features

* **Dry-run by default** — print actions first; apply with `--yes`.
* **Safety preflight** — backs off if `/` is ≥98% used (override with `--force`).
* **Low-impact mode** — `ionice` + `nice` with `--low-impact`.
* **Tasks** covering APT, logs, journald, `/tmp`, user caches, language caches (Composer/npm/pnpm/yarn/pip), Snap/Flatpak, Docker/Podman/containerd, old kernels, coredumps, build caches, browser caches, Timeshift.
* **Inode tooling** — per-filesystem inodes, hotspots, parameterized deep scans.
* **Configurable** — global & user config files + `--config=FILE`; include/exclude globs.
* **Secure erase** — `--secure-erase` to `shred` files before removal.
* **Quota** — stop when freed `SIZE`, e.g. `--quota=5G`.
* **JSON report** — `--json` prints a machine-friendly summary.
* **Self-update** — `--check-update`, `--update`.
* **Shell completions** — `--completions=bash|zsh`.
* **Doctor** — `--doctor` checks environment & prints quick FS state.

---

## 📦 Install

Single-file install (recommended path matches Toolset layout):

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

---

## 🔧 Usage

```
cleanx [options] <tasks...>
```

### Tasks

| Task            | What it does                                                                        |
| --------------- | ----------------------------------------------------------------------------------- |
| `report`        | Prints FS usage (blocks & inodes), top-heavy dirs, hotspots, deleted-but-open files |
| `apt`           | `apt autoremove --purge` + `apt clean`                                              |
| `apt-residuals` | Purges “rc” packages (residual configs)                                             |
| `journal`       | Rotates & vacuums journald (keep by time/size)                                      |
| `logs`          | Deletes rotated logs older than 14d and truncates `*.log` over `--log-max`          |
| `tmp`           | Deletes `/tmp` entries older than `--tmp-days`                                      |
| `tmpfiles`      | Runs `systemd-tmpfiles --clean`                                                     |
| `usercache`     | Clears `$HOME` caches & trash (respects `--user`)                                   |
| `langcaches`    | Clears Composer/npm/pnpm/yarn/pip caches (per-user)                                 |
| `snap`          | Retains `--snap-retain` revisions; removes disabled & saved snapshots               |
| `flatpak`       | Uninstalls unused, removes `--delete-data`                                          |
| `docker`        | `docker system prune -af` (add `--aggressive` to include volumes)                   |
| `podman`        | Prunes system; with `--aggressive` also prunes volumes                              |
| `containerd`    | Removes untagged images via `ctr`                                                   |
| `kernels`       | Removes old kernels via `apt autoremove --purge`                                    |
| `coredumps`     | Removes `core* > 50M` and `/var/crash/*` (with `--secure-erase` uses `shred`)       |
| `buildcache`    | Clears `ccache`/`distcc` if present                                                 |
| `browsers`      | Clears Chromium/Chrome/Firefox caches                                               |
| `timeshift`     | Keeps last 3 of hourly/daily/weekly/monthly                                         |
| `pkgbig`        | Lists top 30 packages by installed size                                             |
| `inode-scan`    | Parameterized inode hotspot scan (`--inode-path`, `--inode-depth`, `--inode-top`)   |
| `fshints`       | Prints **safe** Btrfs/ZFS maintenance hints                                         |
| `all`           | Bundles sane tasks for full cleanup (no destructive FS ops)                         |

### Options (selected)

* **Execution & safety**

    * `--dry-run` (default) • `--yes` (apply) • `--low-impact` • `--force`
* **Scope & tuning**

    * `--journal-keep=7d|200M` • `--log-max=100M` • `--tmp-days=7` • `--snap-retain=2`
    * `--user=NAME` (target user whose caches to clear)
    * `--exclude-glob=GLOB` (repeatable, prunes from destructive `find` calls)
    * `--include-glob=GLOB` (repeatable, name filter for some tasks, e.g., logs)
* **Privacy & quotas**

    * `--secure-erase` (use `shred -zuf` before delete) • `--quota=SIZE` (stop after freeing SIZE)
* **Reports & config**

    * `--json` (print JSON summary) • `--config=FILE` (extra config)
* **Update & extras**

    * `--version`, `--check-update`, `--update`, `--channel=main|tag|branch`
    * `--print-config`, `--doctor`, `--completions=bash|zsh`

Run `cleanx --help` for the full list.

---

## 🧱 Safety Model

* **Dry-run first**: You must pass `--yes` to make changes.
* **RootFS guard**: Aborts if `/` is ≥98% used (avoid worsening full-disk scenarios). Bypass with `--force`.
* **Locking**: prevents concurrent runs (`/tmp/.cleanfy.lock`).
* **Exclusion support**: `--exclude-glob` is respected across destructive `find` calls.
* **Secure erase optional**: `--secure-erase` uses `shred` on files, then removes directories.

---

## ⚙️ Configuration

`cleanx` loads these files (if present) **after defaults but before CLI args**:

* `/etc/cleanfy.conf`
* `~/.config/cleanfy.conf`
* `--config=/path/to/custom.conf` (highest precedence)

Example config:

```bash
# /etc/cleanfy.conf
JOURNAL_KEEP="200M"
LOG_MAX_SIZE="50M"
TMP_DAYS=5
SNAP_RETAIN=2
EXCLUDE_GLOBS=( "/var/log/private/*" "/var/tmp/keep/*" )
INCLUDE_GLOBS=( "*.log" "*.gz" )
```

Check the **effective** configuration at any time:

```bash
cleanx --print-config
```

---

## 📊 JSON Report

Add `--json` to print a summary object to stdout:

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
  "tasks": ["logs","tmp","usercache"],
  "excludes": ["/var/log/private/*"],
  "includes": ["*.log","*.gz"]
}
```

---

## 🔄 Self-Update

Compare & update from the repo (defaults to `--channel=main`):

```bash
cleanx --check-update
sudo cleanx --update
```

---

## ⌨️ Shell Completions

Generate to stdout and save:

```bash
# Bash
cleanx --completions=bash | sudo tee /etc/bash_completion.d/cleanx > /dev/null
# Zsh
cleanx --completions=zsh | sudo tee /usr/local/share/zsh/site-functions/_cleanx > /dev/null
```

---

## ⏱️ systemd Timer (optional)

Run weekly at low impact:

`/etc/systemd/system/cleanx.service`

```ini
[Unit]
Description=cleanx cleanup

[Service]
Type=oneshot
ExecStart=/usr/local/bin/cleanx --yes --low-impact apt apt-residuals logs tmp tmpfiles usercache langcaches journal
Nice=10
IOSchedulingClass=idle
```

`/etc/systemd/system/cleanx.timer`

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

* Validates required tools (`find`, `du`, `sort`, `awk`, `xargs`, `df`).
* Notes optional tools (`journalctl`, `snap`, `docker`, etc.).
* Prints FS table for quick inspection.

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
cleanx --report inode-scan --inode-path=/var --inode-depth=4 --inode-top=100
```

**3) Minimal container host reclaim (fast & safe):**

```bash
sudo cleanx --yes docker containerd pkgbig
```

**4) Secure erase user caches + cap runtime with quota:**

```bash
sudo cleanx --yes --secure-erase --quota=2G usercache logs
```

---

## 🔐 Notes on Secure Erase

* `--secure-erase` uses `shred -zuf` (overwrite + remove). It’s **slower**, but privacy-safer.
* On copy-on-write FS (e.g., Btrfs/ZFS), overwrite guarantees are nuanced. Consider FS-native snapshot pruning (see `fshints` task).

---

## 🧩 Compatibility

* Tested on modern Debian/Ubuntu derivates.
* Requires common base tools; optional tasks gracefully **no-op** if their tool isn’t installed:

    * `journal`, `snap`, `flatpak`, `docker`, `podman`, `ctr`, `timeshift`, `ccache`, `lsof`, `btrfs`, `zfs`.

---

## ❓ FAQ

**Q: Why dry-run by default?**
To make destructive actions explicit. Pass `--yes` to apply.

**Q: It says the root filesystem is ≥98% and exits.**
Safety guard to avoid worsening a full disk. If you know what you’re doing, add `--force`.

**Q: Can I target a different user’s caches?**
Yes: `--user=NAME` (requires privileges to remove their files).

**Q: How do includes/excludes work?**
`--exclude-glob` is turned into a `find ... -path GLOB -prune` across destructive tasks.
`--include-glob` is used as `-name GLOB` where sensible (e.g., active logs truncation).

---

## 🧹 What `all` Runs

`apt`, `apt-residuals`, `journal`, `logs`, `tmp`, `tmpfiles`, `usercache`, `langcaches`, `snap`, `flatpak`, `docker`, `podman`, `containerd`, `kernels`, `coredumps`, `buildcache`, `browsers`, `timeshift`, `fshints`.

It **does not** run dangerous filesystem operations; it’s a curated, sane default sweep.

---

## 🧾 Exit Codes

* `0` success
* `1` generic error (missing tool, lock active, cancelled confirmation, checksum fail, etc.)
* `10` `--check-update` found a newer version

---

## 🐎 Performance Tips

* Use `--low-impact` on busy nodes.
* Prefer scoped runs (`logs tmp usercache`) for speed.
* Use `--quota=SIZE` to **stop early** after enough space is reclaimed.
* Avoid `--secure-erase` unless required (it’s significantly slower).

