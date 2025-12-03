# dockex

`dockex` wraps common Docker operations, inspection, light benchmarking and backups into one CLI.

It is **non-invasive** (just calls `docker` under the hood) and is safe to drop into existing environments.

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Docker/dockex" \
  -o /usr/local/bin/dockex && sudo chmod +x /usr/local/bin/dockex
sudo chmod +x /usr/local/bin/dockex
````

## Requirements

`dockex` expects these tools to be available:

* `docker`
* `jq`
* `awk`

Optional (used only by specific commands):

* `ab` (ApacheBench) – for `benchmark`
* `zip` / `unzip` (inside the Alpine helper container) – for `backup` / `restore`

## Usage

```bash
dockex <command> [arguments]
```

### Commands

| Command                                                      | Description                                                                                       |
|--------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `list`                                                       | Show Docker images, containers, networks, and volumes                                             |
| `info` / `inspect <container>`                               | Detailed container info (image, state, health, IP, ports, env, volumes, CPU shares, memory limit) |
| `ps [name_pattern]`                                          | Fleet summary: image, status, CPU%, memory usage, restart policy, health (optional name filter)   |
| `logs <container> [lines]`                                   | Show last *N* lines of logs (default: 10)                                                         |
| `logs-errors <container> [lines]`                            | Show only error-like log lines (default: last 500 lines, filtered by common error patterns)       |
| `stream_logs <container>`                                    | Stream logs in real time (`docker logs -f`)                                                       |
| `start <container>`                                          | Start a stopped container                                                                         |
| `stop <container>`                                           | Stop a running container                                                                          |
| `restart <container>`                                        | Restart a container                                                                               |
| `shell <container>`                                          | Exec into a container (`bash` if available, otherwise `sh`)                                       |
| `top <container>`                                            | Show processes running inside a container (`docker top`)                                          |
| `update_resources <container>`                               | Interactively adjust CPU shares & memory limits (`docker update`)                                 |
| `backup <container>`                                         | Interactively select and back up a mounted volume into a dated `.zip` in the current directory    |
| `restore <container> <backup.zip>`                           | Restore container data from a backup zip into the container’s volumes                             |
| `benchmark <container> [instances] [requests] [concurrency]` | ApacheBench HTTP stress test against container’s port `80` (single + multi-instance)              |
| `stats <container> [duration] [interval]`                    | Profile CPU% / MEM% over time using `docker stats` (default: 30s duration, 2s interval)           |
| `doctor`                                                     | Doctor mode: host-wide summary (no args) or deep health check for a specific container            |
| `cleanup [unused\|aggressive\|all]`                          | Prune and cleanup Docker resources (safe/unused, aggressive, or wipe-all)                         |
| `create <image> [name]`                                      | Guided `docker run` scaffolding (ports, env, volumes, network)                                    |

### Command Details

**Inspection & overview**

* `dockex info my_container`
  Detailed inspect view: image, created time, state, health, OS, IP, hostname, command, network, ports, CPU shares, memory limit, env vars, mounts.

* `dockex ps`
  Shows all containers (running + stopped) with:

    * NAME, IMAGE, STATUS
    * CPU usage (from `docker stats --no-stream`)
    * Memory usage + percentage
    * Restart policy
    * Health status

  You can filter by name substring:

  ```bash
  dockex ps api
  ```

**Logs**

* `dockex logs my_container [lines]`
  Tail last `lines` (default `10`) from container logs.

* `dockex logs-errors my_container [lines]`
  Tail last `lines` (default `500`) and show only lines matching:

  ```text
  error|exception|panic|critical|failed|oom-kill
  ```

* `dockex stream_logs my_container`
  Simple wrapper around `docker logs -f`.

**Lifecycle**

* `dockex start my_container`
* `dockex stop my_container`
* `dockex restart my_container`

Thin wrappers around `docker start/stop/restart` with validation.

**Shell & processes**

* `dockex shell my_container`

    * Tries `bash` first (`docker exec -it <name> bash`)
    * Falls back to `sh` if `bash` isn’t present

* `dockex top my_container`
  Runs `docker top` for a quick process view.

**Resources**

* `dockex update_resources my_container`

  Interactive:

    * Shows current CPU shares & memory limit
    * Prompts:

        * `CPU shares (e.g. 512)`
        * `Memory (e.g. 500m, 1g)`
    * Calls `docker update` with the values.

