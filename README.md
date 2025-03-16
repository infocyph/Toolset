# Toolset

Welcome to **Toolset**, a versatile set of scripts designed to streamline your Linux-based development environment management tasks. This repository provides three key utilities: `dockex` for Docker container management, `phpx` for PHP version and extension management, and `gitx` for Git workflow and repository management.

## Table of Contents
- [Installation](#installation)
- [Scripts Overview](#scripts-overview)
  - [dockex](#dockex)
  - [phpx](#phpx)
  - [gitx](#gitx)
- [Usage](#usage)
  - [dockex Commands](#dockex-commands)
  - [phpx Commands](#phpx-commands)
  - [gitx Commands](#gitx-commands)
- [Contributing](#contributing)
- [License](#license)

## Installation

phpx:
```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/PHP/phpx" -o /usr/local/bin/phpx && sudo chmod +x /usr/local/bin/phpx
```

dockex:
```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Docker/dockex" -o /usr/local/bin/dockex && sudo chmod +x /usr/local/bin/dockex
```

gitx:
```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Git/gitx" -o /usr/local/bin/gitx && sudo chmod +x /usr/local/bin/gitx
```

## Scripts Overview

### dockex

`dockex` is a Docker management utility that simplifies common Docker operations. It allows you to manage containers, monitor resource usage, perform benchmarks, and backup/restore data.

#### Key Features:
- Manage Docker containers (start, stop, restart, etc.)
- Inspect detailed container stats (CPU, memory, network, and more)
- Benchmark containers using Apache Benchmark (ab)
- Backup and restore container data
- Dynamically update container resources (CPU, memory)
- Cleanup images, containers, networks and volumes

### phpx

`phpx` is a lightweight PHP management script allowing you to switch between PHP versions, manage extensions, configure PHP-FPM or mod_php for different web servers, and even run a quick built-in server. It also lets you install Composer, PECL packages, remove unwanted versions/extensions, and more.

#### Key Features:
- **Switch** between multiple PHP versions (with automatic installation if missing).
- **Install & Manage** PHP extensions (interactive selection or by name).
- **Clean** orphaned/missing extension references to prevent startup errors.
- **Serve** a PHP application quickly using the built-in PHP web server.
- **Install Composer** or **PECL** packages with minimal hassle.
- **Remove** entire PHP versions (including dependencies) or just selected extensions.
- **Self-Update** the phpx script to get the latest features and fixes.

### gitx

`gitx` is a Git workflow and repository management script designed to simplify Git operations for developers. It provides commands for **branch management, commit tracking, stash operations, reporting, cleanup**, and more.

#### **Key Features:**
- **Branch Management**: Create, sync, merge, reset, and delete branches.
- **Commit Operations**: Interactive commits, amending, cherry-picking, and reverting commits.
- **Stash Management**: Save, list, apply, drop, rename, and clear stashes.
- **Comparison & Reporting**: Compare branches, generate PR reports, and track changes.
- **Cleanup & Optimization**: Prune remote branches, clean untracked files, and manage large files.
- **Configuration & Tagging**: Edit Git settings, manage tags, and summarize repository details.

## Usage

### dockex Commands

```bash
dockex <command> [container_name] [options]
```

#### Available Commands:
- **info** | **stats** | **inspect**: Show detailed information about a container's resource usage, IP, health status, environment variables, etc.
- **logs**: Display container logs (optional: specify number of lines).
- **start**: Start a stopped container.
- **stop**: Stop a running container.
- **restart**: Restart a container.
- **benchmark**: Perform a stress test using Apache Benchmark.
- **update_resources**: Dynamically update CPU and memory limits for a container.
- **stream_logs**: Stream container logs in real-time.
- **backup**: Backup container volume data.
- **restore**: Restore container data from a backup.
- **list**: List all Docker images, containers, networks, and volumes.
- **create**: Interactively create a new Docker container.
- **cleanup**: Remove all Docker images, containers, networks and volumes.

#### Examples:
```bash
dockex my_container info         # Show detailed container info and resource usage
dockex my_container logs 50      # Show the last 50 lines of logs
dockex my_container start        # Start a stopped container
dockex my_container benchmark 5  # Run a multi-node benchmark with 5 instances
dockex my_container backup       # Backup data from a selected container volume
dockex create nginx my_container # Create a new container using the nginx image
```

### phpx Commands

```bash
phpx {switch|ext|install|serve|run|remove|sury|clean|self-update} <arguments>
```

#### Available Commands:
- **`switch|s <php_version>`**  
  Switch to the specified PHP version (e.g., 8.2), installing it if not found. Also sets up PHP-FPM or mod_php for your current web server (Apache, Nginx, Lighttpd).

- **`ext|extensions|x [php_version]`**  
  Lists currently installed extensions for the given PHP version and allows interactive installation of additional extensions. If no version is provided, it defaults to the active PHP version.

- **`install|i composer`**  
  Installs Composer globally if not already installed, then updates it to the latest version.

- **`install|i <pecl_package>(,...)`**  
  Installs one or more PECL packages (e.g., `xdebug,redis`). Automatically sets up PECL if it’s missing.

- **`serve [--host <host>] [--port <port>] [--root <dir>] [--router <file>] [-v]`**  
  Spins up the built-in PHP development server from the specified (or current) directory.
  - `--host`: Defaults to `127.0.0.1`
  - `--port`: Defaults to `8000`
  - `--root`: Defaults to your current directory
  - `--router`: If provided, uses a custom router file
  - `-v|--verbose`: Increases output for debugging

- **`run <script_path> [php_version]`**  
  Runs a PHP script using the specified or currently active PHP version. If the specified version is missing, it attempts to install it first.

- **`remove <php_version>`**  
  Removes the specified PHP version and all associated packages/services (e.g., PHP-FPM).
  - **`remove <php_version> ext|extension`**: Interactively remove selected extensions for that version.

- **`sury`**  
  Adds the Sury (or Ondrej) repository for Debian/Ubuntu systems if needed, providing the latest PHP packages.

- **`clean [php_version]`**  
  Checks for and removes references to missing/broken PHP extensions (e.g., stale `.ini` files) in the specified or current PHP version. Helps eliminate “Unable to load dynamic library” errors.

- **`self-update`**  
  Updates the **phpx** script itself by fetching the latest version from GitHub. Backs up the old file for safety.

#### Examples:
```bash
# Switch to PHP 8.2 (installing if needed) and configure Apache or Nginx:
phpx switch 8.2

# List installed extensions for the current PHP version and install new ones interactively:
phpx ext

# Install Composer globally if missing:
phpx install composer

# Install multiple PECL packages (e.g., xdebug and redis):
phpx install xdebug,redis

# Serve the current directory on 192.168.0.1:8080, optionally specifying a custom router:
phpx serve --host=192.168.0.1 --port=8080 --root=/var/www --router=router.php

# Run a specific script with PHP 8.2:
phpx run /path/to/my_script.php 8.2

# Clean orphaned extensions (.ini references to missing .so files) for the current PHP version:
phpx clean

# Remove an entire PHP version (and optional FPM service):
phpx remove 8.1

# Remove extensions for PHP 8.2 interactively:
phpx remove 8.2 ext

# Update phpx itself to the latest version:
phpx self-update
```

### gitx Commands

```bash
gitx <command> [options]
```

#### **🔄 Repository & Branch Management**
- **`status`** → Show repository status, branch tracking info, and remote details.
- **`fetch`** → Fetch remote branches and prune stale references.
- **`sync`** → Sync `alpha` and `develop` with `main`/`master`.
- **`create <branch_type> <name>`** → Create a new branch from `main`/`master`.
  - `<branch_type>`: feature, bugfix, hotfix, release, docs, ci, experiment.
  - `<name>`: A short descriptive name for the branch.
- **`merge <source_branch> <target_branch>`** → Merge one branch into another.
- **`reset-branch`** → Reset the current branch to match the remote.
  - Interactive mode with **soft/hard reset** options.
- **`prune`** → Prune remote branches and delete local tracking branches.
- **`cleanup`** → Delete branches that have been merged.
- **`compare <branch1> <branch2>`** → Compare two branches.

#### **📦 Commit & Change Management**
- **`commit`** → Interactive commit helper (select files, enter a message).
- **`amend`** → Amend the last commit message.
- **`cherry-pick <commit_hash>`** → Cherry-pick a specific commit.
- **`revert`** → Revert specific commits with options.
- **`unstage`** → Unstage all files (requires confirmation).
- **`stage-deleted`** → Stage all deleted files.
- **`stage-deleted-dir <directory>`** → Stage deleted files in a specific directory.
- **`diff [output_file]`** → View or save staged changes.
  - `[output_file]` (optional): Save diff to a file (default: `diffs.txt`).

#### **📊 Tracking & Reporting**
- **`log-file <file_path>`** → View commit history and diffs for a specific file.
- **`summary [commit_range] [include-all]`** → Summarize commits, insertions, deletions, surviving code.
  - `[commit_range]` (optional): e.g., `HEAD~50`.
  - `[include-all]` (optional): Include all text-based files.
- **`report <start_commit> [end_commit] [output_file]`** → Generate a report of PRs, non-PR merges, and standalone commits.
  - `<start_commit>`: Starting commit hash or tag.
  - `[end_commit]` (optional, default: HEAD): Ending commit hash or tag.
  - `[output_file]` (optional): Output file for the report (default: `pr_report.txt`).
- **`count-changes`** → Count insertions and deletions between two commits.
- **`list-changes <branch1> <branch2>`** → List files changed between two branches.
- **`changelog <start_commit> <end_commit>`** → Generate a changelog between commits or tags.

#### **🔖 Tags & Releases**
- **`tag <version>`** → Tag the current branch with a version.
  - `<version>`: Must follow semantic versioning (e.g., `v1.0.0`).
- **`latest-tag`** → Get the latest tag in the repository.
- **`initial-commit`** → Get the initial commit hash.

#### **🗄️ Stashing & Cleanup**
- **`stash`** → Manage stash operations (save, list, apply, drop, rename, clear).
- **`clean`** → Clean untracked files and directories.
  - Interactive mode with preview option.
- **`large-files`** → Show the largest files in the repository.

#### **⚙️ Configuration & Utilities**
- **`add-remote <name> <url>`** → Add a new remote repository.
  - `<name>`: Remote name (e.g., `origin`).
  - `<url>`: Remote URL.
- **`push-remote <remote> <branch>`** → Push to a specific remote branch.
- **`pull-remote <remote> <branch>`** → Pull from a specific remote branch.
- **`config`** → Edit Git configuration interactively.
- **`set-lf`** → Set Git to use LF line endings.
- **`self-update`** → Update `gitx` to the latest version.

#### Examples:
```bash
# Track staged changes and save to a file
gitx diff changes.txt

# Generate a commit report for a specific range
gitx report abc123 HEAD output.txt

# Sync develop and alpha branches with main/master
gitx sync

# Merge a feature branch into main
gitx merge feature/login main

# Compare two branches to find differences
gitx compare develop main

# Reset the current branch to match the remote state
gitx reset-branch

# Clean up merged branches
gitx cleanup

# Summarize the last 50 commits with surviving code percentage
gitx summary HEAD~50 include-all
```

## Contributing

We welcome contributions! Whether you're fixing bugs, adding new features, or improving documentation, feel free to submit issues or pull requests to enhance **Toolset**.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.