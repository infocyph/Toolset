#!/usr/bin/env python3
from pathlib import Path

script = Path("Clean/cleanx")
text = script.read_text()

replacements = [
    (
        "  --channel=NAME            update/check channel (default: stable)\n",
        "  --channel=NAME            channel for --check-update (default: stable); --update stays stable\n",
    ),
    (
        "  --update                  self-update to latest from --channel\n",
        "  --update                  self-update from the latest checksum-verified stable release\n",
    ),
]
for old, new in replacements:
    if old not in text:
        raise SystemExit(f"cleanx help text not found: {old!r}")
    text = text.replace(old, new, 1)
script.write_text(text)

readme = Path("Clean/README.md")
doc = readme.read_text()

replacements = [
    (
        "`cleanx` is a **safe, modular, dry-run-by-default** disk & inode cleaner for Linux (Debian/Ubuntu focused).",
        "`cleanx` is a **safe, modular, dry-run-by-default** disk & inode cleaner for Linux.",
    ),
    (
        "* **Safety preflight** — refuses to run if `/` is ≥98% used (override with `--force`).",
        "* **Safety preflight** — warns when `/` is ≥98% used but still permits reclaim operations; `--force` suppresses that warning.",
    ),
    (
        "* **Tasks** for: APT, logs, journald, `/tmp`, user caches, language caches (Composer/npm/pnpm/yarn/pip), Snap/Flatpak, Docker/Podman/containerd, old kernels, coredumps, build caches, browser caches, Timeshift, package size view, FS hints.",
        "* **Tasks** for: package cleanup (APT/DNF/Zypper with explicit safe skips elsewhere), logs, journald, `/tmp`, user caches, language caches (Composer/npm/pnpm/yarn/pip), Snap/Flatpak, Docker/Podman/containerd, old kernels where supported, coredumps, build caches, browser caches, Timeshift, package size view, FS hints.",
    ),
    (
        "* **Configurable** — global & user config files + `--config=FILE`; include/exclude globs.",
        "* **Configurable** — declarative `KEY=VALUE` global/user config + `--config=FILE`; config files are never sourced as shell code.",
    ),
    (
        "* **JSON report** — `--json` prints a machine-friendly summary.",
        "* **JSON report** — `--json` reserves stdout for one parseable JSON document; operational output is sent to stderr.",
    ),
    (
        "* **Self-update** — `--check-update`, `--update`, with `--channel` support.",
        "* **Self-update** — `--update` uses the checksum-verified latest stable release; `--channel` can be used for explicit branch/tag version checks.",
    ),
    (
        "* **Locking** — prevents concurrent runs via `/tmp/.cleanfy.lock`.",
        "* **Locking** — prevents concurrent mutation runs with `flock` in the runtime/lock directory and an atomic private-directory fallback.",
    ),
    (
        "| `apt`           | `apt autoremove --purge -y` + `apt clean`",
        "| `packages` / `apt` | Package cleanup backend: APT (`autoremove` + `clean`), DNF (`autoremove` + `clean all`), Zypper cache cleanup, or an explicit safe skip when no supported automatic policy exists",
    ),
    (
        "| `langcaches`    | Clears Composer/npm/pnpm/yarn/pip caches for target user via `su -`",
        "| `langcaches`    | Clears Composer/npm/pnpm/yarn/pip caches for the validated target user via `runuser` when available",
    ),
    (
        "* `--force`\n  Run even if root filesystem (`/`) is ≥98% used. Without this, `cleanx` bails out as a safety precaution.",
        "* `--force`\n  Suppress the ≥98% root-filesystem warning. Reclaim tasks are allowed to continue without this flag so a full filesystem does not disable the cleaner.",
    ),
    (
        "* `--json`\n  Print a JSON summary at the end with before/after usage, reclaimed bytes, tasks, etc.",
        "* `--json`\n  Emit exactly one JSON document on stdout with before/after usage, reclaimed bytes, tasks, etc. Human/progress output is redirected to stderr.",
    ),
    (
        "* `--config=PATH`\n  Extra config file to source (evaluated after global/user config, before CLI overrides).",
        "* `--config=PATH`\n  Extra declarative `KEY=VALUE` config file. It is parsed, never sourced; command-line options retain highest precedence.",
    ),
    (
        "* `--channel=NAME`\n  Self-update/check channel (branch/tag). Default: `main`. Affects `--check-update` and `--update`.",
        "* `--channel=NAME`\n  Version-check channel (branch/tag) for `--check-update`. Default: `stable`. `--update` intentionally remains on the checksum-verified stable release path.",
    ),
    (
        "* **RootFS guard**\n  If `/` is ≥98% used, `cleanx` exits with a warning (unless `--force` is set). This prevents making a full-disk situation worse.",
        "* **Full-filesystem behavior**\n  If `/` is ≥98% used, `cleanx` warns but continues with reclaim tasks. `--force` suppresses the warning; it is not required to recover disk space.",
    ),
    (
        "* **Locking**\n  `cleanx` uses `/tmp/.cleanfy.lock` to guard against concurrent runs. If the lock exists, it refuses to start (you can manually remove the file if it’s stale).",
        "* **Locking**\n  Mutating runs use non-blocking `flock` in `$XDG_RUNTIME_DIR`, `/run/lock`, or a private per-UID temporary directory. If `flock` is unavailable, an atomic lock directory is used. Read-only report-only runs do not take the mutation lock.",
    ),
]
for old, new in replacements:
    if old not in doc:
        raise SystemExit(f"README text not found: {old[:120]!r}")
    doc = doc.replace(old, new, 1)

start = doc.find("## ⚙️ Configuration\n")
end = doc.find("\n---\n\n## 📊 JSON Report", start)
if start == -1 or end == -1:
    raise SystemExit("README configuration section markers missing")
config_section = '''## ⚙️ Configuration

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
'''
doc = doc[:start] + config_section + doc[end:]

# JSON examples now use JSON booleans and the stable channel.
doc = doc.replace('  "channel": "main",', '  "channel": "stable",', 1)
doc = doc.replace('  "aggressive": 0,\n  "low_impact": 1,\n  "secure_erase": 0,', '  "aggressive": false,\n  "low_impact": true,\n  "secure_erase": false,', 1)
doc = doc.replace('  "quota_reached": 0,', '  "quota_reached": false,', 1)

doc = doc.replace(
    "Update to the latest version from a channel (default: `main`):",
    "Update to the latest checksum-verified stable release:",
    1,
)
doc = doc.replace(
    "Use an alternate branch/tag as the channel:\n\n```bash\nsudo cleanx --channel=develop --update\n```",
    "Compare against an explicit development branch/tag without changing the stable updater path:\n\n```bash\ncleanx --channel=develop --check-update\n```",
    1,
)

readme.write_text(doc)
