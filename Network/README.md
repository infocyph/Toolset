# netx

`netx` is a **network toolbox CLI** for diagnostics, security and quick benchmarks:

* End-to-end “doctor” checks for any host (DNS, ping, route, port, HTTP, TLS)
* DNS helpers (resolve/dump/compare/trace/reverse/system)
* HTTP latency breakdowns (DNS/connect/TLS/TTFB/total)
* HTTP sniff (headers/body + curl timings) and packet sniff (tcpdump wrapper)
* TLS certificate inspection, expiry checks and chain view
* Port & connection inspection (with basic **risk scoring** for outbound flows)
* Outbound connection **baseline + diff + watch** (“what just started talking out?”)
* Suspicious listener detection (wildcard/high ports/temp binaries)
* Interface / IP / route overview and public IP detection
* Simple watchers (ping/HTTP) and waiters (wait-for-port)
* Stack-level checks (service endpoints in a small config)
* Network namespace helpers for container/network debugging
* Firewall summary & full rules dump (nftables/iptables)
* One-shot “net report” snapshot to a file

It’s **non-invasive** – just thin wrappers over `ip`, `ss`/`netstat`, `curl`, `ping`, `openssl`, `nft`/`iptables`, etc.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Network/netx" \
  -o /usr/local/bin/netx && sudo chmod +x /usr/local/bin/netx
```

(Adjust the path if your repo layout is different.)

---

## Requirements

`netx` expects a **Linux** host with basic networking tools.

**Core (most commands):**

* `ip` (from `iproute2`)
* `ss` or `netstat`
* `awk`
* `sed`
* `grep`
* `date`
* `tput` (optional, for color)

**Diagnostics / HTTP / TLS:**

* `curl` – HTTP/HTTPS, proxy tests, public IP, benchmarks
* `ping` – host reachability & RTT
* `traceroute` **or** `mtr` – path tracing / route hops
* `openssl` – TLS info / verify / chain

**Firewall / Namespaces (optional, only for specific commands):**

* `nft` or `iptables` – firewall summary / rules
* `ufw` – if you want UFW summary
* `ip netns` – for namespace listing and exec

**Sniffing / pretty output (optional):**

* `tcpdump` – for `netx sniff pkt` (packet capture)
* `jq` – for pretty-printing JSON bodies in `netx sniff http`
* `timeout` – to enforce `--seconds` limits for some long-running commands (if present)

If a tool is missing, `netx` will tell you and skip or degrade that feature.

### Tool matrix (what you actually need)

This is a quick map from **netx features → external tools**.

**Always required (netx won’t be very useful without these):**

* `bash` (v4+ recommended)
* `ip` (`iproute2`)
* `ss` (**preferred**) or `netstat`
* `awk`, `sed`, `grep`, `cut`, `tr`, `xargs`

**Common (most people should have these installed):**

* `curl` – HTTP/HTTPS probes, proxy tests, public IP, benchmarks, sniff http
* `ping` – reachability + RTT (doctor/bench/watch)
* `openssl` – TLS info/verify/chain

**Feature-specific (install when you need the command):**

* Path tracing (`netx trace`, `netx path trace`, doctor route section):
  * `mtr` (**best**) or `traceroute` (fallback)
* Port checks (`netx port check`, `netx wait port`, doctor port section):
  * `nc` (netcat)
* Packet capture (`netx sniff pkt`):
  * `tcpdump` (**requires root/sudo**)
  * `timeout` (optional) for `--seconds`
* JSON pretty output (`netx sniff http` when body is JSON, or piping JSON output):
  * `jq` (optional but recommended)
* Firewall (`netx fw summary`, `netx fw list`):
  * `nft` (**preferred**) or `iptables` / `iptables-save`
  * `ufw` (optional; only if you want UFW status)
* Network namespaces (`netx ns ...`):
  * `ip netns` (part of `iproute2`)
* Docker network awareness (doctor’s docker subnet summary):
  * `docker` (optional)
* Bench HTTP (`netx bench http`):
  * `xargs` (for concurrency via `xargs -P`)

### Quick install (common distros)

**Debian/Ubuntu:**

```bash
sudo apt-get update && sudo apt-get install -y \
  iproute2 iputils-ping curl openssl netcat-openbsd \
  mtr-tiny traceroute tcpdump jq coreutils \
  nftables iptables
