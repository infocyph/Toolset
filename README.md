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

The release installer defaults to `/usr/local/bin` and verifies every selected tool against `SHA256SUMS` before installation:

```bash
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh"
sudo bash install.sh gitx
```

Install several tools or the whole suite:

```bash
sudo bash install.sh gitx netx sqlitex
sudo bash install.sh --all
```

### One liners

For a quick all/individual install, use the same checksum-verifying installer in one command.

```bash
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh" && sudo bash install.sh --all && rm -f install.sh
```

```bash
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh" && sudo bash install.sh chromacat && rm -f install.sh
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh" && sudo bash install.sh cleanx && rm -f install.sh
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh" && sudo bash install.sh dockex && rm -f install.sh
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh" && sudo bash install.sh gitx && rm -f install.sh
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh" && sudo bash install.sh netx && rm -f install.sh
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh" && sudo bash install.sh phpx && rm -f install.sh
curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh" && sudo bash install.sh sqlitex && rm -f install.sh
```

For an exact Toolset 2.0.1 install, replace `releases/latest/download` with `releases/download/2.0.1` and pass `--release 2.0.1`, for example:

```bash
curl -fsSLO "https://github.com/infocyph/Toolset/releases/download/2.0.1/install.sh" && sudo bash install.sh --release 2.0.1 chromacat && rm -f install.sh
```

The installer defaults to `/usr/local/bin`, so normal installation uses explicit privilege elevation:

```bash
sudo bash install.sh gitx
```

The installer never invokes `sudo` itself. For a deliberate user-local install, override the prefix explicitly:

```bash
bash install.sh --prefix "$HOME/bin" gitx
```

### Exact reproducible release

Pin the suite release and verify the installer itself before running it:

```bash
release="2.0.1"
base="https://github.com/infocyph/Toolset/releases/download/${release}"

curl -fsSLO "${base}/install.sh"
curl -fsSLO "${base}/SHA256SUMS"
grep '  install.sh$' SHA256SUMS | sha256sum -c -

sudo bash install.sh --release "$release" gitx netx
```

The installer also verifies each requested CLI, syntax-checks it, validates its `--version` contract, stages the replacement in the destination directory, and preserves an existing installation as `<tool>.previous`.

### Direct single-file installation

You can install a release asset without the installer:

```bash
release="2.0.1"
tool="gitx"
base="https://github.com/infocyph/Toolset/releases/download/${release}"

curl -fsSLO "${base}/${tool}"
curl -fsSLO "${base}/SHA256SUMS"
grep "  ${tool}$" SHA256SUMS | sha256sum -c -

sudo install -m 0755 "$tool" "/usr/local/bin/$tool"
```

Stable Toolset suite tags use `MAJOR.MINOR` or `MAJOR.MINOR.PATCH`. Toolset 2.0 remains immutable at tag `2.0`; this maintenance release is `2.0.1`.

<!-- TOOLSET2-ROOT-CONTRACT:START -->
## Support, Safety & Automation Contracts

- [CLI dependency/capability, security and output contracts](docs/cli-contracts.md)
- [2.0 security review](docs/security-review.md)

Toolset targets Linux with capability-gated features rather than claiming identical behavior on every distribution. CI smoke-covers Debian 13, Ubuntu 24.04, Fedora 42 and Alpine 3.22 with Bash. High-impact operations remain tool-specific and are documented in each tool README and the suite contract.

Released consumers should pin immutable stable tag `2.0.1` (or another exact release tag) or the tagged commit SHA; published assets are immutable.
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
