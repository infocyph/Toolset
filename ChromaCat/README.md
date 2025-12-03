# chromacat

`chromacat` renders colourful, animated text, banners and ASCII art in your terminal.

Think of it as a **colour-aware `cat`** for:

* rainbow / palette gradients
* scrolling or line-by-line animations
* boxed banners / section headers
* theme & palette presets
* optional image-to-ANSI support (via `chafa` / `jp2a` / `img2txt`)
* log-friendly highlighting modes
* self-update from GitHub
* graceful fallback to plain `cat` when appropriate

When it can’t safely colour (or you didn’t ask for anything special), it behaves like a normal `cat`.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat" \
  -o /usr/local/bin/chromacat && sudo chmod +x /usr/local/bin/chromacat
```

Or keep it in your `$HOME/bin` and add that to `PATH`.

---

## Usage

```bash
echo "Hello" | chromacat [options]
chromacat [options] <file.txt>
tail -f app.log | chromacat --log
```

**Cat fallback behaviour**

* If `getopt` is missing, `chromacat` **becomes `cat`** for that invocation.
* If stdout is **not a TTY**, and you did **not** ask for colour/box/match/etc., it auto-falls back to `cat` as well.
* `--force` can override the “not a TTY” check and still apply colour.

When `-I/--image` is used, `chromacat` will **only render the ASCII/ANSI art** as produced by the image backend (no extra gradient on top).

---

## CLI Options

### Colour & Animation

```text
-p, --spread <f>         Rainbow spread (default 3.0)
-F, --freq <f>           Rainbow frequency (default 0.1)
-S, --seed <n>           Seed (0 = random)
-a, --animate            Classic scrolling animation
-aa, --line              Line-by-line reveal animation
    --style <name>       Animation style (classic|line|none)
    --per-line           Use one colour per line (faster, log-friendly)
-d, --duration <sec>     Animation seconds (default 1)
-s, --speed <fps>        Frames / second (default 5.0)
-m, --match <regex>      Colour only text matching regex
    --only-match         Hide non-matching characters (with --match)
    --strip-ansi         Strip existing ANSI codes before colouring
    --log                Log preset (no animation, per-line gradient)
    --stream             Disable animations for streaming input