```

**Alpine:**

```bash
sudo apk add --no-cache \
  iproute2 iputils curl openssl netcat-openbsd \
  mtr traceroute tcpdump jq coreutils \
  nftables iptables
```

**Fedora/RHEL/CentOS (dnf):**

```bash
sudo dnf install -y \
  iproute iputils curl openssl nmap-ncat \
  mtr traceroute tcpdump jq coreutils \
  nftables iptables
```

**Optional quality-of-life:**

* `tput` – colored output (auto-detected)
* `timeout` – timeboxing long/streaming commands in more places

---

## Usage

```bash
netx [--json] [--quiet] <command> [subcommand] [options]
```


### Global output flags

`netx` supports two global flags that can be placed **before** the command:

* `--quiet` – suppress banners/sections and print only the primary value where it makes sense (more script-friendly).
* `--json` – emit machine-readable JSON where applicable.  
  For long-running/streaming commands (e.g. `watch`, `wait`, `sniff pkt`, `guard watch`) output stays streaming (no capture), so `--json` is effectively passthrough.

Examples:

```bash
netx --quiet ip public --ipv4
netx --json route explain example.com | jq .
```


Examples:

```bash
netx doctor example.com --http --tls
netx dns dump example.com --full
netx http trace https://example.com
netx tls verify example.com
netx port ls --listening --tcp --process
netx conn ls --suspicious-only
netx guard watch --interval 30 --exclude-user sshd,systemd --exclude-cidr 10.,192.168.
netx ip info
netx fw summary
```

---

## Core Features

### 1. Host “doctor” (end-to-end checks)

* **`netx doctor <host> [--port P] [--http] [--tls] [--raw]`**

Runs a mini health-check against a host:

* DNS lookup (+ timing, fallback to `/etc/hosts`/NSS)

* Ping summary (min/avg/max/jitter) if `ping` is available

* First hops route using `traceroute` or `mtr`

* Port reachability using `nc`

* Optional HTTP probe:

    * status code, total time, response size, redirect count

* Optional TLS summary:

    * basic certificate subject, issuer and validity dates

Useful when “something is wrong with this host” and you want a quick end-to-end snapshot.

---

### 2. DNS toolbox

Under `netx dns`:

* `resolve` – simple resolve with optional type/resolver
* `dump` – multi-type dump (A/AAAA/CNAME/MX/NS/TXT, plus SRV if `--full`)
* `compare` – compare answers across resolvers (e.g. `1.1.1.1,8.8.8.8,9.9.9.9`)
* `trace` – `dig +trace` style lookup
* `reverse` – PTR lookup for an IP
* `system` – show `/etc/resolv.conf` and `systemd-resolve --status` (if present)
* `whoami` – show resolver-view + egress IP (best-effort, via a chosen resolver)
* `flush` – flush DNS caches (best-effort: systemd-resolved/nscd/macOS)
* `hosts` – check `/etc/hosts` for a given hostname

Great for “DNS is lying” or “why is this host resolving differently here vs there?”.

---

### 3. HTTP / Proxy helpers

Under `netx http`:

* `get` – GET request with optional headers/body/JSON and timeout
* `head` – HEAD request
* `trace` – detailed timing breakdown:

    * DNS, connect, TLS, TTFB, total, status, size, redirects

Under `netx proxy`:

* `env` – show current `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`
* `test` – check connectivity **without** proxy vs **with** proxy:

    * first run with `NO_PROXY="*"` (forced direct)
    * then run with current proxy env

Good for debugging “only works when proxy is off/on” problems.

---

### 4. Benchmarks (curl-based)

Under `netx bench`:

* `http` – simple HTTP benchmark using parallel `curl`:

    * `--requests N` – total requests (default `50`)
    * `--concurrency N` – parallelism via `xargs -P` (default `5`)
    * `--timeout N` – per-request timeout (default `5s`)

  Aggregates:

    * min/avg/p95/p99/max latency (ms)
    * total requests
    * success count (2xx–3xx)
    * approximate requests/second

* `ping` – ICMP ping benchmark:

    * `--count N` (default `50`)
    * prints normal `ping` output plus RTT summary (min/avg/max/jitter)

---

### 5. TLS inspection

Under `netx tls`:

* `info <host> [--port P]`:

    * subject, issuer, validity period

* `verify <host> [--port P] [--strict]`:

    * prints `notAfter` date and days remaining
    * classifies as:

        * **OK**
        * **WARN** (expiring soon, < 30 days)
        * **EXPIRED**

* `chain <host> [--port P]`:

    * shows each certificate in the chain:

        * subject
        * issuer

All are thin wrappers over `openssl s_client` + `openssl x509`.

---

### 6. Port & connection inspection (with risk scoring)

Under `netx port`:

* `ls [--listening] [--tcp] [--udp] [--process]`:

    * uses `ss` (or falls back to `netstat`)
    * prints:

      ```text
      Proto  Local                    Peer                     PID    Process
      ```

* `find <port> [--process]`:

    * who is listening on this port?

* `check <host> <port> [--timeout N] [--udp]`:

    * thin wrapper over `nc` – prints `OK`/`FAIL`

* `scan <host> [--ports 80,443,3306]`:

    * quick TCP check over a small port list.

Under `netx conn`:

* `ls [--all] [--outbound] [--listening] [--suspicious-only]`:

    * prints current connections with a **simple risk score**:

      ```text
      !   Proto Local                 Remote                State      PID   Risk     Process
      *   tcp   10.0.2.15:42318       185.x.y.z:4444        ESTAB      4242  HIGH     python
      ```

    * scoring heuristics consider:

        * public vs private destination IP
        * high remote ports not in common-safe set (`22,53,80,123,443,587,993,995`)
        * suspicious process names (`bash`, `python`, `nc`, `socat`, `curl`, `wget`, etc.)
        * binary running from `/tmp`, `/dev/shm`, `/var/tmp`
        * non-root user talking to odd public ports

    * `--suspicious-only` shows only flagged flows.

* `record [--interval N] [--duration N] [--out file]`:

    * periodically logs `ss -tunp` / `netstat -tunp` to a file.

* `summary --file <file>`:

    * summarises a recorded file:

        * unique remote endpoints (hosts/ports).

This is meant for “what are we currently talking to?” and “did something weird just open a tunnel out?”.

---

### 7. Outbound Guard (baseline + alert)

Under `netx guard`:

* `snapshot [--file path]`:

    * captures a **baseline** of current connections into a normalized text file.

* `diff [--file path]`:

    * shows **new outbound connections** since the baseline:

      ```text
      == New outbound connections since baseline ==
        tcp   10.0.2.15:42318 -> 185.x.y.z:4444  4242   python
      ```

* `watch [--interval N] [--file path]         [--exclude-user list] [--exclude-port list]         [--exclude-cidr list] [--exec cmd]`:

    * continuously compares against the last snapshot and prints **ALERT** sections for new connections.

    * Exclusions:

        * `--exclude-user` – comma-separated process names (`sshd,systemd-resolved`)
        * `--exclude-port` – comma-separated ports (local or remote)
        * `--exclude-cidr` – simple prefix-style strings (`10.,192.168.,172.16.`)

    * `--exec cmd`:

        * if set, new lines are piped into this command (for logging/notification/hooks).

Nice for lightweight EDR-style “if any new process starts talking out, tell me”.

---

### 8. Suspicious listeners

Under `netx sec`:

* `listeners [--exclude-user list] [--exclude-port list]`:

    * scans listening sockets and flags “interesting” ones:

        * listening on `0.0.0.0`, `[::]` or `*`
        * port > 1024
        * binary living under `/tmp` or `/dev/shm`

    * prints:

      ```text
      [WARN] tcp   0.0.0.0:4444         pid=4242  proc=python        path=/tmp/.x/py
      ```

Use exclusions to ignore known-good daemons (`sshd`, `docker-proxy`, etc.).

---

### 9. IP / Interfaces / Routes

Under `netx ip`:

* `info`:

    * prints an **interface → IPv4 → IPv6** table
    * default routes
    * DNS configuration (via `dns_system`)

* `public [--ipv4] [--ipv6]`:

    * gets public IP via HTTPS:

        * IPv4 via `api.seeip.org` / `ipv4.icanhazip.com`
        * IPv6 via `api.seeip.org` / `ipv6.icanhazip.com`

Under `netx if`:

* `ls`:

    * shows all interfaces with primary IPv4 (plus extra count):

      ```text
      Index  Name                 IPv4 (primary)
        1     lo                   127.0.0.1/8
        2     enp4s0               192.168.68.42/22
        3     wlp0s20f3            10.9.55.119/8
        4     docker0              172.17.0.1/16
      ```

* `stats <iface>`:

    * `ip -s link show` for RX/TX counters and errors.

Under `netx route`:

* `show`:

    * prints all routes in a compact table:

      ```text
      Type     Destination          Dev          Extra
      default  default              enp4s0       proto dhcp src 192.168.68.42 metric 100
      other    10.0.0.0/8           wlp0s20f3    proto kernel scope link src 10.9.55.119
      ```

---

### 10. Watchers & Waiters

Under `netx watch`:

* `ping <host> [--interval N]`:

    * loops; each iteration runs a short `ping -c 3` and prints timestamped output.

* `http <url> [--interval N] [--expect-status CODE]`:

    * loops HTTP checks; prints:

      ```text
      2025-01-01T12:00:00+00:00 status=200 (expect 200)
      ```

Under `netx wait`:

* `port <host> <port> [--timeout N]`:

    * waits until TCP port is reachable (via `nc`), or times out.

Good for scripts and stack bring-up (“wait until Postgres is ready”).

---

### 11. Stack check

Under `netx stack`:

* `check <name> [--config /path/to.conf]`:

    * stack config format (INI-ish):

      ```ini
      [services]
      api=http://localhost:8080/health
      db=db.internal:5432
      cache=127.0.0.1:6379
      ```

    * If `--config` not given, defaults to:
      `${NETX_STACK_DIR:-$HOME/.config/netx/stacks}/<name>.conf`.

    * For each service:

        * `http://` targets → `http_trace` (HTTP timings & status)
        * `host:port` targets → `port_check` (`OK`/`FAIL`)

