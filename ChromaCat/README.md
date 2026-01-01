# chromacat

`chromacat` renders colourful, animated text, banners and ASCII art in your terminal.

Think of it as a **colour-aware `cat`** for:

- rainbow / palette gradients
- scrolling or line-by-line animations
- boxed banners / section headers (with title + padding)
- theme & palette presets
- optional image-to-ANSI support (via `chafa` / `jp2a` / `img2txt`)
- log-friendly highlighting modes (regex + per-line)
- self-update from GitHub
- graceful fallback to plain `cat` when appropriate

When it can’t safely colour (or you didn’t ask for anything special), it behaves like a normal `cat`.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat" \
  -o /usr/local/bin/chromacat && sudo chmod +x /usr/local/bin/chromacat
````

Or keep it in your `$HOME/bin` and add that to `PATH`.

---

## Usage

```bash
echo "Hello" | chromacat [options]
chromacat [options] <file.txt>
tail -f app.log | chromacat --log
```

### Cat fallback behaviour

* If GNU `getopt` is missing (or incompatible), `chromacat` **becomes `cat`** for that invocation.
* If stdout is **not a TTY**, and you did **not** ask for colour/box/match/etc., it auto-falls back to `cat`.
* `--force` overrides the “not a TTY” check and still applies colour.

### Image mode note

When `-I/--image` is used, `chromacat` will **only render the ASCII/ANSI art** produced by the image backend (no extra gradient/box/animation on top). This prevents “double colouring” an ANSI image.

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

    --per-line           One colour per line (faster/log-friendly)
-d, --duration <sec>     Animation seconds (default 1)
-s, --speed <fps>        Frames / second (default 5.0)

-m, --match <regex>      Colour only matching text
    --only-match         Hide non-matching characters (with --match)
    --strip-ansi         Strip existing ANSI codes before colouring

    --log                Preset (no animation + per-line)
    --stream             Disable animations for streaming input