**Backup & restore**

* `dockex backup my_container`

    * Lists mounted volumes as `host_path -> container_path`
    * Prompts you to choose one
    * Creates a dated zip:
      `./<container>-backup-YYYY-MM-DD.zip`

* `dockex restore my_container backup-YYYY-MM-DD.zip`

    * Mounts the backup zip into a temporary Alpine container
    * Unzips into `/` with `--volumes-from` the target container
    * Overwrites existing files under the mounted volume paths

**Benchmark**

* `dockex benchmark my_container [instances] [requests] [concurrency]`

    * Requires `ab` (ApacheBench) to be installed
    * Reads container IP + mapped host port for `80/tcp`
    * Runs:

        * One single-node benchmark: `requests` (default `100`) with concurrency `concurrency` (default `10`)
        * Then `instances` (default `3`) concurrent `ab` runs
    * Prints the raw `ab` output for each node and a summary.

**Stats profiling**

* `dockex stats my_container [duration] [interval]`

  Example:

  ```bash
  dockex stats my_container 60 5
  ```

    * Collects `docker stats --no-stream` every `interval` seconds for `duration` seconds
    * Prints each sample (CPU%, MEM usage, MEM%)
    * At the end prints:

        * average/max CPU%
        * average/max MEM%
        * last memory usage

**Doctor**

* `dockex doctor`

  Host-wide summary:

    * `docker info` key fields (version, drivers, root dir)
    * `df -h` for Docker root (if available)
    * `docker system df`
    * Container list + statuses

* `dockex doctor my_container`

  Container-focused health check:

    * Basic status: name, image, status, ports
    * Inspect:

        * restart policy
        * health status + last healthcheck output (if any)
        * CPU shares
        * memory limit
    * One-shot `docker stats` snapshot
    * Embedded `logs-errors` (last 500 lines)
    * Suggestions:

        * restart policy hints
        * memory limit hints
        * healthcheck hints

**Cleanup**

* `dockex cleanup unused` (default)

    * Safe prune:

        * exited containers
        * dangling images
        * dangling volumes
        * dangling custom networks
        * `docker system prune -f`

* `dockex cleanup aggressive`

    * Aggressive prune:

        * all unused containers / images / volumes / custom networks

* `dockex cleanup all`

    * **Destructive**:

        * Stops all running containers
        * Removes **all** containers, images, volumes, custom networks

**Create**

* `dockex create nginx mynginx`

  Guided `docker run`:

    * Asks for:

        * ports (`host:container`, comma-separated)
        * env vars (`KEY=VALUE`, comma-separated)
        * volumes (`host_path:container_path`, comma-separated)
        * network name (optional)
    * Assembles and runs a full `docker run -d --name ...` command.

## Examples

```bash
# Show all Docker resources
dockex list

# Overview of all containers (CPU/MEM/restart/health)
dockex ps

# Filter summary to containers whose name contains "api"
dockex ps api

# View detailed inspect-like info for my_container
dockex info my_container
dockex inspect my_container

# Tail last 10 lines of logs for my_container
dockex logs my_container
dockex logs my_container 50

# Show only error-like lines from last 1000 log lines
dockex logs-errors my_container 1000

# Stream logs live
dockex stream_logs my_container

# Start / stop / restart
dockex start my_container
dockex stop my_container
dockex restart my_container

# Shell into container (bash if present, else sh)
dockex shell my_container

# View processes inside the container
dockex top my_container

# Run benchmark: 3 instances, 100 requests each, concurrency 10
dockex benchmark my_container 3 100 10

# Update CPU and memory interactively
dockex update_resources my_container

# Profile container for 60 seconds with 5-second intervals
dockex stats my_container 60 5

# Doctor mode: host-level summary
dockex doctor

# Doctor mode: deep health check for a specific container
dockex doctor my_container

# Backup and restore volumes
dockex backup my_container
dockex restore my_container my_container-backup-2025-11-01.zip

# Create a new nginx container named mynginx
dockex create nginx mynginx

# Cleanup unused Docker resources
dockex cleanup           # same as 'cleanup unused'
dockex cleanup aggressive
dockex cleanup all       # DANGEROUS: wipes everything
```
