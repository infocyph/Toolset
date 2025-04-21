# Toolset

Welcome to **Toolset**, a versatile set of scripts designed to streamline your Linux-based development environment management tasks. This repository provides four key utilities:

- **dockex**: Docker container management
- **phpx**: PHP version and extension management
- **gitx**: Git workflow and repository management
- **chromacat**: Colourful animated text printing

---

## Table of Contents
- [Installation](#installation)
- [dockex](#dockex)
- [phpx](#phpx)
- [gitx](#gitx)
- [chromacat](#chromacat)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

Install each script individually:

**dockex:**
```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Docker/dockex" -o /usr/local/bin/dockex && sudo chmod +x /usr/local/bin/dockex
```

**phpx:**
```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/PHP/phpx" -o /usr/local/bin/phpx && sudo chmod +x /usr/local/bin/phpx
```

**gitx:**
```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Git/gitx" -o /usr/local/bin/gitx && sudo chmod +x /usr/local/bin/gitx
```

**chromacat:**
```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat" -o /usr/local/bin/chromacat && sudo chmod +x /usr/local/bin/chromacat
```

---

## dockex

`dockex` simplifies Docker operations, including container management, resource monitoring, benchmarking, and backups.

### Key Features:
- Container management (start, stop, restart)
- Detailed container stats and logs
- Apache Benchmark for stress tests
- Dynamic resource updates
- Backup and restore data
- Cleanup operations

### Usage:
```bash
dockex <command> [container_name] [options]
```

#### Example Commands:
```bash
dockex my_container info
dockex my_container logs 50
dockex my_container benchmark 5
dockex create nginx my_container
```

---

## phpx

`phpx` manages PHP versions, extensions, and configuration for multiple web servers.

### Key Features:
- PHP version switching
- Extension management
- Built-in PHP development server
- Composer and PECL package installation
- PHP version cleanup and extension management
- Self-update capability

### Usage:
```bash
phpx {switch|ext|install|serve|run|remove|sury|clean|self-update} <arguments>
```

#### Example Commands:
```bash
phpx switch 8.2
phpx ext
phpx install composer
phpx install xdebug,redis
phpx serve --host=192.168.0.1 --port=8080
phpx remove 8.1
phpx self-update
```

---

## gitx

`gitx` simplifies Git operations, streamlining repository and workflow management.

### Key Features:
- Branch creation, merging, syncing
- Commit operations and amendments
- Stash management
- Branch comparisons and reporting
- Cleanup and optimization
- Tagging and configuration management

### Usage:
```bash
gitx <command> [options]
```

#### Example Commands:
```bash
gitx status
gitx sync
gitx create feature new-login
gitx merge feature/new-login main
gitx diff changes.txt
gitx report abc123 HEAD output.txt
gitx cleanup
gitx tag v1.0.0
```

---

## chromacat

`chromacat` provides colourful animated text output for terminals, supporting ASCII art, animations, boxes and various themes.

### Key Features:
- Colourful animated text (classic scrolling `-a` or line‑by‑line reveal `-aa`)
- Six ASCII‑box styles (`default`, `parchment`, `simple`, `shell`, `html`, `plus`) + comment‑style (`comment`) and PHP‑tag (`php`) frames via `-B`
- Rainbow, themed (`--theme`) or custom‑palette (`-P <file>`) gradients
- Gradient orientation control (`-O h|v|d`) and seedable randomness
- True‑colour (24‑bit) and 8‑bit fallback with `--truecolor` / auto‑detect
- ASCII‑image import via `-I <image>` (uses `img2txt`)
- Force colour on pipes (`-f`), invert colours (`-i`), customise spread / freq

### Usage:
```bash
chromacat [OPTIONS] [FILE]...
```

### Common Options (subset):
```
-a | --animate              classic scrolling animation
-aa| --line                 line-by-line reveal animation
-d  | --duration <sec>      total animation time
-s  | --speed <fps>         frames/second (classic) or lines/second (line)
-b  | --box                 enable box; style picked with -B
-B  | --box-style <name>    default|parchment|simple|shell|html|plus|comment|php
-O  | --orientation <o>     gradient flow: h (horizontal), v (vertical), d (diagonal)
-P  | --palette <file>      custom HEX palette, one per line
-T  | --theme <name>        fire|ice|sunset|ocean|rainbow
-i  | --invert              reverse foreground/background
-t  | --truecolor           force 24‑bit colour
-f  | --force               colour even when stdout is not a TTY
```

#### Example Commands:
```bash
echo "hello" | chromacat -a -d 2                          # rainbow scroll
figlet "Docker" | chromacat -b -B parchment -aa -d 6 -O d # parchment box, diagonal reveal
echo "hello" | chromacat --theme ocean --animate          # themed colours
figlet "Code" | chromacat -b -B php -O h                  # PHP‑tag box
figlet "Logs" | chromacat -b -B plus -P palette.txt       # custom palette with plus box
```

---

## Contributing

We welcome contributions! Submit issues or pull requests to help improve **Toolset**.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

