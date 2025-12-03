# dockex

`dockex` is a **Docker helper CLI** that wraps common day-to-day ops into one script:

* Inspect containers in-depth (network, limits, env, mounts, health)
* Fleet summaries with live CPU/MEM stats
* Logs (normal, error-focused, streaming)
* Start/stop/restart, shell, top
* Volume backup & restore (zip-based)
* HTTP benchmarks via ApacheBench
* Resource tuning (CPU shares, memory limits)
* Host/container “doctor” health snapshots
* Safe → aggressive → destructive cleanup modes
* Guided `docker run` for quickly bootstrapping containers

It is **non-invasive** – everything is just thin wrappers over `docker` + a few standard tools.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Docker/dockex" \
  -o /usr/local/bin/dockex && sudo chmod +x /usr/local/bin/dockex
```

---

## Requirements

`dockex` expects these tools to be available on the host:

**Required:**

* `docker`
* `jq`
* `awk`

**Optional (only used by specific commands):**

* `ab` (ApacheBench) – for `benchmark`
* `zip` / `unzip` (inside a temporary Alpine helper container) – for `backup` / `restore`
* `df` – for disk reports in `doctor`

---

## Usage

```bash
dockex <command> [arguments]
```

Commands follow this general style:

```bash
dockex <command> [container_name] [options...]
```

---

## Core Features

### Inspection & fleet overview

* **`info` / `inspect`** – Deep inspect a single container:

    * ID, image, created time, state, health, OS, IP, hostname, command
    * CPU shares, memory limit (human readable)
    * Ports, network, gateways, linked containers
    * Environment variables and mounts

* **`ps`** – “Fleet” snapshot:

    * All containers (running + stopped)
    * CPU usage, memory usage + %, restart policy, health

### Logs & lifecycle

* **`logs` / `logs-errors` / `stream_logs`**

    * Tail normal logs, error-like lines only, or follow logs live.

* **`start` / `stop` / `restart`**

    * Thin safety wrappers over base Docker lifecycle commands.

### Shell & processes

* **`shell`**

    * Exec into a running container:

        * Tries `bash` first, falls back to `sh`.

* **`top`**

    * Quick process view inside the container via `docker top`.

### Resources & profiling

* **`update_resources`**

    * Interactively tune per-container CPU shares + memory limit.

* **`stats`**

    * Time-boxed profiling using `docker stats`:

        * collect samples over `duration` with `interval`
        * summarize avg/max CPU% and MEM%.

* **`benchmark`**

    * ApacheBench HTTP load against container’s `80/tcp`:

        * single-run + multi-instance execution.

### Backup, restore & cleanup

* **`backup` / `restore`**

    * Zip-based volume backup/restore using a temporary Alpine container.

* **`cleanup`**

    * Three levels:

        * `unused` (safe prune),
        * `aggressive` (all unused),
        * `all` (wipe everything – destructive).

### Doctor & inventory

* **`doctor`**

    * Host-wide Docker health snapshot **or** deep dive into one container.

* **`list`**

    * High-level inventory of images, containers, networks, volumes.

* **`create`**

    * Guided `docker run` scaffolding for new containers.

---

## Command Reference

### `list`

```bash
dockex list
```

Shows a multi-section overview:

* **Images** – repository, tag, ID, size
* **Running containers** – name, image, ID, status
* **All containers** – including stopped ones
* **Networks** – name, driver, ID
* **Volumes** – name, driver

---

### `info` / `inspect`

```bash
dockex info <container>
dockex inspect <container>
```

Shows a detailed inspect view for a **running** container:

* ID, image, created timestamp
* State & health (or “No Healthcheck”)
* OS, IP, hostname, command
* Network name, CIDR, gateway, links
* Ports mapping JSON (`NetworkSettings.Ports`)
* CPU shares and memory limits (converted to MB or “Unlimited”)
* Environment variables (if any)
* Mounted volumes, as `host_path -> container_path`

---

### `ps`

```bash
dockex ps
dockex ps <name_pattern>
```

Fleet summary of all containers (running + stopped):

* `NAME`, `IMAGE`, `STATUS`
* CPU usage (`docker stats --no-stream`)
* MEM usage + MEM% (e.g. `120MiB (12.34%)`)
* Restart policy (`HostConfig.RestartPolicy`)
* Health status (if defined)

If `name_pattern` is supplied, only containers whose name contains that substring are shown:

```bash
dockex ps api
```

---

### `logs`

```bash
dockex logs <container> [lines]
```

* Shows last `lines` of logs (`docker logs --tail`)
* Default: `10` lines if omitted.

Examples:

```bash
dockex logs my_container
dockex logs my_container 50
```

---

### `logs-errors`

```bash
dockex logs-errors <container> [lines]
```

* Pulls last `lines` (default `500`) from the container logs

* Filters on common error patterns:

  ```text
  error|exception|panic|critical|failed|oom-kill
  ```

* Prints count + matching lines; falls back gracefully if none found.

Example:

```bash
dockex logs-errors my_container 1000
```

---

### `stream_logs`

```bash
dockex stream_logs <container>
```

Simple wrapper around:

```bash
docker logs -f <container>
```

Streams logs in real-time.

---

### Lifecycle: `start`, `stop`, `restart`

```bash
dockex start <container>
dockex stop <container>
dockex restart <container>
```

* All three validate the container exists first.
* `stop` requires the container to be running; others just require it to exist.

Thin wrappers over:

* `docker start`
* `docker stop`
* `docker restart`

---

### `shell`

```bash
dockex shell <container>
```

Exec into a running container:

* First tries: `docker exec -it <container> bash`
* If `bash` is not available, falls back to: `docker exec -it <container> sh`

Useful for generic images where you don’t remember which shell is present.

---

### `top`

```bash
dockex top <container>
```

Runs `docker top` for a quick “inside container” process table.

---

### `update_resources`

```bash
dockex update_resources <container>
```

Interactive CPU/memory tuning:

1. Validates the container exists.
2. Reads current:

    * CPU shares (`HostConfig.CpuShares`)
    * Memory limit (`HostConfig.Memory`) and prints it as MB or “Unlimited”
3. Prompts for:

    * new CPU shares (e.g., `512`)
    * new memory limit (e.g., `500m`, `1g`)
4. Executes:

```bash
docker update --cpu-shares <shares> --memory <limit> <container>
```

---

### `backup`

```bash
dockex backup <container>
```

Volume backup workflow:

1. Lists all mounts as:

   ```text
   host_path -> container_path
   ```

2. Prompts to choose which one to back up.

3. Uses a temporary Alpine container with `--volumes-from` the target container, plus current directory mounted as `/backup`.

4. Creates a dated zip in the **current working directory**:

   ```text
   <container>-backup-YYYY-MM-DD.zip
   ```

Example:

```bash
dockex backup my_container
# => ./my_container-backup-2025-11-01.zip
```

---

### `restore`

```bash
dockex restore <container> <backup.zip>
```

Restore workflow:

1. Validates container exists.

2. Validates `backup.zip` exists in the current directory (or given path).

3. Runs a temporary Alpine container:

    * `--volumes-from` target container
    * mounts PWD as `/backup`
    * uses `unzip -o` to extract the zip into `/`

4. Files under mounted volume paths are overwritten.

Example:

```bash
dockex restore my_container my_container-backup-2025-11-01.zip
```

---

### `benchmark`

```bash
dockex benchmark <container> [instances] [requests] [concurrency]
```

Parameters:

* `instances`   – number of parallel `ab` runs (default: `3`)
* `requests`    – total requests per run (default: `100`)
* `concurrency` – concurrency per run (default: `10`)

Behaviour:

1. Requires `ab` (ApacheBench) to be installed.
2. Detects:

    * container IP
    * mapped host port for `80/tcp`
3. Runs:

    * a single benchmark: `ab -n <requests> -c <concurrency> http://IP:PORT/`
    * then `instances` parallel runs, each writing to a temp file.
