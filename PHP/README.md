# phpx

`phpx` is a **PHP toolkit & manager** for Debian/Ubuntu-like systems:

- Install / list / switch PHP versions (CLI + FPM) via apt + Sury/Ondřej repos
- Manage extensions (apt-based) and clean broken `.so` references
- Run health checks (`doctor`) and summarized config (`info`)
- Manage Composer + PECL packages
- Start PHP’s built-in web server safely (`serve`)
- Generate tuned `php.ini` + FPM pool configs (`generate-config`)
- Self-update the `phpx` script itself
- Log actions per-day, with optional override/disable via env vars

High-impact commands (`switch`, `install`, `remove`, `sury`, `self-update`) run basic system checks (disk space, curl/wget,
network) before touching apt or remote endpoints.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/PHP/phpx" \
  -o /usr/local/bin/phpx && sudo chmod +x /usr/local/bin/phpx
````

---

## Usage

```bash
phpx {list | info | doctor | switch | ext | install | serve | run | remove | generate-config | sury | clean | self-update} <args>
```

Aliases:

* `switch` = `s`
* `ext` = `extensions` = `x`
* `install` = `i`

Some commands require root (via `sudo`):

* `switch`, `ext`, `install`, `remove`, `generate-config`, `sury`, `clean`, `self-update` and any path that ends up
  installing/removing packages or modifying system config.

---

## Core Features

### Version lifecycle

* **`list`** – show installed PHP versions (CLI + FPM state) and default CLI.
* **`switch <X.Y> [--no-web]`** – switch default CLI to `X.Y` (installs if missing, updates `update-alternatives`,
  runs web-server helper unless `--no-web` is passed).
* **`remove <X.Y>`** – purge PHP `X.Y` and related packages (stops/disables FPM, purges matching `phpX.Y-*` packages).

### Health & diagnostics

* **`info [X.Y]`** – summarized `php -i` for a version: binary, ini paths, memory limits, opcache/JIT, extension count,
  FPM state.
* **`doctor <X.Y> [--fix]`** – sanity checks for a version:

    * CLI vs FPM mismatch
    * broken extension `.so` entries
    * Apache `mod_php` conflicts
    * FPM `pm.max_children` hint based on system RAM
      With `--fix`, it also calls `clean` and de-duplicates Apache PHP modules.

### Extensions & cleanup

* **`ext [X.Y] [--install="ext1,ext2"]`** (`extensions`, `x`)

    * If no version is provided, uses current CLI version.
    * Lists installed extensions (`phpX.Y-*` packages).
    * Lists installable extensions from `apt-cache`.
    * Interactive selection to install new ones, *or* non-interactive name list via `--install=...`.
* **`clean [X.Y]`**

    * Parses `php -m` errors for “Unable to load dynamic library …”.
    * Removes `.ini` files pointing to missing extension `.so` files for that version.

### Composer & PECL

* **`install composer`**

    * Ensures `curl` exists (installs it if run as root).
    * Installs Composer globally to `/usr/local/bin/composer`.
    * Runs `composer self-update`.
* **`install <pecl1,pecl2,...>`**

    * Accepts comma and/or space separated lists (`xdebug,redis apcu`).
    * Ensures `pecl` exists (`php-pear` + `php-dev` via apt).
    * Installs each PECL package, skipping already-installed ones.

### Built-in server

* **`serve [--host H] [--port P] [--root DIR] [--router FILE] [-v]`**

    * Checks default `php` exists.

    * Validates `--root` directory.

    * Checks port availability via `lsof` / `ss` / `netstat` when available.

    * Auto-discovers a likely document root by probing, in order:

        * `ROOT/public/index.php`
        * `ROOT/public/index.html`
        * `ROOT/index.php`
        * `ROOT/index.html`

    * If `--router` is passed, it must exist; otherwise it serves the detected root directly.

### Running scripts with a specific version

* **`run <script.php> [X.Y]`**

    * Validates script path.
    * If `X.Y` is omitted, uses the active default CLI version.
    * If the requested version isn’t installed, it will attempt to install it, then run the script via `/usr/bin/phpX.Y`
      or `/usr/local/bin/phpX.Y`.

### Config generator

* **`generate-config <environment> <X.Y>`**

  Generates two files in the current directory:

    * `fpm.<environment>.conf`
    * `php.<environment>.ini`

  Where:

    * `environment` ∈ `{production, development}`
    * `X.Y` is the PHP version (e.g. `8.2`, `8.3`)

  Uses total system memory to derive:

    * `pm.max_children`, start/min/max spare servers
    * sensible opcache + JIT defaults per environment

### Repositories & self-update

* **`sury`**

    * Detects OS + codename from `/etc/os-release` + `lsb_release`.
    * Ubuntu: adds `ppa:ondrej/php` if missing.
    * Debian: adds Sury repository for the codename (after verifying codename is supported on `packages.sury.org`).
