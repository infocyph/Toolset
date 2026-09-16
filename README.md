# Toolset

A collection of small, focused, shell-based CLIs to streamline day-to-day development and ops on Linux.

Every tool is a standalone Bash script. Install only the tools you need; no shared Toolset runtime is required.

## Tools at a Glance

| Tool        | Area             | Quick Summary                                                                 | Docs                             |
|-------------|------------------|-------------------------------------------------------------------------------|----------------------------------|
| `dockex`    | Docker           | Inspect, benchmark, backup/restore and clean Docker resources                 | [Docker](Docker/README.md)       |
| `phpx`      | PHP              | PHP version / extension manager, FPM/webserver config, doctor & tuner         | [PHP](PHP/README.md)             |
| `gitx`      | Git              | Opinionated Git workflow, cleanup, summaries & changelog helper               | [Git](Git/README.md)             |
| `chromacat` | Terminal output  | Colourful / animated text, banners & ASCII art with themes and palettes       | [ChromaCat](ChromaCat/README.md) |
| `sqlitex`   | SQLite           | Non-interactive, flag-driven SQLite admin, migrations, seeds & tuning         | [Sqlite](Sqlite/README.md)       |
| `cleanx`    | Cleanup & Inodes | Safe, modular disk & inode cleaner; **dry-run by default**, quota/JSON/update | [Clean](Clean/README.md)         |
| `netx`      | Networking       | Network diagnostics, DNS/TLS/HTTP helpers, firewall view & outbound guard     | [Net](Network/README.md)         |

### Tool Documentation

- **dockex** – Docker helper: [Docker](Docker/README.md)
- **phpx** – PHP manager / doctor: [PHP](PHP/README.md)
- **gitx** – Git workflow helper: [Git](Git/README.md)
- **chromacat** – colourful terminal text: [ChromaCat](ChromaCat/README.md)
- **sqlitex** – SQLite CLI: [Sqlite](Sqlite/README.md)
- **cleanx** – disk & inode cleaner: [Clean](Clean/README.md)
- **netx** – network toolbox (DNS/TLS/HTTP/ports/firewall): [Net](Network/README.md)

---

## Installation

Stable installations use **GitHub release assets**, not the mutable `main` branch. Each release publishes the seven standalone CLIs, `install.sh`, `SHA256SUMS`, and `manifest.json`.

### Latest stable release

The release installer defaults to `~/.local/bin` and verifies every selected tool against `SHA256SUMS` before installation:

```bash
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh"
bash install.sh gitx
```

Install several tools or the whole suite:

```bash
bash install.sh gitx netx sqlitex
bash install.sh --all
```

Use another writable installation directory when needed:

```bash
bash install.sh --prefix "$HOME/bin" gitx
```

For a system-wide directory, privilege elevation is explicit; the installer never invokes `sudo` itself:

```bash
sudo bash install.sh --prefix /usr/local/bin gitx
```

### Exact reproducible release

Pin the suite release and verify the installer itself before running it:

```bash
release="2.0"
base="https://github.com/infocyph/Toolset/releases/download/${release}"

curl -fsSLO "${base}/install.sh"
curl -fsSLO "${base}/SHA256SUMS"
grep '  install.sh$' SHA256SUMS | sha256sum -c -

bash install.sh --release "$release" gitx netx
```

The installer also verifies each requested CLI, syntax-checks it, validates its `--version` contract, stages the replacement in the destination directory, and preserves an existing installation as `<tool>.previous`.

### Direct single-file installation

You can install a release asset without the installer:

```bash
release="2.0"
tool="gitx"
base="https://github.com/infocyph/Toolset/releases/download/${release}"

curl -fsSLO "${base}/${tool}"
curl -fsSLO "${base}/SHA256SUMS"
grep "  ${tool}$" SHA256SUMS | sha256sum -c -

install -m 0755 "$tool" "$HOME/.local/bin/$tool"
```

Stable Toolset suite tags use `MAJOR.MINOR`; Toolset 2.0 is published from immutable tag `2.0`.


<!-- TOOLSET2-ROOT-CONTRACT:START -->
## Support, Safety & Automation Contracts

- [CLI dependency/capability, security and output contracts](docs/cli-contracts.md)
- [Toolset 2.0 implementation plan](docs/plans/toolset-2.0-standalone-linux-cli-hardening-plan.md)
- [Live 2.0 implementation tracker](docs/plans/toolset-2.0-progress-tracker.md)
- [2.0 security review](docs/security-review.md)

Toolset targets Linux with capability-gated features rather than claiming identical behavior on every distribution. CI smoke-covers Debian 13, Ubuntu 24.04, Fedora 42 and Alpine 3.22 with Bash. High-impact operations remain tool-specific and are documented in each tool README and the suite contract.

Released consumers should pin immutable stable tag `2.0` or the tagged commit SHA; published assets are immutable.
<!-- TOOLSET2-ROOT-CONTRACT:END -->
---

## Development Builds

The `main` branch is development state and is intentionally **not** the stable installation channel. If you explicitly test a development snapshot, pin a commit SHA rather than relying on a moving branch URL.

---

## Contributing

Bug fixes, small UX improvements, new subcommands or better docs are welcome. Open an issue or PR against this repository.

---

## License

Licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