4. Prints each node’s raw `ab` output plus a short summary.

Example:

```bash
dockex benchmark my_container 5 500 50
```

---

### `stats`

```bash
dockex stats <container> [duration] [interval]
```

Parameters:

* `duration` – total seconds to profile (default: `30`)
* `interval` – seconds between samples (default: `2`)

Workflow:

1. Requires a **running** container.

2. Computes sample count = `duration / interval` (at least `1`).

3. At each interval, runs:

   ```bash
   docker stats --no-stream --format '{{.CPUPerc}}||{{.MemUsage}}||{{.MemPerc}}'
   ```

4. Prints each sample:

   ```text
   Sample 1/15: CPU=12.34%, MEM=120MiB (15.67%)
   ```

5. At the end, prints summary:

* Sample count
* Average & max CPU %
* Average & max MEM %
* Last recorded MEM usage

Example:

```bash
dockex stats my_container 60 5
```

---

### `doctor`

```bash
dockex doctor
dockex doctor <container>
```

**Host-level mode (no args):**

```bash
dockex doctor
```

Outputs:

* Key `docker info` fields:

    * Server version
    * Storage driver
    * Cgroup driver
    * Docker root dir
    * Logging driver
* `df -h` for Docker root, if possible
* `docker system df`
* Container list + statuses

