# Toolset

A collection of small, focused, shell-based CLIs to streamline day-to-day development and ops on Linux.

All tools are standalone bash scripts and can be installed with a single `curl + chmod`.

## Tools at a Glance

| Tool        | Area            | Quick Summary                                                 | Docs                             |
|-------------|-----------------|---------------------------------------------------------------|----------------------------------|
| `dockex`    | Docker          | Inspect, benchmark, backup/restore and clean Docker resources | [Docker](Docker/README.md)       |
| `phpx`      | PHP             | PHP version/extension manager, FPM/webserver config, doctor   | [PHP](PHP/README.md)             |
| `gitx`      | Git             | Opinionated Git workflow, reporting & cleanup helper          | [Git](Git/README.md)             |
| `chromacat` | Terminal output | Colourful / animated text & ASCII art in the terminal         | [ChromaCat](ChromaCat/README.md) |
| `sqlitex`   | SQLite          | Non-interactive, flag-driven SQLite admin & migrations        | [Sqlite](Sqlite/README.md)       |

### Tool Documentation

- **dockex** – Docker helper: [Docker](Docker/README.md)
- **phpx** – PHP manager / doctor: [PHP](PHP/README.md)
- **gitx** – Git workflow helper: [Git](Git/README.md)
- **chromacat** – colourful terminal text: [ChromaCat](ChromaCat/README.md)
- **sqlitex** – SQLite CLI: [Sqlite](Sqlite/README.md)

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
# chromacat – colourful terminal text
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat" \
  -o /usr/local/bin/chromacat && sudo chmod +x /usr/local/bin/chromacat
```

```bash
# sqlitex – SQLite CLI
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Sqlite/sqlitex" \
  -o /usr/local/bin/sqlitex && sudo chmod +x /usr/local/bin/sqlitex
```

See each tool’s README (linked above) for full command reference and examples.

---

## Contributing

Bug fixes, small UX improvements, new subcommands or better docs are all welcome.
Feel free to open an issue or PR against this repo.

## License

Licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
