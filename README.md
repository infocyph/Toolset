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

`phpx` is a PHP management script that allows you to switch between PHP versions, manage extensions, and handle PHP-FPM and CLI configurations. It also offers built-in web server capabilities.

#### Key Features:
- Switch between multiple PHP versions
- Install and manage PHP extensions
- Serve a PHP application with a built-in PHP web server
- Install Composer and PECL packages easily
- Remove PHP versions and extensions when no longer needed

### gitx

`gitx` is a Git workflow and repository management script designed to simplify Git operations for developers. It includes features for branch management, commit tracking, reporting, and more.

#### Key Features:
- Manage Git branches (create, merge, sync with `main`/`master`)
- Generate reports for pull requests, non-PR merges, and standalone commits
- Track and save staged changes to a file
- Perform stash operations (save, list, apply, drop)
- Compare two branches to identify differences
- Edit Git configuration interactively
- Cleanup merged branches
- Summarize repository details
- Tag releases

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
phpx {switch|ext|install|serve|run|remove|sury} <php_version|composer|pecl_package|script_path>
```

#### Available Commands:
- **switch** | **s** `<php_version>`: Switch to a specified PHP version, installing it if not found. Also installs PHP-FPM if needed for Nginx or Lighttpd.
- **ext** | **extensions** | **x** `[php_version]`: Show installed PHP extensions for a given version and allow new ones to be installed. Defaults to the current PHP version if none is provided.
- **install** | **i** **composer**: Install Composer globally if not already installed.
- **install** | **i** `<pecl_package>`: Install a PECL package (or multiple packages separated by commas).
- **serve**: Start a PHP built-in web server from the current or specified root directory.
- **run** `<script_path>` `[php_version]`: Run a PHP script using the specified or currently active PHP version.
- **remove** `<php_version>`: Remove the specified PHP version.
- **remove** `[php_version] [extension | ext]`: Remove a specified PHP extension for a given version (Interactive).
- **remove** : Remove a specified PHP extension for a current version (Interactive).
- **sury**: Add the Sury PPA for the current operating system.

#### Examples:
```bash
phpx switch 8.2                       # Switch to PHP 8.2 and install if necessary
phpx ext                              # Show installed extensions for the current PHP version
phpx install composer                 # Install Composer globally
phpx install xdebug,redis             # Install multiple PECL packages (xdebug and redis)
phpx serve --host=192.168.0.1 --port=8080  # Serve the current directory at the specified host and port
phpx run 8.2 my_script.php            # Run a PHP script using PHP version 8.2
phpx remove 8.1                       # Remove PHP version 8.1
phpx remove 8.2 ext                  # Remove extensions for given version interactively
phpx remove                           # Remove extensions for current version interactively
```

### gitx Commands

```bash
gitx <command> [options]
```

#### Available Commands:
- **report `<start_commit>` `<end_commit>` `[output_file]`**: Generate a report for PRs, non-PR merges, and standalone commits in the specified commit range. Defaults `end_commit` to `HEAD` and the output file to `pr_and_commits_report.txt`.
- **diff `[output_file]`**: Track changes in staged files and save them to a specified file (default: `diffs.txt`).
- **stash**: Manage stash operations (save, list, apply, drop).
- **compare**: Compare two branches to identify differences.
- **config**: Edit Git configuration interactively.
- **create `<branch_type>` `<name>`**: Create a new branch based on `main`/`master`.
- **sync**: Sync `alpha` and `develop` branches with `main`/`master`.
- **merge `<source_branch>` `<target_branch>`**: Merge one branch into another.
- **tag `<version>`**: Tag the current branch with the specified version.
- **cleanup**: Delete branches that have been merged.
- **summarize**: Display a summary of the repository, including the current branch, total commits, and available remotes and branches.

#### Examples:
```bash
gitx report abc123 HEAD output.txt        # Generate a commit report for the range abc123..HEAD
gitx diff changes.txt                    # Save staged changes to changes.txt
gitx stash                               # Manage stash operations interactively
gitx compare                             # Compare two branches and display differences
gitx create feature login-system         # Create a feature branch named "login-system"
gitx sync                                # Sync alpha and develop with main/master
gitx merge feature/login main            # Merge "feature/login" into "main"
gitx tag v1.0.0                          # Tag the current branch with version "v1.0.0"
gitx cleanup                             # Cleanup branches merged into main/master
gitx summarize                           # Summarize the repository details
```

## Contributing

We welcome contributions! Whether you're fixing bugs, adding new features, or improving documentation, feel free to submit issues or pull requests to enhance **Toolset**.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.