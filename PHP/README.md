# phpx

`phpx` is a **PHP toolkit & manager** for Debian/Ubuntu-like systems.

It wraps the usual “install / switch / inspect / tune” PHP tasks into a single script, without hiding what’s going on underneath.

---

## Features

- **Version lifecycle**
  - Install / list / switch PHP versions (CLI + FPM) via apt + Sury/Ondřej repos
  - Safely remove PHP versions and related packages
- **Extensions & cleanup**
  - Discover, install and remove `phpX.Y-*` extensions
  - Clean broken `.so` references from `.ini` files (`clean`)
- **Health & diagnostics**
  - Run sanity checks (`doctor`) for a PHP version
  - Get a summarized config view (`info`) with OPcache/JIT/FPM hints
- **Composer & PECL**
  - Install/update Composer globally
  - Install multiple PECL packages in one go
- **Runtime helpers**
  - Start PHP’s built-in web server safely (`serve`)
  - Run scripts under a specific PHP version (`run`)
- **Configs & repos**
  - Generate tuned `php.ini` + FPM pool configs (`generate-config`)
  - Add Sury/Ondřej PHP repositories (`sury`)
- **Script lifecycle**
  - Self-update from GitHub (`self-update`)
  - Per-day logging with env-based overrides

High-impact commands (`switch`, `install`, `remove`, `sury`, `self-update`) run basic system checks (disk space, curl/wget,
network) before touching apt or remote endpoints.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/PHP/phpx" \
  -o /usr/local/bin/phpx && sudo chmod +x /usr/local/bin/phpx
````

---

## Requirements

* Debian/Ubuntu or derivative (uses `apt`, `dpkg`, `lsb_release`, `systemctl`, etc.)
* For most commands:

    * `php` binaries (`phpX.Y`), `php-fpm` units if FPM is used
* For repo / package management:

    * `curl`, `wget`, `software-properties-common` (auto-installed when possible)
* For Composer:

    * `curl` (auto-installed when run as root)
* For logs:

    * Writable log directory (`/var/log/phpx` as root, `~/.local/phpx_logs` as user)

---

## Usage at a Glance

```bash
phpx {list | info | doctor | switch | ext | install | serve | run | remove | generate-config | sury | clean | self-update} <args>
```

### Command aliases

* `switch` → `s`
* `ext` → `extensions`, `x`
* `install` → `i`

### Commands that usually require `sudo`

Anything that installs/removes packages or touches system config:

* `switch`, `ext`, `install`, `remove`, `generate-config`, `sury`, `clean`, `self-update`
* Plus any path that ends up calling apt / dpkg or writing into `/etc`, `/usr/local/bin`, etc.

---

## Commands Overview

| Command                       | Summary                                                        |                                                              |                                           |
| ----------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------- |
| `list`                        | List installed PHP versions (CLI + FPM state, current default) |                                                              |                                           |
| `info [X.Y]`                  | Summarized phpinfo-style view for a version                    |                                                              |                                           |
| `doctor [X.Y] [--fix]`        | Sanity checks + optional auto-fix for a version                |                                                              |                                           |
| `switch                       | s <X.Y> [--no-web]`                                            | Switch default CLI to `X.Y`, optionally configure web server |                                           |
| `ext                          | extensions                                                     | x [X.Y] [...]`                                               | Discover/install extensions for a version |
| `install                      | i composer`                                                    | Install/update Composer globally                             |                                           |
| `install                      | i <pecl1,pecl2,...>`                                           | Install PECL packages                                        |                                           |
| `serve [options]`             | Start PHP built-in web server safely                           |                                                              |                                           |
| `run <script.php> [X.Y]`      | Run script with a specific PHP version                         |                                                              |                                           |
| `remove <X.Y>`                | Remove PHP `X.Y` and related packages                          |                                                              |                                           |
| `remove <X.Y> ext [...]`      | Remove extensions for PHP `X.Y`                                |                                                              |                                           |
| `remove ext [...]`            | Remove extensions for detected default version                 |                                                              |                                           |
| `generate-config <env> <X.Y>` | Generate `php.ini` + FPM pool configs (prod/dev)               |                                                              |                                           |
| `sury`                        | Add Sury/Ondřej PHP repo for Debian/Ubuntu                     |                                                              |                                           |
| `clean [X.Y]`                 | Clean broken extension `.ini` entries                          |                                                              |                                           |
| `self-update`                 | Update `phpx` script from GitHub                               |                                                              |                                           |

