# Toolset

Welcome to **Toolset**, a versatile collection of standalone shell-based CLIs to streamline your day-to-day development
and operations workflows on Linux. This repo bundles five utilities:

- **dockex**: Docker container & resource management
- **phpx**: Full-featured PHP version, extension & server management
- **gitx**: Opinionated Git workflow, reporting & cleanup helper
- **chromacat**: Colourful, animated terminal text renderer
- **sqlitex**: Lightweight, production-grade SQLite administration

---

## Table of Contents

- [Installation](#installation)
- [dockex](#dockex)
- [phpx](#phpx)
- [gitx](#gitx)
- [chromacat](#chromacat)
- [sqlitex](#sqlitex)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

Install any of the tools with a single curl + chmod. For example:

```bash
# Install dockex
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Docker/dockex" \
  -o /usr/local/bin/dockex && sudo chmod +x /usr/local/bin/dockex

# Install phpx
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/PHP/phpx" \
  -o /usr/local/bin/phpx && sudo chmod +x /usr/local/bin/phpx

# Install gitx
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Git/gitx" \
  -o /usr/local/bin/gitx && sudo chmod +x /usr/local/bin/gitx

# Install chromacat
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat" \
  -o /usr/local/bin/chromacat && sudo chmod +x /usr/local/bin/chromacat

# Install sqlitex
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Sqlite/sqlitex" \
  -o /usr/local/bin/sqlitex && sudo chmod +x /usr/local/bin/sqlitex
```

---

## dockex

`dockex` wraps Docker + jq + benchmarking + backups into one tool.

### Commands

| Command                                                            | Description                                                    |
|--------------------------------------------------------------------|----------------------------------------------------------------|
| `list`                                                             | Show Docker images, containers, networks, and volumes          |
| `info` / `stats` / `inspect` <br>`<container>`                     | Detailed container info (CPU, memory, I/O, env, ports, health) |
| `logs` <br>`<container> [lines]`                                   | Show last N lines of logs (default 10)                         |
| `stream_logs` <br>`<container>`                                    | Stream logs in real time                                       |
| `start` <br>`<container>`                                          | Start a stopped container                                      |
| `stop` <br>`<container>`                                           | Stop a running container                                       |
| `restart` <br>`<container>`                                        | Restart a container                                            |
| `benchmark` <br>`<container> [instances] [requests] [concurrency]` | ApacheBench stress test                                        |
| `update_resources` <br>`<container>`                               | Dynamically adjust CPU shares & memory                         |
| `backup` <br>`<container>`                                         | Backup container volume data                                   |
| `restore` <br>`<container> <backup.zip>`                           | Restore container data from backup                             |
| `create` <br>`<image> [name]`                                      | Interactive `docker run` scaffolding                           |
| `cleanup` <br>`[unused\|aggressive\|all]`                          | Prune and cleanup Docker resources                             |

#### Examples

```bash
# Show all Docker resources
dockex list

# View detailed stats for my_container
dockex info my_container

# Tail last 10 lines of logs for my_container
dockex logs my_container 10

# Stream logs live for my_container
dockex stream_logs my_container

# Start a stopped container
dockex start my_container

# Stop a running container
dockex stop my_container

# Restart a container
dockex restart my_container

# Run benchmark: 3 instances, 100 requests each, concurrency of 10
dockex benchmark my_container 3 100 10

# Update CPU and memory limits
dockex update_resources my_container

# Backup container's volume data
dockex backup my_container

# Restore container data from zip
dockex restore my_container backup.zip

# Create a new nginx container named mynginx
dockex create nginx mynginx

# Cleanup unused Docker resources
dockex cleanup unused
```

---

## phpx

`phpx` automates installing, switching, configuring PHP, Composer, PECL, built-in server, extensions, config generation,
cleanup, and self-update.

### Commands

| Command                                                               | Description                                                                                     |
|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `switch` <br>`<X.Y>`                                                  | Switch PHP CLI to version X.Y (installs if needed, updates alternatives, configures web server) |
| `ext` <br>`[X.Y]`                                                     | List & interactively install/remove extensions for PHP X.Y (defaults to active version)         |
| `install composer`                                                    | Install Composer globally and self-update                                                       |
| `install` <br>`<pecl1,pecl2,...>`                                     | Install one or more PECL packages                                                               |
| `serve` <br>`[--host H] [--port P] [--root DIR] [--router FILE] [-v]` | Start built-in PHP web server                                                                   |
| `run` <br>`<script.php> [X.Y]`                                        | Run a PHP script with specified or active PHP version                                           |
| `remove` <br>`<X.Y>`                                                  | Remove PHP version X.Y and related packages                                                     |
| `remove` <br>`<X.Y> ext`                                              | Interactively remove extensions for PHP X.Y                                                     |
| `sury`                                                                | Add Sury/Ondřej PHP repository for Debian/Ubuntu                                                |
| `clean` <br>`[X.Y]`                                                   | Clean up broken extension references for PHP X.Y or active version                              |
| `generate-config` <br>`<environment> <X.Y>`                           | Generate tuned `php.ini` + FPM pool config for `production` or `development`                    |
| `self-update`                                                         | Update the `phpx` script itself from GitHub                                                     |

#### Examples

```bash
# Switch the CLI to PHP 8.2
phpx switch 8.2

# List extensions for PHP 8.2
phpx ext 8.2

# Install Composer globally
phpx install composer

# Install xdebug and redis via PECL
phpx install xdebug,redis

# Serve current directory on localhost:8000
phpx serve --host 127.0.0.1 --port 8000

# Run a script with PHP 7.4
phpx run script.php 7.4

# Remove PHP 7.4 and its packages
phpx remove 7.4

# Interactively remove extensions from PHP 7.4
phpx remove 7.4 ext

# Add the Sury.org repo on Debian/Ubuntu
phpx sury

# Clean broken extensions for current version
phpx clean

# Generate production config for PHP 8.2
phpx generate-config production 8.2

# Update the phpx script to latest
phpx self-update
```

---

## gitx

`gitx` provides an all-in-one Git helper: branch workflows, interactive commits, stash, reporting, cleanup, etc.

### Commands

| Command                                  | Description                                                              |
|------------------------------------------|--------------------------------------------------------------------------|
| `status`                                 | Show repo status, tracking & remote info                                 |
| `fetch`                                  | Fetch remotes & prune stale refs                                         |
| `sync`                                   | Merge main → alpha/develop (plus optional extras)                        |
| `create` <br>`<type> <name>`             | Create branch (`feature\|bugfix\|hotfix\|release\|docs\|ci\|experiment`) |
| `merge` <br>`<src> <dst>`                | Merge source branch into target                                          |
| `reset-branch`                           | Reset current branch to remote (soft/hard/dry-run)                       |
| `prune`                                  | Prune remote-tracking branches & delete local stale ones                 |
| `cleanup`                                | Delete merged branches                                                   |
| `compare` <br>`<branch1> <branch2>`      | Show commit & file diff between two branches                             |
| `commit`                                 | Interactive commit helper                                                |
| `amend`                                  | Amend last commit message                                                |
| `cherry-pick` <br>`<hash>`               | Cherry-pick specific commits                                             |
| `revert`                                 | Revert commits (interactive)                                             |
| `diff`                                   | Show or save staged diff                                                 |
| `log-file` <br>`<file>`                  | Show commit history & diffs for a file                                   |
| `large-files`                            | List largest files in repo                                               |
| `stash`                                  | Manage stash (save, list, apply, pop, drop, rename, clear)               |
| `report` <br>`<start> [end] [outfile]`   | Generate PR & merge commit report                                        |
| `summary` <br>`[range] [include-all]`    | Summarize commits, changes, surviving code %                             |
| `count-changes`                          | Count insertions/deletions between two commits                           |
| `list-changes` <br>`<branch1> <branch2>` | List files changed between branches                                      |
| `changelog` <br>`<start> <end>`          | Generate changelog between refs                                          |
| `commit-report` <br>`<range/dates>`      | Detailed commit report by author/type                                    |
| `add-remote` <br>`<name> <url>`          | Add a new Git remote                                                     |
| `push-remote` <br>`<remote> <branch>`    | Push to specific remote branch                                           |
| `pull-remote` <br>`<remote> <branch>`    | Pull from specific remote branch                                         |
| `config`                                 | Interactive Git config editor                                            |
| `set-lf`                                 | Enforce LF line endings                                                  |
| `self-update`                            | Update the `gitx` script itself from GitHub                              |

#### Examples

```bash
# Show status and branch info
gitx status

# Fetch and prune
gitx fetch

# Sync alpha & develop from main
gitx sync

# Create a new feature branch
gitx create feature my-feature

# Merge feature into main
gitx merge my-feature main

# Reset current branch to remote state
gitx reset-branch

# Prune stale remote branches
gitx prune

# Delete merged local branches
gitx cleanup

# Compare main against develop
gitx compare main develop

# Interactive commit helper
gitx commit

# Amend last commit
gitx amend

# Cherry-pick a specific commit
gitx cherry-pick abc1234

# Revert commits interactively
gitx revert

# Show staged diff or save to file
gitx diff

# View history and diffs for README.md
gitx log-file README.md

# List top 10 largest files
gitx large-files

# Manage stash operations
gitx stash

# Generate PR/merge report from v1.0.0 to v2.0.0
gitx report v1.0.0 v2.0.0 report.txt

# Summarize last 50 commits including surviving code %
gitx summary HEAD~50 include-all

# Count changes between two commits
gitx count-changes

# List changed files between branches
gitx list-changes main develop

# Create a changelog between tags
gitx changelog v1.0.0 v1.1.0

# Detailed commit report
gitx commit-report v1.0.0 v1.1.0

# Add a new remote called origin
gitx add-remote origin https://github.com/user/repo.git

# Push main to origin
gitx push-remote origin main

# Pull develop from origin
gitx pull-remote origin develop

# Edit Git config
gitx config

# Set Git to LF only
gitx set-lf

# Update gitx script
gitx self-update
```

---

## chromacat

`chromacat` paints colourful, animated text & ASCII art in your terminal.

### Options

| Option                        | Purpose                                            |
|-------------------------------|----------------------------------------------------|
| `-p, --spread <f>`            | Rainbow spread factor                              |
| `-F, --freq <f>`              | Rainbow frequency                                  |
| `-S, --seed <n>`              | PRNG seed (0=random)                               |
| `-a, --animate`               | Classic scrolling animation                        |
| `-aa, --line`                 | Line-by-line reveal animation                      |
| `-d, --duration <s>`          | Animation duration (seconds)                       |
| `-s, --speed <fps>`           | Frames-per-second (or lines/sec)                   |
| `-i, --invert`                | Invert foreground/background                       |
| `-t, --truecolor`             | Force 24-bit colour                                |
| `-f, --force`                 | Force colour even if not a TTY                     |
| `-b, --box`                   | Draw ASCII box                                     |
| `-B, --box-style <name>`      | Box style (default, parchment, simple, …)          |
| `-O, --orientation <h\|v\|d>` | Gradient orientation: horizontal/vertical/diagonal |
| `-P, --palette <file>`        | Custom HEX palette file                            |
| `-T, --theme <name>`          | Predefined themes (fire, ice, sunset, …)           |
| `-I, --image <file>`          | ASCII-art import via chafa/jp2a/img2txt            |
| `--blink`                     | Blinking text                                      |
| `--image-opacity <0–100>`     | ASCII-image brightness                             |
| `-v, --version`               | Print version                                      |
| `-h, --help`                  | Show help                                          |

#### Examples

```bash
# Rainbow scroll "hello" over 2s
echo "hello" | chromacat -a -d 2

# Boxed diagonal reveal with parchment style
figlet "Docker" | chromacat -b -B parchment -aa -O d

# Render screenshot.png as ANSI art at 80% opacity
chromacat -T ocean --image screenshot.png --image-opacity 80
```

---

## sqlitex

A non-interactive, parameter-based SQLite CLI.

### Commands

| Command                                                               | Description                                   |
|-----------------------------------------------------------------------|-----------------------------------------------|
| `create-db`                                                           | Create a new SQLite database file             |
| `create-table` <br>`--table <name> --columns "<col_defs>"`            | Create table if not exists                    |
| `insert` <br>`--table <name> --values "<vals>"`                       | Insert a single record                        |
| `insert-batch` <br>`--file <sql_file>`                                | Execute a SQL file of inserts                 |
| `select` <br>`--table <name> [--where "<cond>"] [--export csv\|json]` | Query rows (pretty/CSV/JSON)                  |
| `update` <br>`--table <name> --set "<set>" --where "<cond>"`          | Update rows (with safe backup & transaction)  |
| `delete` <br>`--table <name> --where "<cond>"`                        | Delete rows (with safe backup & transaction)  |
| `schema` <br>`--table <name>`                                         | Show table schema                             |
| `migrate` <br>`[--rollback]`                                          | Apply pending migrations or rollback last one |
| `seed`                                                                | Import seed files (SQL, CSV, JSON)            |
| `reset`                                                               | Backup → drop & recreate DB → migrate → seed  |

#### Examples

```bash
# Create database file my.db
sqlitex --db my.db create-db

# Create users table with id & name columns
sqlitex --db my.db create-table --table users --columns "id INTEGER PRIMARY KEY, name TEXT"

# Insert a single record into users
sqlitex --db my.db insert --table users --values "NULL,'Alice'"

# Batch-insert from SQL file
sqlitex --db my.db insert-batch --file seeds/users.sql

# Select rows where id > 5, pretty-print in table form
sqlitex --db my.db select --table users --where "id>5"

# Export query to CSV
sqlitex --db my.db select --table users --where "id>5" --export csv

# Update name to Bob for id=1
sqlitex --db my.db update --table users --set "name='Bob'" --where "id=1"

# Delete record with id=2
sqlitex --db my.db delete --table users --where "id=2"

# Show schema of users table
sqlitex --db my.db schema --table users

# Run all pending migrations
sqlitex --db my.db migrate

# Roll back last migration
sqlitex --db my.db migrate --rollback

# Seed the database with SQL, CSV, JSON files
sqlitex --db my.db seed

# Fully reset DB: backup, recreate, migrate, seed
sqlitex --db my.db reset
```

---

## Contributing

We welcome improvements, bug fixes, new features, or better documentation!  
Please open an issue or pull request against this repo.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