```

**Details**

* `--spread` / `--freq`:

    * control how fast/slow the rainbow cycles across characters/lines.
* `--seed`:

    * `0` → uses a random seed per run.
    * non-zero → reproducible gradients for the same content.
* `-a/--animate` (`classic`):

    * repeatedly reprints the content and scrolls it like a marquee.
* `-aa/--line` or `--style line`:

    * reveals lines one by one over the given duration.
* `--per-line`:

    * switches mode to **line-level colour**:

        * each line gets one gradient colour,
        * better for big outputs and logs.
* `--log` preset:

    * `animation_style = none`
    * `mode = line` (as if `--per-line`).
* `--stream`:

    * disables animations (but still colours) – useful for infinite streams (`tail -f`, long-running CLIs).
* `--match <regex>` / `--only-match`:

    * if `--match` is set:

        * only matching characters are colourised.
        * non-matching characters stay plain.
    * if you also use `--only-match`:

        * non-matching characters are **not printed at all**.
* `--strip-ansi`:

    * removes existing `\033[...m` sequences before applying new colour.
    * good for re-theming already coloured logs.

> For logs, something like:
>
> ```bash
> tail -f app.log | chromacat --log --strip-ansi --match 'ERROR|WARN'
> ```

---

### Appearance & Layout

```text
-i, --invert             Invert foreground / background
-t, --truecolor          Force 24-bit colour
-f, --force              Colour even if stdout not a TTY
-b, --box                Draw ASCII box
-B, --box-style <name>   Box style: default|dashed|dash2|round|double|heavy|parchment|simple|shell|html|plus|comment|php|chain
    --title <text>       Box title line
    --center             Center-align box content
-O, --orientation <o>    Gradient orientation: h|v|d
-P, --palette <file>     Palette file (HEX per line)
-T, --theme <name>       fire|ice|sunset|ocean|rainbow (comma-separated list)
    --list-themes        Show available themes and exit
    --sample-theme <n>   Preview theme and exit
    --random-theme       Pick a random theme
    --blink              Blinking text
```

**Details**

* `--invert`:

    * uses ANSI reverse video around coloured segments.

* `--truecolor`:

    * forces 24-bit RGB sequences, but only if `COLORTERM` contains `truecolor`.

* `--orientation`:

    * accepts `h`, `v`, `d` and also the full words:

        * `horizontal` → `h`
        * `vertical` → `v`
        * `diagonal` → `d`

* `--palette <file>`:

    * file with one hex colour per line, e.g.:

      ```text
      FF0000
      FFA500
      FFFF00
      ```

* `--theme`:

    * supports multiple themes in one go:

      ```bash
      chromacat -T fire,ice
      ```

    * built-in themes:

        * `fire`    – warm oranges/yellows
        * `ice`     – cyans/blues
        * `sunset`  – reds/oranges/golds
        * `ocean`   – cool blues
        * `rainbow` – standard rainbow

* `--list-themes`:

    * prints the built-in theme list and exits.

* `--sample-theme <name>`:

    * prints a small “Sample for theme "<name>"” line using that theme and exits.

* `--random-theme`:

    * when no theme/palette specified:

        * picks randomly from `fire`, `ice`, `sunset`, `ocean`, `rainbow`.

* `--blink`:

    * wraps coloured characters with ANSI blink **on/off** codes.
    * obeys `NO_COLOR` (disabled if `NO_COLOR` is set).

---

### Images & Banners

```text
-I, --image <file>       ASCII-art mode via chafa/jp2a/img2txt
-H, --header <text>      Render header/banner (figlet if available)
```

#### Image mode (`-I/--image`)

Behaviour:

* Detects terminal size (capped at 160x60).

* Tries, in order:

    1. `chafa` (preferred)
    2. `jp2a`
    3. `img2txt`

* Prints the backend’s **ANSI output as-is**:

    * **No additional gradient**, box or animation applied.
    * This ensures the image renderer controls the colours.

Examples:

```bash
chromacat -I screenshot.png
chromacat -I logo.jpg
```

#### Header mode (`-H/--header`)

Behaviour:

* Ignores stdin/files; operates only on the header text.

* If `figlet` is installed:

  ```bash
  figlet "text"
  ```

  is used; otherwise plain text.

* If `--box` / `--box-style` / `--title` / `--center` are provided:

    * the figlet/plain output is first boxed via the internal box renderer.

* After that, the result goes through:

    * `classic` / `line` animation, or
    * static `colour_block` (default).

Example:

```bash
chromacat -H "Release v1.0.0" -b --box-style double --center
```

---

### Maintenance & Meta

```text
-U, --self-update        Fetch latest chromacat and replace current script
-v, --version            Print version and exit
-h, --help               Show this help
```

#### Self-update

```bash
# Default: update resolved "chromacat" binary
chromacat --self-update

# Explicit target
CHROMACAT_PATH=/usr/local/bin/chromacat chromacat -U
```

The updater:

1. Downloads from
   `https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat`
2. Writes to a temporary file.
3. If `sha256sum` is available:

    * compares remote vs local hash.
    * if identical → “already up-to-date”.
4. Moves the new script into place and makes it executable.

If it cannot overwrite the target, it will tell you to use `sudo` or set `CHROMACAT_PATH`.

---

## Environment Variables

CLI flags **always win** over environment defaults.

| Variable              | Description                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------ |
| `CHROMACAT_THEME`     | Default theme(s), comma-separated (e.g. `fire,ocean`)                                      |
| `CHROMACAT_BOX_STYLE` | Default box style (same values as `--box-style`)                                           |
| `CHROMACAT_STYLE`     | Default animation style (`classic`, `line`, `none`)                                        |
| `CHROMACAT_PATH`      | Target path for `--self-update`                                                            |
| `NO_COLOR`            | If set (to anything), disables colour, animations, blink, invert and truecolor logic fully |

Example:

```bash
export CHROMACAT_THEME=fire,sunset
export CHROMACAT_BOX_STYLE=double
export CHROMACAT_STYLE=none
```

With `NO_COLOR` set, `chromacat` becomes essentially a smarter `cat`/box drawer with **no** ANSI sequences emitted.

---

## Behaviour Notes

### Truecolor detection

* `-t/--truecolor` only enables 24-bit colour if:

  ```bash
  COLORTERM contains "truecolor"
  ```

* Otherwise, it falls back to 256-colour approximation.

### Non-TTY handling & force

* If stdout is not a TTY **and** `--force` is not used:

    * Animations are disabled.
    * Box is disabled.
    * Truecolor is disabled.
    * If no other colouring features are used, it **behaves exactly like `cat`**.

* `--force` keeps colouring even when piping to files or through other programs.

---

## Examples

### 1. Simple rainbow scroll

```bash
echo "hello" | chromacat -a -d 2
```

### 2. Parchment banner with diagonal reveal

```bash
figlet "Docker" | chromacat -b -B parchment --title "Containers" -aa -d 6 -O d
```

### 3. Log highlighting (preset + regex)

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

### 9. Theme exploration

```bash
chromacat --list-themes
chromacat --sample-theme fire
echo "Ocean vibes" | chromacat --random-theme
```

### 10. Self-update

```bash
sudo chromacat --self-update
```

Drop it into your pipelines in place of `cat` whenever you want logs and banners to actually be *visible* instead of grey noise.