---

## Command Details

### 1. Version Lifecycle

#### `list`

```bash
phpx list
```

* Lists installed PHP versions (`phpX.Y` packages).
* Shows:

    * CLI binary path per version (if any)
    * FPM state: active / installed / not present
    * Current `php` default and its version

---

#### `switch` / `s`

```bash
phpx switch 8.2
phpx s 8.3
phpx switch 8.2 --no-web
```

* Verifies or installs `php8.2`, `php8.2-cli`, `php8.2-fpm` as needed.
* Cleans missing extensions for that version.
* Updates `update-alternatives` for:

    * `php`
    * `phar`
    * `phar.phar`
* By default, runs a web-server configuration helper:

    * Detects installed web servers (`apache2`, `nginx`, `lighttpd`)
    * Offers to configure Apache for:

        * PHP-FPM (`phpX.Y-fpm`) **or**
        * `libapache2-mod-phpX.Y` (mod_php)
    * For Nginx/Lighttpd, prints the appropriate `fastcgi` socket.
* Use `--no-web` to skip the server configuration wizard (good for CI / CLI-only boxes).

> System checks (disk + network + curl/wget) run before any apt usage.

---

#### `remove`

```bash
# Remove a PHP version
phpx remove 7.4

# Remove extensions for a specific version (interactive)
phpx remove 8.1 ext

# Remove extensions for auto-detected default version (interactive)
phpx remove ext

# Non-interactive extension removal by name
phpx remove 8.1 ext --remove=redis,imagick
```

* If the first arg looks like `X.Y`:

    * `remove <X.Y>`:

        * Stops + disables `phpX.Y-fpm` if present
        * Purges all `phpX.Y-*` packages via apt
        * Runs apt autoremove
    * `remove <X.Y> ext [--remove="ext1,ext2"]`:

        * Removes only specified extensions (`phpX.Y-ext`) for that version
        * Interactive selection if `--remove` is omitted
* If the first arg is **not** a version:

    * `remove ext [...]`:

        * Operates on auto-detected default CLI version

---

### 2. Health & Diagnostics

#### `info`

```bash
phpx info 8.3
phpx info           # uses current default CLI version
```

Shows a summarized `php -i` / `php -m` view for the chosen version:

* Binary path (`/usr/bin/phpX.Y` or `/usr/local/bin/phpX.Y`)
* Loaded `php.ini`, additional `.ini` scan dir, `extension_dir`
* Key runtime settings:

    * `memory_limit`, `max_execution_time`, `post_max_size`, `upload_max_filesize`, etc.
* FPM overview:

    * Service state (`phpX.Y-fpm`): active / installed / missing
    * Pool dir: `/etc/php/X.Y/fpm/pool.d`
    * Selected FPM settings when available:

        * `listen`, `pm`, `pm.max_children`, min/max spare, `pm.max_requests`
        * slowlog path and `request_slowlog_timeout`
* Extensions:

    * Total modules from `php -m`
    * `apt`-level extension packages: `phpX.Y-*`
    * `xdebug` presence
* OPcache & JIT snapshot:

    * `opcache.*`, `opcache.jit*` values
* Best-effort performance hints (e.g., disabled OPcache, small opcache memory, JIT off, xdebug in non-dev)

---

#### `doctor`

```bash
phpx doctor           # uses current default CLI version
phpx doctor 8.2
phpx doctor 8.2 --fix
```

Runs sanity checks for a version and prints actionable hints:

* CLI vs FPM:

    * Default CLI version vs inspected version
    * `phpX.Y-fpm` service state
