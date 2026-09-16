# Toolset 2.0 Security Review

This document records the repository-wide security closeout required by the Toolset 2.0 hardening plan. The permanent CI audit is `tests/security-audit.sh`; it scans all seven distributable scripts plus `install.sh` and uploads the retained high-impact call-site report.

## Hard blockers

The final audit treats the following as release blockers:

- internal `eval` execution;
- sourcing writable `config`, `settings`, or `credentials` as shell code;
- raw `curl | sh` / `curl | bash` execution;
- `chmod 777` / world-writable runtime setup;
- stable Toolset downloads from mutable raw `main`/`master` URLs;
- predictable shared sensitive `/tmp` state;
- interpolated double-quoted `bash -c` / `sh -c` command strings.

The Phase 5 audit reports **none** for these blocker classes.

## Retained high-impact constructs

### Recursive deletion

Retained recursive deletion is limited to explicit product behavior or private temporary-state cleanup:

- `cleanx` uses `rm -rf -- "$root"` only after its destructive-root validation and dry-run/approval boundary;
- installer/self-update/test-style temporary directories come from `mktemp -d` and are removed by cleanup traps;
- `gitx` temporary AI/report state is privately created before recursive cleanup;
- `dockex` benchmark temporary directories are local per-run state.

No `find -delete` call remains in the distributable/runtime sources scanned by the audit.

### `bash -c` / `sh -c`

A small number of shell workers remain for explicit fixed-purpose operations:

- `dockex` shell availability check executes the fixed command `exit 0` inside a selected container;
- `dockex` backup/restore helper containers use fixed shell programs and pass mount/archive values as positional parameters (`$1`, `$2`) rather than interpolating them into shell source;
- `netx` parallel HTTP benchmark uses a fixed worker program and passes URL/timeout as positional parameters.

During the final audit, the telnet fallback in `dockex trace` was found interpolating host/port into a double-quoted `sh -c` string. It was removed; the probe now pipes fixed input directly to `docker exec -i ... telnet "$host" "$port"`. The permanent audit blocks reintroduction of interpolated shell-command strings.

### Root and privilege boundaries

Root/sudo checks remain only where host capabilities require them:

- `phpx` system package, service, repository and system-configuration mutations;
- `cleanx` system cleanup;
- `netx` packet capture, firewall and namespace operations when the host requires elevated privilege;
- Docker operations rely on the selected Docker endpoint/socket permissions rather than unconditional sudo.

Help/version and other read-only/generic paths are not globally root-gated.

### Network downloads and supply chain

Stable Toolset installation/self-update downloads release assets and verifies SHA-256 data from the same immutable release. Stable paths do not consume Toolset `main`/`master` raw content.

Other network downloads are command-specific. Examples include:

- Composer installer plus published installer signature validation in `phpx`;
- bounded Sury repository/keyring retrieval with package identity validation;
- Gemini requests in `gitx` with timeout, response-size and staged-diff limits;
- bounded diagnostic HTTP/TLS/public-IP operations in `netx`.

Release tags/assets are immutable. Before merge, `tests/release-delivery.sh` exercises exact tag `2.0` through a trusted local mirror and injects a transient connection reset; after merge, the maintainer creates tag `2.0` and the release workflow repeats live verification.

### Secrets and environment output

- `dockex` container environment values are redacted by default and require explicit opt-in for raw values;
- `gitx` Gemini credentials are not stored unless explicitly requested; persisted credentials use restrictive permissions;
- JSON/machine output paths keep human diagnostics on stderr where provided by the tool contract;
- logging/config code reviewed during Phase 2/3 avoids intentional secret emission.

### Temporary files and concurrency

Sensitive/interactively generated state uses `mktemp`/`mktemp -d` or private XDG/runtime paths. Fixed globally shared temp filenames that could be symlink-raced are prohibited by the audit. Cleanup traps cover updater, installer and relevant per-command temporary state.

### Background workers and cleanup

Retained background workers are bounded task workers (for example lint/benchmark fan-out), not unattended daemons. Commands owning temporary files/directories install cleanup traps where required. CI keeps background-process and trap call sites visible in the security report so future changes receive explicit review.

## Tool-specific boundaries

The consolidated dependency, output and security contracts live in [`cli-contracts.md`](cli-contracts.md). Each per-tool README also carries standardized sections for requirements, capabilities, destructive/security behavior, output/exit behavior and self-update.
