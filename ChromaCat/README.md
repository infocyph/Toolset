# chromacat

`chromacat` renders colourful, animated text, banners and ASCII art in your terminal.

Think of it as a **colour-aware `cat`** for:

- rainbow / palette gradients
- scrolling or line-by-line animations
- boxed banners / section headers
- theme & palette presets
- optional image-to-ANSI support (via `chafa` / `jp2a` / `img2txt`)
- log-friendly highlighting modes
- self-update from GitHub

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat" \
  -o /usr/local/bin/chromacat && sudo chmod +x /usr/local/bin/chromacat
````

Or keep it in your `$HOME/bin` and add to `PATH`.

---

## Usage

```bash
echo "Hello" | chromacat [options]
chromacat [options] <file.txt
tail -f app.log | chromacat --log
```

When `-I/--image` is used, `chromacat` will **only render the ASCII/ANSI art** as produced by the image backend (no
extra gradient on top).

---

## CLI Options

### Colour & Animation

| Option                 | Description                                                      |
|------------------------|------------------------------------------------------------------|
| `-p, --spread <f>`     | Rainbow spread factor (gradient smoothness)                      |
| `-F, --freq <f>`       | Rainbow frequency (colour cycle density)                         |
| `-S, --seed <n>`       | PRNG seed (0 = random per run)                                   |
| `-a, --animate`        | Classic scrolling animation (full buffer scrolls)                |
| `-aa, --line`          | Line-by-line reveal animation                                    |
| `--style <name>`       | Animation style: `classic`                                       | `line` | `none`                     |
| `--per-line`           | One colour per line (faster, log-friendly; works with all modes) |
| `-d, --duration <sec>` | Animation duration in seconds                                    |
| `-s, --speed <fps>`    | Frames per second (for animations)                               |
| `-m, --match <regex>`  | Only colour characters that match the regex                      |
| `--only-match`         | When combined with `--match`, hide non-matching characters       |
| `--strip-ansi`         | Strip existing ANSI escape codes before colouring                |
| `--log`                | Log preset: no animation, `--per-line` enabled                   |
| `--stream`             | Disable animations (safe for infinite streams like `tail -f`)    |

> Tip: For logs, `chromacat --log --match 'ERROR|WARN'` is usually the sweet spot.

---

### Appearance & Layout

| Option                   | Description                                                                                                                                    |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `-i, --invert`           | Invert foreground/background (ANSI reverse video)                                                                                              |
| `-t, --truecolor`        | Force 24-bit colour (requires truecolor-capable terminal)                                                                                      |
| `-f, --force`            | Force colour even if stdout is not a TTY                                                                                                       |
| `-b, --box`              | Draw an ASCII box around content                                                                                                               |
| `-B, --box-style <name>` | Box style: `default`, `dashed`, `dash2`, `round`, `double`, `heavy`, `parchment`, `simple`, `shell`, `html`, `plus`, `comment`, `php`, `chain` |
| `--title <text>`         | Box title line (printed at top inside the box)                                                                                                 |
| `--center`               | Center-align box content (and title)                                                                                                           |
| `-O, --orientation <o>`  | Gradient orientation: `h`(orizontal)                                                                                                           | `v`(ertical) | `d`(iagonal)                                                                             |
| `-P, --palette <file>`   | Custom palette file (one HEX colour per line, e.g. `FF0000`)                                                                                   |
| `-T, --theme <name>`     | Theme (comma-separated list): `fire`, `ice`, `sunset`, `ocean`, `rainbow`                                                                      |
| `--list-themes`          | Print available themes and exit                                                                                                                |
| `--sample-theme <name>`  | Render a short preview of the theme and exit                                                                                                   |
| `--random-theme`         | Pick a random theme if no theme/palette was explicitly set                                                                                     |
| `--blink`                | Blinking text (ANSI blink attribute)                                                                                                           |

---

### Images & Banners

| Option                | Description                                                          |
|-----------------------|----------------------------------------------------------------------|
| `-I, --image <file>`  | Render image as ANSI/ASCII art via `chafa`                           | `jp2a` | `img2txt`      |
| `-H, --header <text>` | Render a header/banner (uses `figlet` if available, otherwise plain) |

**Image behaviour**

* If `-I/--image` is given, `chromacat`:

    * Detects terminal size
    * Uses `chafa`, or falls back to `jp2a` or `img2txt`
    * Prints **their ANSI output as-is** (no additional gradient/box/animation)

**Header behaviour**

* `-H/--header` ignores stdin/files and:

    * Runs `figlet "text"` if available (else plain text)
    * Optional `--box`/`--box-style`/`--title`/`--center` are applied
    * Then gradient/animation is applied like normal text

---

### Maintenance & Meta

| Option              | Description                                                            |
|---------------------|------------------------------------------------------------------------|
| `-U, --self-update` | Download latest `chromacat` from GitHub and replace the current script |
| `-v, --version`     | Print version and exit                                                 |
| `-h, --help`        | Show help and exit                                                     |

**Self-update**

```bash
# Default: update whatever "chromacat" resolves to in PATH
chromacat --self-update

# Override target path explicitly
CHROMACAT_PATH=/usr/local/bin/chromacat chromacat -U
```

It:

* downloads from
  `https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat`
* creates a backup `chromacat.bak-YYYYMMDDHHMMSS`
* makes the new script executable

If it can’t overwrite the target, it will tell you (use `sudo` or adjust `CHROMACAT_PATH`).

---

## Environment Variables

These are **optional**; CLI flags always win.

| Variable              | Description                                           |
|-----------------------|-------------------------------------------------------|
| `CHROMACAT_THEME`     | Default theme(s), comma-separated (e.g. `fire,ocean`) |
| `CHROMACAT_BOX_STYLE` | Default box style (same values as `--box-style`)      |
| `CHROMACAT_STYLE`     | Default animation style (`classic`                    | `line` | `none`) |
| `CHROMACAT_PATH`      | Target path for `--self-update`                       |
| `NO_COLOR`            | If set, disables colour, animations and blink         |

Example:

```bash
export CHROMACAT_THEME=fire,sunset
export CHROMACAT_BOX_STYLE=double
export CHROMACAT_STYLE=none
```

---

## Examples

### 1. Simple rainbow scroll

```bash
echo "hello" | chromacat -a -d 2
```

### 2. Parchment banner with diagonal reveal

```bash
figlet "Docker" | chromacat -b -B parchment --title "Containers" -aa -O d
```

### 3. Log highlighting (recommended)

```bash
tail -f app.log \
  | chromacat --log --strip-ansi --match 'ERROR|WARN'
```

### 4. Match-only mode

```bash
echo "status=OK code=200" \
  | chromacat -m 'OK|200' --only-match
```

### 5. Per-line gradient for big output

```bash
kubectl get pods -A \
  | chromacat --per-line -T ocean
```

### 6. Image to ANSI (no extra gradient)

```bash
chromacat -I screenshot.png
```

Backend priority: `chafa` → `jp2a` → `img2txt`.

### 7. Header with centered box

```bash
chromacat -H "Release v1.0.0" -b --box-style double --center
```

### 8. Fixed seed (reproducible colours)

```bash
echo "Consistent colours" | chromacat -S 42 -T sunset
```

### 9. Self-update

```bash
sudo chromacat --self-update
```