* Broken extensions:

    * Parses `php -m` stderr for “Unable to load dynamic library …”
    * Lists missing `.so` entries and suggests `phpx clean <X.Y>`
* Apache `mod_php`:

    * Detects enabled `phpX.Y_module` variants
    * Warns if multiple modules are enabled
* FPM sizing hints:

    * Uses system RAM to derive a recommended `pm.max_children` ballpark
* Runtime checks:

    * Too low `memory_limit`
    * `max_execution_time` unusually high
    * `upload_max_filesize > post_max_size`
    * Dev-style `display_errors On` + `log_errors Off`
* OPcache & JIT hints:

    * OPcache disabled / tiny memory
    * Frequent revalidation (dev vs prod)
    * JIT effectively disabled
* `xdebug` warnings in non-dev setups

With `--fix`:

* Runs the same checks plus:

    * Cleans broken `.ini` extension references (same behavior as `phpx clean <X.Y>`)
    * On Apache, can disable extra `mod_php` modules, keeping a single version active (best-effort).

---

### 3. Extensions & Cleanup

#### `ext` / `extensions` / `x`

```bash
# Use detected default version
phpx ext

# Work on a specific version
phpx ext 8.3

# Non-interactive install for a version
phpx ext 8.2 --install=redis,imagick

# Force “yes” answers via env
PHPX_ASSUME_YES=1 phpx ext 8.2 --install=redis
```

* If no version is given:

    * Uses the currently active CLI version.
* Shows:

    * All installed extensions from apt: `phpX.Y-*`
    * All installable extensions from `apt-cache` for `phpX.Y-*`, excluding ones already installed.
* Interactive mode:

    * Enter numbers or names (comma-separated) to select extensions.
* Non-interactive mode:

    * Use `--install=ext1,ext2` to install by extension name.
* Behavior:

    * Auto-installs `phpX.Y` if missing.
    * Cleans stale/missing extension references first.
    * Installs selected apt packages, then:

        * Runs `phpenmod -v X.Y <ext>`
        * Reloads `phpX.Y-fpm` if running.

---

#### `clean`

```bash
phpx clean        # uses current default version
phpx clean 8.2
```

* Parses `php -m` output for “Unable to load dynamic library …” lines.
* For each missing `.so`:

    * Finds matching `.ini` files under `/etc/php/X.Y`
    * Removes those `.ini` files
* Safe to run multiple times; only broken entries are targeted.

---

### 4. Composer & PECL

#### `install composer`

```bash
phpx install composer
phpx i composer
```

* Ensures `curl` is installed (installs via apt if run as root).
* Installs Composer using the official installer:

    * Downloads installer via `curl`
    * Places `composer` into `/usr/local/bin/composer`
* Runs `composer self-update` to bring it to latest stable.

---

#### `install <pecl1,pecl2,...>`

```bash
phpx install xdebug,redis apcu
phpx i xdebug, redis apcu
```

* Accepts:

    * Comma-separated names
    * Space-separated names
    * Or a mix of both
* Ensures PECL is ready:

    * Installs `php-pear` and `php-dev` via apt if needed.
* For each package:

    * Skips if already installed (per `pecl list`)
    * Otherwise runs `pecl install <package>`

> You still need to enable PECL extensions in PHP configs as usual (e.g., adding `.ini` files under `/etc/php/X.Y/mods-available`).

---

### 5. Runtime Helpers

#### `serve`

```bash
phpx serve
phpx serve --host=0.0.0.0 --port=8080
phpx serve --root=/var/www/app --router=router.php -v
```

Options:

* `--host <host>` (default: `127.0.0.1`)
* `--port <port>` (default: `8000`)
* `--root <dir>` (default: current directory)
* `--router <file>` (custom router script)
* `-v`, `--verbose` (extra output)

Behavior:

1. Ensures a `php` CLI is available.
2. Validates `--root` directory.
3. Checks port availability via `lsof` / `ss` / `netstat` when present.
4. If no `--router` is given, auto-discovers a likely document root by probing (in order):

    * `ROOT/public/index.php`
    * `ROOT/public/index.html`
    * `ROOT/index.php`
    * `ROOT/index.html`