Plus a quick hint that `dockex doctor <container>` gives a deeper container view.

**Container mode:**

```bash
dockex doctor my_container
```

Outputs:

* Basic status:

    * Name, image, status, ports
* Inspect highlights:

    * restart policy
    * health status + last healthcheck output (if any)
    * CPU shares
    * memory limit (MB / Unlimited)
* One-shot `docker stats` snapshot for CPU/MEM
* Embedded `logs-errors` (last 500 lines)
* Suggestions, e.g.:

    * set a sane restart policy
    * set a memory limit to avoid host OOM
    * add a healthcheck if missing
    * check logs/health cmd if not healthy

---

### `cleanup`

```bash
dockex cleanup                # default = unused
dockex cleanup unused
dockex cleanup aggressive
dockex cleanup all            # destructive
```

Modes:

1. **`unused`** (default, safer):

    * Shows what will be removed:

        * exited containers
        * dangling images
        * dangling volumes
        * dangling custom networks
    * Asks for confirmation.
    * Runs:

        * `docker container prune -f`
        * `docker image prune -f`
        * `docker volume prune -f`
        * `docker network prune -f`
        * `docker system prune -f`

2. **`aggressive`**:

    * Lists all containers/images/volumes/networks.
    * On confirmation, prunes **all unused** resources:

        * containers, images, volumes, custom networks.

3. **`all`** (wipe-everything mode):

    * Lists **all** resources:

        * running containers
        * all containers
        * all images
        * all volumes
        * user-defined networks
    * On confirmation:

        * stops all running containers
        * removes **all** containers
        * removes **all** images
        * removes **all** volumes
        * removes all user-defined networks (keeps `bridge`, `host`, `none`)

Use `cleanup all` only if you truly want a clean slate.

---

### `create`

```bash
dockex create <image> [name]
```

Guided `docker run` helper:

1. Asks for container name if not provided.

2. Optionally prompts for:

    * port mappings (`host_port:container_port`, comma-separated)
    * env vars (`KEY=VALUE`, comma-separated)
    * volumes (`host_path:container_path`, comma-separated)
    * network name (or default bridge)

3. Builds and prints a final command like:

   ```bash
   docker run -d --name mynginx -p 8080:80 -v /host:/data --network mynet nginx
   ```

4. Executes the command and reports success/failure.

Example:

```bash
dockex create nginx mynginx
```

---

## Examples

```bash
# Show all Docker resources quickly
dockex list

# Fleet view of all containers (CPU/MEM/restart/health)
dockex ps
dockex ps api

# Detailed inspect for a single container
dockex info my_container
dockex inspect my_container

# Logs
dockex logs my_container
dockex logs my_container 50
dockex logs-errors my_container 1000
dockex stream_logs my_container

# Lifecycle
dockex start my_container
dockex stop my_container
dockex restart my_container

# Shell & processes
dockex shell my_container
dockex top my_container

# Benchmark: 3 instances, 100 requests, concurrency 10
dockex benchmark my_container 3 100 10

# Resource tuning & profiling
dockex update_resources my_container
dockex stats my_container 60 5

# Doctor mode
dockex doctor
dockex doctor my_container

# Backup & restore volume data
dockex backup my_container
dockex restore my_container my_container-backup-2025-11-01.zip

# Guided container creation
dockex create nginx mynginx

# Cleanup behavior
dockex cleanup            # safe / unused
dockex cleanup aggressive # prune all unused
dockex cleanup all        # DANGEROUS: wipe everything
```

`dockex` is part of the **Toolset** collection. See the main repo README for an overview of the other tools.
