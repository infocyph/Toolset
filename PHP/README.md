# phpx

`phpx` is a **PHP toolkit & manager** for Debian/Ubuntu-like systems.

It wraps the usual “install / switch / inspect / tune” PHP tasks into a single script, without hiding what’s going on underneath.

---

## Features

* **Version lifecycle**

  * Install / list / switch PHP versions (CLI + FPM) via `apt` + Sury/Ondřej repos
  * Safely remove PHP versions and related packages
  * Discover **available** PHP versions from APT (`known`) and compare against local installs (`variants`)
* **Extensions & cleanup**

  * Discover, install and remove `phpX.Y-*` extensions
  * Toggle extensions during switch: `phpx switch 8.4 +mysql -curl`
  * Clean broken `.so` references from `.ini` files (`clean`)
* **Health & diagnostics**

  * Run sanity checks (`doctor`) for a PHP version
  * Get a summarized config view (`info`) with OPcache/JIT/FPM hints
  * Lint a repo quickly and show only failures (`syntax`)
* **Composer & PECL**

  * Install/update Composer globally
  * Install multiple PECL packages in one go
* **Runtime helpers**

  * Start PHP’s built-in web server safely (`serve`)
  * Run scripts under a specific PHP version (`run`)
* **Configs & repos**

  * Generate tuned `php.ini` + FPM pool configs (`generate-config`)
  * Add Sury/Ondřej PHP repositories (`sury`)
* **Service helpers**

  * Control PHP-FPM (`fpm`) and Apache wiring (`apache`)
* **Script lifecycle**

  * Self-update from GitHub (`self-update`)
  * Per-day logging with env-based overrides

High-impact commands (`switch`, `install`, `remove`, `sury`, `self-update`) run basic system checks (disk space, curl/wget, network) before touching apt or remote endpoints.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/PHP/phpx" \
  -o /usr/local/bin/phpx && sudo chmod +x /usr/local/bin/phpx
```

---

## Requirements

* Debian/Ubuntu or derivative (uses `apt`, `dpkg`, `lsb_release`, `systemctl`, `update-alternatives`, etc.)
* For extension toggles:

  * `phpenmod` / `phpdismod` (from Debian PHP packaging)
* For logs:

  * Writable log directory (`/var/log/phpx` as root, `~/.local/phpx_logs` as user)

---

## Usage at a Glance

```bash
phpx {list|info|doctor|switch|ext|install|serve|run|remove|generate-config|sury|clean|self-update|known|variants|syntax|fpm|apache} <args>
```

### Command aliases

* `switch` → `s`
* `ext` → `extensions`, `x`
* `install` → `i`

### Commands that usually require `sudo`

Anything that installs/removes packages or touches system config:

* `switch`, `ext`, `install`, `remove`, `generate-config`, `sury`, `clean`, `self-update`
* plus anything that ends up calling `apt`/`dpkg` or writing into `/etc`, `/usr/local/bin`, etc.

---

## Commands Overview

| Command                                          | Aliases         | Summary                                                              |                                           |
| ------------------------------------------------ | --------------- | -------------------------------------------------------------------- | ----------------------------------------- |
| `list`                                           |                 | List installed PHP versions (CLI + FPM state, current default)       |                                           |
| `info [X.Y]`                                     |                 | Summarized phpinfo-style view for a version                          |                                           |
| `doctor [X.Y] [--fix]`                           |                 | Sanity checks + optional auto-fix                                    |                                           |
| `switch <X.Y> [--no-web] [+ext] [-ext] [ext...]` | `s`             | Switch default CLI to `X.Y` (+ optional extension toggles)           |                                           |
| `ext [X.Y] [--install=...] [-y                   | --yes]`         | `extensions`, `x`                                                    | Discover/install extensions for a version |
| `install composer`                               | `i composer`    | Install/update Composer globally                                     |                                           |
| `install <pecl...>`                              | `i <pecl...>`   | Install PECL packages                                                |                                           |
| `serve [options]`                                |                 | Start PHP built-in web server safely                                 |                                           |
| `run <script.php> [X.Y]`                         |                 | Run script with a specific PHP version                               |                                           |
| `remove <X.Y>`                                   |                 | Remove PHP `X.Y` and related packages                                |                                           |
| `remove <X.Y> ext [--remove=...]`                |                 | Remove extensions for PHP `X.Y`                                      |                                           |
| `remove ext [--remove=...]`                      |                 | Remove extensions for detected default version                       |                                           |
| `generate-config <env> <X.Y>`                    |                 | Generate `php.ini` + FPM pool configs (prod/dev)                     |                                           |
| `sury`                                           |                 | Add Sury/Ondřej PHP repo for Debian/Ubuntu                           |                                           |
| `clean [X.Y]`                                    |                 | Clean broken extension `.ini` entries                                |                                           |
| `known [--more]`                                 |                 | Show PHP X.Y versions available from current APT sources             |                                           |
| `variants [--more]`                              |                 | Show local installed versions + APT-available versions not installed |                                           |
| `syntax [options]`                               | `lint`, `check` | Lint repo PHP files (print only failures)                            |                                           |
| `fpm <subcommand> [X.Y]`                         |                 | Manage php-fpm services for a version                                |                                           |
| `apache <subcommand> [X.Y]`                      |                 | Apache helpers (status/reload/restart + FPM/mod_php wiring)          |                                           |
| `self-update`                                    |                 | Update `phpx` script from GitHub                                     |                                           |

---

## Command Details

### 1) Version Discovery & Lifecycle

#### `known`

Shows PHP versions available from your current APT sources (useful after `phpx sury`):

```bash
phpx known
phpx known --more
```

* `--more` prints APT “Candidate” version (best-effort).

#### `variants`

Shows:

1. **local installed** PHP versions
2. **APT-available** PHP versions that are **not installed locally**

```bash
phpx variants
phpx variants --more
```

* `--more` prints APT “Candidate” version for each remote entry (best-effort).

---

#### `list`

```bash
phpx list
```

Lists installed PHP versions (`phpX.Y-*` packages), and shows:

* CLI binary per version (if any)
* FPM state: active / installed / not present
* current `php` default and its version

---

#### `switch` / `s`

```bash
phpx switch 8.2
phpx s 8.3
phpx switch 8.2 --no-web