Good for quick health snapshots of small, multi-service stacks.

---

### 12. Namespaces

Under `netx ns`:

* `ls`:

    * `ip netns list` – shows available network namespaces.

* `inspect <ns>`:

    * (`ip netns exec`) interface addresses + routes for the namespace.

* `exec <ns> <cmd...>`:

    * run an arbitrary command inside a network namespace.

Handy when debugging container stacks or overlay networks that use netns.

---

### 13. Path trace

Under `netx path`:

* `trace <host> [--max-hops N]`:

    * also available as a shortcut: `netx trace <host> [--max-hops N]`

* `trace <host> [--max-hops N]`:

    * uses `mtr` if available, else `traceroute`.
    * default max hops: `15`.

When you just want “show me the path to this host” with a single command.

---

### 14. Firewall

Under `netx fw`:

* `summary`:

    * For `nft`:

        * prints the first ~80 lines of `nft list ruleset`
        * hints to use `netx fw list --raw` for full dump

    * For `iptables`:

        * `iptables -L -n --line-numbers`

    * If `ufw` exists:

        * adds `ufw status` section.

* `list [--raw]`:

    * `nft list ruleset` or `iptables-save`
    * without `--raw` it just indents for readability.

---

### 15. Net report

* **`netx report [--out file]`**