```

#### Details

* `--spread` / `--freq`

    * Control how quickly the gradient cycles across the output.
* `--seed`

    * `0` → random per run
    * non-zero → reproducible gradient
* `-a/--animate` (`classic`)

    * Reprints content repeatedly to create a scrolling/marquee effect.
* `-aa/--line` or `--style line`

    * Reveals lines one by one over the given duration.
* `--per-line`

    * Uses a single gradient colour per line (much faster on large output).
* `--log`

    * Shortcut preset:

        * `animation_style = none`
        * `mode = line` (same idea as `--per-line`)
* `--stream`

    * Forces no animations (still colours) — ideal for `tail -f` or long streams.
* `--match <regex>` + `--only-match`

    * With `--match`: only matching characters are colourised.
    * With `--only-match`: non-matching characters are not printed at all.
* `--strip-ansi`

    * Removes existing `\033[...m` sequences before applying new colour.
    * Useful to re-theme already coloured logs.

Example:

```bash
tail -f app.log | chromacat --log --strip-ansi --match 'ERROR|WARN'
```

---

### Appearance & Layout

```text
-i, --invert             Invert foreground / background
-t, --truecolor          Prefer 24-bit colour if supported
-f, --force              Colour even if stdout not a TTY
    --no-color           Disable colouring (also respects NO_COLOR)

-b, --box                Draw ASCII box
-B, --box-style <name>   default|dashed|dash2|round|double|heavy|parchment|simple|shell|html|plus|comment|php|chain
    --title <text>       Box title line
    --center             Center-align box content
    --pad <n>            Padding inside box (default 0)

-O, --orientation <o>    Gradient orientation: h|v|d
-P, --palette <file>     Palette file (HEX per line)

-T, --theme <name(s)>    Themes (comma list)
    --list-themes        List themes and exit
    --sample-theme <n>   Print theme sample and exit
    --random-theme       Pick random theme

    --blink              Blinking text
```

#### Details

* `--invert`

    * Uses ANSI reverse-video around coloured segments.
* `--truecolor`

    * Enables 24-bit colour **only if** `COLORTERM` contains `truecolor`.
    * Otherwise falls back to 256-colour approximation.
* `--no-color`

    * Hard disables colouring + animations + blink + invert (same effect as `NO_COLOR`).
* `--orientation`

    * Accepts `h`, `v`, `d` (and full words):

        * `horizontal` → `h`
        * `vertical` → `v`
        * `diagonal` → `d`

#### Box rendering (`--box`, `--title`, `--center`, `--pad`)

* `--title` adds a title line inside the box.
* `--center` centers each line inside the box.
* `--pad <n>` adds inner padding:

    * adds blank lines above/below content
    * adds left/right spacing
* Box width is computed using the **longest line across both title and content**, so alignment stays correct.

Example:

```bash
echo "hello" | chromacat -T neon --per-line -b -B round --title "ChromaCat" --center --pad 1
```

#### Palettes & themes

`--palette <file>` expects **one HEX colour per line**:

```text
FF0000
FFA500
FFFF00
00FF00
0000FF
```

Themes can be comma-separated:

```bash
echo "multi" | chromacat -T fire,ice
```

Built-in themes:

* `fire`    – warm oranges/yellows
* `ice`     – cyans/blues
* `sunset`  – reds/oranges/golds
* `ocean`   – cool blues
* `rainbow` – standard rainbow

`--random-theme` picks from the built-ins when no palette/theme was explicitly selected.

> Note: If you use a theme name that isn’t built-in, `chromacat` warns and falls back to rainbow math.

---

### Images & Banners

```text
-I, --image <file>       ASCII-art mode via chafa/jp2a/img2txt
-H, --header <text>      Render header/banner (figlet if available)
```

#### Image mode (`-I/--image`)

* Detects terminal size (capped at 160×60)
* Tries backends in order:

    1. `chafa` (preferred)
    2. `jp2a`
    3. `img2txt`
* Prints the backend’s ANSI output **as-is** (no extra gradient/box/animation)

Examples:

```bash
chromacat -I screenshot.png
chromacat -I logo.jpg
```

#### Header mode (`-H/--header`)

* Ignores stdin/files; renders only the header text.
* Uses `figlet` if available; otherwise plain text.
* You can combine with box + colour + animation:

```bash
chromacat -H "Release v1.0.0" -b --box-style double --center --pad 1
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
chromacat --self-update
CHROMACAT_PATH=/usr/local/bin/chromacat chromacat -U
```

The updater:

1. Downloads from GitHub raw
2. Writes to a temporary file
3. If `sha256sum` is available, compares local vs remote
4. Replaces the target and makes it executable

If it cannot overwrite the target, it suggests `sudo` or setting `CHROMACAT_PATH`.

---

## Environment Variables

CLI flags **always win** over environment defaults.

| Variable              | Description                                                          |
| --------------------- | -------------------------------------------------------------------- |
| `CHROMACAT_THEME`     | Default theme(s), comma-separated (e.g. `fire,ocean`)                |
| `CHROMACAT_BOX_STYLE` | Default box style (same values as `--box-style`)                     |
| `CHROMACAT_STYLE`     | Default animation style (`classic`, `line`, `none`)                  |
| `CHROMACAT_PATH`      | Target path for `--self-update`                                      |
| `NO_COLOR`            | If set, disables colour/animations/blink/invert/truecolor (hard-off) |

Example:

```bash
export CHROMACAT_THEME=fire,sunset
export CHROMACAT_BOX_STYLE=double
export CHROMACAT_STYLE=none
```

---

## Behaviour Notes

### Truecolor detection

`--truecolor` uses 24-bit colour only when:

```bash
COLORTERM contains "truecolor"
```

Otherwise it uses 256-colour approximations.

### Non-TTY handling & force

If stdout is not a TTY and `--force` is not used:

* animations are disabled
* box rendering is disabled
* truecolor is disabled
* if no other color features were requested, it behaves like `cat`

Use `--force` to keep coloring in pipelines.

---

## Examples

### 1) Simple rainbow

```bash
echo "hello" | chromacat
```

### 2) Scrolling animation

```bash
echo "hello" | chromacat -a -d 2
```

### 3) Boxed + titled + padded + centered

```bash
echo "hello" | chromacat -T neon --per-line -b -B round --title "ChromaCat" --center --pad 1
```

### 4) Parchment banner with diagonal reveal

```bash
figlet "Docker" | chromacat -b -B parchment --title "Containers" -aa -d 6 -O d
```

### 5) Log highlighting (preset + regex)

```bash
tail -f app.log | chromacat --log --strip-ansi --match 'ERROR|WARN'
```

### 6) Match-only mode

```bash
echo "status=OK code=200" | chromacat -m 'OK|200' --only-match
```

### 7) Per-line gradient for big output

```bash
kubectl get pods -A | chromacat --per-line -T ocean
```

### 8) Image to ANSI (no extra gradient)

```bash
chromacat -I screenshot.png
```

### 9) Theme exploration

```bash
chromacat --list-themes
chromacat --sample-theme fire
echo "Ocean vibes" | chromacat --random-theme
```

### 10) Self-update

```bash
sudo chromacat --self-update
```

Drop it into your pipelines in place of `cat` whenever you want logs and banners to actually be *visible* instead of grey noise.