# extension toggles during switch
phpx switch 8.4 +mysql -curl
phpx switch 8.3 mysql
```

What it does:

* Ensures `phpX.Y`, `phpX.Y-cli` (and FPM as needed) are installed.
* Cleans broken `.ini` extension references for that version.
* Updates `update-alternatives` for:

  * `php`, `phar`, `phar.phar`
* Web server wizard (unless `--no-web`):

  * detects installed web server(s) and wires PHP-FPM or mod_php depending on choices.
* **Extension toggles**:

  * `+ext` or `ext` ⇒ install `phpX.Y-ext` if missing, then `phpenmod -v X.Y ext`
  * `-ext` ⇒ `phpdismod -v X.Y ext` (does not purge packages)
  * reloads `phpX.Y-fpm` if active

---

#### `remove`

```bash
# remove a PHP version
phpx remove 7.4

# remove extensions for a specific version
phpx remove 8.1 ext --remove=redis,imagick

# remove extensions for detected default version
phpx remove ext --remove=redis,imagick
```

Behavior:

* `remove <X.Y>`:

  * stops/disables `phpX.Y-fpm` if present
  * purges `phpX.Y-*` packages via APT
  * runs `apt autoremove`
* `remove <X.Y> ext ...`:

  * removes only selected `phpX.Y-<ext>` packages
* `remove ext ...`:

  * operates on detected default CLI version

---

### 2) Health & Diagnostics

#### `info`

```bash
phpx info 8.3
phpx info      # uses current default CLI version
```

Shows:

* binary path, loaded `php.ini`, scan dir, `extension_dir`
* key runtime settings (memory_limit, upload limits, etc.)
* FPM overview (`phpX.Y-fpm` state + key pool settings)
* extension summary (`php -m`, apt-level `phpX.Y-*`, xdebug presence)
* OPcache + JIT snapshot + best-effort hints

---

#### `doctor`

```bash
phpx doctor
phpx doctor 8.2
phpx doctor 8.2 --fix
```

Checks:

* CLI vs FPM mismatch, service states
* broken extensions (“Unable to load dynamic library …”)
* Apache mod_php conflicts
* FPM sizing hints (RAM-based)
* runtime sanity (upload/post sizes, display/log errors, etc.)
* OPcache & JIT hints
* xdebug warnings

With `--fix`:

* runs `clean` behavior for broken extension `.ini` entries
* best-effort Apache mod_php conflict cleanup

---

#### `syntax` (PHP lint)

Lints all `*.php` files under the current directory and prints **only failures**.

```bash
phpx syntax
phpx syntax --exclude storage --exclude bootstrap/cache
phpx syntax --jobs 8
phpx syntax --php /usr/bin/php8.4
```

Defaults:

* excludes: `vendor`, `node_modules`
* jobs: `nproc` (or `sysctl -n hw.ncpu`)
* hides “No syntax errors detected” lines

---

### 3) Extensions & Cleanup

#### `ext` / `extensions` / `x`

```bash
phpx ext
phpx ext 8.3
phpx ext 8.2 --install=redis,imagick
PHPX_ASSUME_YES=1 phpx ext 8.2 --install=redis
```

* If no version is given: uses current default CLI version.
* Interactive mode: choose from installable extensions via APT metadata.
* Non-interactive mode: `--install=ext1,ext2`
* Installs packages `phpX.Y-ext` and enables them (reloads FPM if running).

---

#### `clean`

```bash
phpx clean
phpx clean 8.2
```

* Detects missing `.so` errors
* removes broken `.ini` entries under `/etc/php/X.Y/...`
* safe to run repeatedly

---

### 4) Composer & PECL

#### `install composer`

```bash
phpx install composer
phpx i composer
```

* ensures `curl` is available
* installs Composer into `/usr/local/bin/composer`
* runs `composer self-update`

#### `install <pecl...>`

```bash
phpx install xdebug,redis apcu
phpx i xdebug redis
```

* installs `php-pear` + `php-dev` if needed
* installs PECL packages (skips ones already present per `pecl list`)

---

### 5) Runtime Helpers

#### `serve`

```bash
phpx serve
phpx serve --host=0.0.0.0 --port=8080
phpx serve --root=/var/www/app --router=router.php -v
```

Starts `php -S host:port -t <root> [router]` with basic safety checks.

#### `run`

```bash
phpx run bin/script.php
phpx run bin/script.php 8.2
```

Runs a script with the chosen PHP version (installs version if missing).

---

### 6) Config Generator

#### `generate-config`

```bash
phpx generate-config production 8.2
phpx generate-config development 8.3
```

Outputs:

* `fpm.<env>.conf`
* `php.<env>.ini`

Uses RAM-based FPM sizing and environment-tuned OPcache/JIT defaults.

---

### 7) Services

#### `fpm`

```bash
phpx fpm status 8.2
phpx fpm restart 8.2
phpx fpm test 8.2
phpx fpm config 8.2
```

#### `apache`

```bash
phpx apache status
phpx apache reload
phpx apache fpm 8.2
phpx apache modphp 8.2
```

---

### 8) Repositories & Self-Update

#### `sury`

```bash
phpx sury
```

Adds Sury/Ondřej repo (Debian/Ubuntu) and runs `apt update`.

#### `self-update`

```bash
phpx self-update
```

Updates `/usr/local/bin/phpx` from the official source.

---

## Logging & Environment

Default logs:

* as root: `/var/log/phpx/YYYY-MM-DD.log`
* as user: `~/.local/phpx_logs/YYYY-MM-DD.log`

Environment variables:

* `PHPX_LOG_DIR` override log directory
* `PHPX_NO_LOG` disable file logging
* `PHPX_ASSUME_YES` treat flows as non-interactive “yes” where supported

---

## Quick Examples

```bash
phpx list
phpx known --more
phpx variants --more

phpx info 8.3
phpx doctor 8.2 --fix

phpx switch 8.4 +mysql -curl
phpx switch 8.2 --no-web

phpx ext 8.2 --install=redis,imagick
phpx syntax --exclude storage --exclude bootstrap/cache

phpx sury
phpx self-update
```

---

`phpx` is part of the **Toolset** collection. See the main repo README for the rest of the tools.