Runs a compact mini-report and writes it to a file (default: `~/.netx/net-report.txt`):

* Interface table + default route + DNS
* Routes
* Firewall DNS info (via `dns_system`)
* Listening TCP ports (`port_ls --listening --tcp --process`)
* Outbound connections (`conn_ls --outbound`)

Perfect to attach to tickets: “here’s the network state from this host at time X”.

---

### 16. Sniff (HTTP + Packet)

Under `netx sniff`:

* `http <url> [curl-args...]`:

    * performs a single HTTP probe using `curl` and prints:

        * final effective URL (after redirects)
        * timing breakdown (DNS/connect/TLS/TTFB/total)
        * response headers
        * response body (first ~400 lines)
        * if `jq` is available and the body is JSON (or parses as JSON), it pretty-prints it

  Examples:

  ```bash
  netx sniff http https://example.com
  netx sniff http https://example.com -H 'Accept: application/json'
  netx sniff http https://example.com -- -v   # pass any curl flags as usual
  ```

* `pkt <iface> [options] [-- <bpf-filter...>]`:

    * thin wrapper over `tcpdump` (requires root/sudo)
    * safe defaults: snaplen defaults to a small value for lower overhead unless overridden
    * supports capture limits and rotating pcap output

  Options:

  * `--count N` – stop after N packets
  * `--seconds N` – stop after N seconds (uses `timeout` if available)
  * `--write file.pcap` – write capture to pcap
  * `--rotate MB` + `--files N` – rotate pcap output (`tcpdump -C/-W`)
  * `--snaplen N` – set snap length (capture bytes per packet)
  * `--no-resolve` – no DNS/service name resolution (`-n`)
  * `--verbose` – more decode (`-vv`)
  * `--promisc off` – disable promiscuous mode (`-p`)

  Examples:

  ```bash
  netx sniff pkt any --no-resolve --seconds 10 -- port 443
  netx sniff pkt eth0 --write /tmp/cap.pcap --rotate 25 --files 4 -- 'tcp and (port 80 or port 443)'
  ```

