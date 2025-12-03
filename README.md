# Toolset

A collection of small, focused, shell-based CLIs to streamline day-to-day development and ops on Linux.

All tools are standalone Bash scripts and can be installed with a single `curl + chmod`.

## Tools at a Glance

| Tool        | Area             | Quick Summary                                                                 | Docs                             |
|-------------|------------------|-------------------------------------------------------------------------------|----------------------------------|
| `dockex`    | Docker           | Inspect, benchmark, backup/restore and clean Docker resources                | [Docker](Docker/README.md)       |
| `phpx`      | PHP              | PHP version / extension manager, FPM/webserver config, doctor & tuner        | [PHP](PHP/README.md)             |
| `gitx`      | Git              | Opinionated Git workflow, cleanup, summaries & changelog helper              | [Git](Git/README.md)             |
| `chromacat` | Terminal output  | Colourful / animated text, banners & ASCII art with themes and palettes      | [ChromaCat](ChromaCat/README.md) |
| `sqlitex`   | SQLite           | Non-interactive, flag-driven SQLite admin, migrations, seeds & tuning        | [Sqlite](Sqlite/README.md)       |
| `cleanx`    | Cleanup & Inodes | Safe, modular disk & inode cleaner; **dry-run by default**, quota/JSON/update | [Clean](Clean/README.md)         |

### Tool Documentation

- **dockex** – Docker helper: [Docker](Docker/README.md)  
- **phpx** – PHP manager / doctor: [PHP](PHP/README.md)  
- **gitx** – Git workflow helper: [Git](Git/README.md)  
- **chromacat** – colourful terminal text: [ChromaCat](ChromaCat/README.md)  
- **sqlitex** – SQLite CLI: [Sqlite](Sqlite/README.md)  
- **cleanx** – disk & inode cleaner: [Clean](Clean/README.md)

---

## Installation

Each tool lives in its own directory. Install only what you need:

```bash
# dockex – Docker helper
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Docker/dockex" \
  -o /usr/local/bin/dockex && sudo chmod +x /usr/local/bin/dockex
````

```bash
# phpx – PHP manager
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/PHP/phpx" \
  -o /usr/local/bin/phpx && sudo chmod +x /usr/local/bin/phpx
```

```bash
# gitx – Git workflow helper
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Git/gitx" \
  -o /usr/local/bin/gitx && sudo chmod +x /usr/local/bin/gitx
```

```bash
# chromacat – colourful terminal text / banners
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat" \
  -o /usr/local/bin/chromacat && sudo chmod +x /usr/local/bin/chromacat
```

```bash
# sqlitex – SQLite CLI (CRUD, migrations, seeds, tuning)
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Sqlite/sqlitex" \
  -o /usr/local/bin/sqlitex && sudo chmod +x /usr/local/bin/sqlitex
```

```bash
# cleanx – disk & inode cleaner (dry-run by default; use --yes to apply)
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Clean/cleanx" \
  -o /usr/local/bin/cleanx && sudo chmod +x /usr/local/bin/cleanx
```

See each tool’s README (linked above) for full command reference and examples.

---

## Contributing

Bug fixes, small UX improvements, new subcommands or better docs are all welcome.
Open an issue or PR against this repo.

---

## License

Licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