5. If `--router` is supplied, it must exist; otherwise the command fails.
6. Launches:

```bash
php -S host:port -t <found_root> [router.php]
```

---

#### `run`

```bash
phpx run bin/script.php
phpx run bin/script.php 8.2
```

* Validates script existence.
* If `X.Y` is omitted:

    * Uses active default CLI version (from `php`).
* If `X.Y` is not installed:

    * Attempts to install that PHP version.
* Executes via:

    * `/usr/bin/phpX.Y` or `/usr/local/bin/phpX.Y`

---

### 6. Config Generator

#### `generate-config`

```bash
phpx generate-config production 8.2
phpx generate-config development 8.3
```

* Arguments:

    * `environment` ∈ `production` | `development`
    * `X.Y` PHP version (e.g., `8.2`, `8.3`)
* Outputs in current directory:

    * `fpm.<environment>.conf`
    * `php.<environment>.ini`
* Behavior:

    * Reads total system RAM (`free -m`).
    * Calculates FPM settings:

        * `pm.max_children` with min/max bounds
        * `pm.start_servers`, `pm.min_spare_servers`, `pm.max_spare_servers`
    * Sets environment-specific values:

        * Execution times, upload limits
        * Error display vs logging (dev vs prod)
        * OPcache memory, accelerated files, validation frequency
        * JIT mode + buffer size per environment

You can then merge these templates into your actual `/etc/php/X.Y` configs.

---

### 7. Repositories & Self-Update

#### `sury`

```bash
phpx sury
```

* Reads OS info from `/etc/os-release` and `lsb_release -sc`.
* On Ubuntu (or Ubuntu-like):

    * Installs `software-properties-common` if needed.
    * Adds `ppa:ondrej/php` when missing.
* On Debian (or Debian-like):

    * Verifies that codename is supported by `packages.sury.org`.
    * Installs Sury keyring & adds appropriate `deb` line.
* Runs `apt update` afterwards.

---

#### `self-update`

```bash
phpx self-update
```

* Downloads latest script from:

    * `https://raw.githubusercontent.com/infocyph/Toolset/main/PHP/phpx`

* Compares SHA-256 of local vs downloaded version.

* If identical:

    * Prints “already up-to-date” and exits.

* If different:

    * Replaces `/usr/local/bin/phpx` with the new file.
    * Marks it executable.

---

## Logging & Environment

By default, `phpx` logs to per-day log files:

* As root:
  `/var/log/phpx/YYYY-MM-DD.log`
* As non-root:
  `$HOME/.local/phpx_logs/YYYY-MM-DD.log`

Each log entry includes:

* Timestamp
* Level (`INFO` / `WARN` / `ERROR`)
* Short message

### Environment variables

* `PHPX_LOG_DIR`
  Override log directory (for both root and non-root runs).

* `PHPX_NO_LOG`
  If set (to anything), disables file logging entirely.

* `PHPX_ASSUME_YES`
  If set, treats operations as if `-y` / `--yes` were passed where applicable.
  Useful for non-interactive flows around:

    * `switch`, `install`, `remove`, `sury`, `self-update` and extension management.

---

## Quick Examples

```bash
# Show installed versions and current default
phpx list

# Inspect config for PHP 8.3
phpx info 8.3

# Run doctor with auto-fix on 8.2
phpx doctor 8.2 --fix

# Switch default CLI to 8.2 without touching web server configs
phpx switch 8.2 --no-web

# Install redis and imagick for 8.2 non-interactively
phpx ext 8.2 --install=redis,imagick

# Install Composer globally
phpx install composer

# Start a dev server on 0.0.0.0:8080
phpx serve --host=0.0.0.0 --port=8080

# Generate production-tuned configs for 8.2
phpx generate-config production 8.2

# Add Sury/Ondřej repo and refresh apt
phpx sury

# Update phpx itself
phpx self-update
```

---

`phpx` is part of the **Toolset** collection. See the main repo README for an overview of the other tools.