## Command Reference & Examples

```bash
# 1) End-to-end check to a host
netx doctor example.com --http --tls

# 2) DNS basics
netx dns resolve example.com
netx dns dump example.com --full
netx dns compare example.com --type A --resolver 1.1.1.1,8.8.8.8

# 3) HTTP tracing & proxy
netx http trace https://example.com
netx proxy env
netx proxy test https://example.com

# 4) Benchmarks
netx bench http https://example.com --requests 100 --concurrency 10
netx bench ping 8.8.8.8 --count 100

# 5) TLS
netx tls info example.com
netx tls verify example.com
netx tls chain example.com

# 6) Ports & connections
netx port ls --listening --tcp --process
netx port find 5432 --process
netx port scan localhost --ports 22,80,443,3306
netx conn ls --outbound
netx conn ls --suspicious-only

# 7) Outbound Guard
netx guard snapshot
netx guard diff
netx guard watch --interval 30 \
  --exclude-user sshd,systemd-resolved \
  --exclude-cidr 10.,192.168. \
  --exec 'tee -a /var/log/netx-guard.log'

# 8) Suspicious listeners
netx sec listeners --exclude-user sshd,docker-proxy

# 9) IP / interfaces / routes
netx ip info
netx ip public --ipv4
netx if ls
netx if stats enp4s0
netx route show

# 10) Watchers / waiters
netx watch ping 8.8.8.8 --interval 10
netx watch http https://example.com --interval 5 --expect-status 200
netx wait port localhost 5432 --timeout 60

# 11) Stack check
netx stack check myapp
netx stack check myapp --config ~/.config/netx/stacks/myapp.conf

# 12) Namespaces
netx ns ls
netx ns inspect ns-docker
netx ns exec ns-docker curl -sS http://10.0.0.5:8080/health

# 13) Sniff
netx sniff http https://example.com
netx sniff pkt any --no-resolve --seconds 5 -- port 443

# 14) Route explain / path trace shortcut
netx route explain example.com
netx trace 8.8.8.8

# 15) DNS whoami / flush
netx dns whoami --resolver 1.1.1.1
netx dns flush

# 16) Path & firewall & report
netx path trace 8.8.8.8
netx fw summary
netx fw list --raw
netx report --out /tmp/net-report.txt
```

`netx` is part of the **Toolset** collection. See the main repo README for an overview of the other tools.