* **`self-update`**

    * Downloads latest `phpx` from GitHub.
    * Compares SHA-256 hash against local copy.
    * Backs up old script and replaces `/usr/local/bin/phpx` atomically.

---

## Command Reference

### `list`

```bash
phpx list
```

Shows installed PHP versions, whether a CLI binary exists for each, FPM state, and the current `php` default.

---

### `info`

```bash
phpx info 8.3
# or simply
phpx info
```

If no version is provided, uses the current default CLI. Prints:

* binary path
* loaded php.ini and additional ini dir
* memory limit / execution time
* opcache & JIT flags
* extension count + common extensions
* FPM service state and pool directory

---

### `doctor`

```bash
phpx doctor 8.2
phpx doctor 8.2 --fix
```

Runs health checks for `8.2`. With `--fix`, it:

* cleans broken `.ini` extension references (same as `phpx clean 8.2`)
* optionally disables extra Apache `mod_php` modules, keeping a single one active
* suggests FPM sizing adjustments based on system RAM

---

### `switch` / `s`

```bash
phpx switch 8.2
phpx s 8.3
phpx switch 8.2 --no-web
```

* Verifies or installs PHP `8.2`.
* Cleans missing extensions for that version.
* Updates `update-alternatives` for `php`, `phar`, `phar.phar`.
* Runs `configure_web_server` to help Apache/Nginx/Lighttpd bind to the chosen version.
  Use `--no-web` to skip web-server configuration (handy for CI / CLI-only boxes).

---

### `ext` / `extensions` / `x`

```bash
phpx ext            # use current default version
phpx ext 8.3        # inspect/install for 8.3
phpx ext 8.2 --install=redis,imagick
```

* Lists installed vs installable `phpX.Y-*` packages.
* Offers interactive selection by number or name.
* With `--install=...`, installs a comma-separated list non-interactively.

---

### `install`

```bash
# Composer
phpx install composer
phpx i composer

# PECL packages
phpx install xdebug,redis apcu
phpx i xdebug, redis apcu
```

* `composer` – installs/updates Composer globally.
* Any other arguments – treated as PECL package list.

---

### `serve`

```bash
phpx serve
phpx serve --host=0.0.0.0 --port=8080
phpx serve --root=/var/www/app --router=router.php -v
```

Starts PHP’s built-in server with guardrails for port/root/router selection and auto index discovery.

---

### `run`

```bash
phpx run bin/script.php
phpx run bin/script.php 8.2
```

Runs a script with the chosen PHP version, installing that version if needed.

---

### `remove`

```bash
# Remove a full PHP version
phpx remove 7.4

# Remove extensions for a specific version (interactive)
phpx remove 8.1 ext

# Remove extensions for detected default version (interactive)
phpx remove ext

# Non-interactive extension removal
phpx remove 8.1 ext --remove=redis,imagick
```

If the first argument looks like `X.Y`:

* `remove <X.Y>` – removes PHP `X.Y` and related packages.
* `remove <X.Y> ext [--remove="ext1,ext2"]` – removes selected extensions only for that version.

If the first argument is not a version:

* `remove ext [--remove="ext1,ext2"]` – removes extensions for the auto-detected default version.

---

### `generate-config`

```bash
phpx generate-config production 8.2
phpx generate-config development 8.3
```

Creates environment-specific FPM + php.ini templates tuned for the host’s RAM:

* `fpm.production.conf` / `php.production.ini`
* `fpm.development.conf` / `php.development.ini`

---

### `sury`

```bash
phpx sury
```

Adds the right PHP repo (Ondřej PPA or Sury) for Debian/Ubuntu systems, validating that the codename is supported.

---

### `clean`

```bash
phpx clean       # uses current PHP version
phpx clean 8.2
```

Removes `.ini` entries for extensions whose `.so` is missing, based on `php -m` error output.

---

### `self-update`

```bash
phpx self-update
```

Fetches the latest `phpx` script from GitHub, compares hashes, backs up the old script and replaces it atomically.

---

## Logging & Environment

By default all commands log to a per-day file:

* As root: `/var/log/phpx/YYYY-MM-DD.log`
* As non-root: `$HOME/.local/phpx_logs/YYYY-MM-DD.log`

Each entry contains timestamp, log level (`INFO` / `WARN` / `ERROR`) and a short description of the action.

Environment helpers:

* `PHPX_LOG_DIR` – override the log directory for both root and non-root runs.
* `PHPX_NO_LOG` – if set (to anything), disables file logging entirely.
* `PHPX_ASSUME_YES` – intended for non-interactive flows where you always want to “answer yes” when possible.

---

`phpx` is part of the **Toolset** collection. See the main repo README for an overview of the other tools.
