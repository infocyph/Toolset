# dockex

`dockex` wraps common Docker operations, inspection, light benchmarking and backups into one CLI.

It is **non-invasive** (just calls `docker` under the hood) and is safe to drop into existing environments.

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Docker/dockex" \
  -o /usr/local/bin/dockex && sudo chmod +x /usr/local/bin/dockex
````

## Usage

```bash
dockex <command >[arguments]
```

### Commands

| Command                                                        | Description                                                    |
|----------------------------------------------------------------|----------------------------------------------------------------|
| `list`                                                         | Show Docker images, containers, networks, and volumes          |
| `info` / `stats` / `inspect` `<container>`                     | Detailed container info (CPU, memory, I/O, env, ports, health) |
| `logs` `<container> [lines]`                                   | Show last N lines of logs (default: 10)                        |
| `stream_logs` `<container>`                                    | Stream logs in real time                                       |
| `start` `<container>`                                          | Start a stopped container                                      |
| `stop` `<container>`                                           | Stop a running container                                       |
| `restart` `<container>`                                        | Restart a container                                            |
| `benchmark` `<container> [instances] [requests] [concurrency]` | ApacheBench stress test against a container                    |
| `update_resources` `<container>`                               | Interactively adjust CPU shares & memory limits                |
| `backup` `<container>`                                         | Backup container volume data                                   |
| `restore` `<container> <backup.zip>`                           | Restore container data from backup                             |
| `create` `<image> [name]`                                      | Guided `docker run` scaffolding                                |
| `cleanup` `[unused\|aggressive\|all]`                          | Prune and cleanup Docker resources                             |

## Examples

```bash
# Show all Docker resources
dockex list

# View detailed stats for my_container
dockex info my_container

# Tail last 10 lines of logs for my_container
dockex logs my_container 10

# Stream logs live
dockex stream_logs my_container

# Start / stop / restart
dockex start my_container
dockex stop my_container
dockex restart my_container

# Run benchmark: 3 instances, 100 requests each, concurrency 10
dockex benchmark my_container 3 100 10

# Update CPU and memory interactively
dockex update_resources my_container

# Backup and restore volumes
dockex backup my_container
dockex restore my_container backup-2025-11-01.zip

# Create a new nginx container named mynginx
dockex create nginx mynginx

# Cleanup unused Docker resources
dockex cleanup unused
```
