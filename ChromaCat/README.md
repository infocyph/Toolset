# chromacat

`chromacat` renders colourful, animated text, banners and ASCII art in your terminal.

It’s designed to be a drop-in replacement for `cat` in pipelines, adding:

- rainbow gradients
- animation (scrolling / line-by-line)
- box frames
- palette/themes
- optional image-to-ANSI support (when `chafa`/similar tools are installed)

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/ChromaCat/chromacat" \
  -o /usr/local/bin/chromacat && sudo chmod +x /usr/local/bin/chromacat
````

## Usage

```bash
echo "Hello" | chromacat [options]
chromacat [options] < file.txt
```

## Options

| Option                        | Purpose                                            |
|-------------------------------|----------------------------------------------------|
| `-p, --spread <f>`            | Rainbow spread factor                              |
| `-F, --freq <f>`              | Rainbow frequency                                  |
| `-S, --seed <n>`              | PRNG seed (0 = random)                             |
| `-a, --animate`               | Classic scrolling animation                        |
| `-aa, --line`                 | Line-by-line reveal animation                      |
| `-d, --duration <s>`          | Animation duration (seconds)                       |
| `-s, --speed <fps>`           | Frames-per-second (or lines/sec)                   |
| `-i, --invert`                | Invert foreground/background                       |
| `-t, --truecolor`             | Force 24-bit colour                                |
| `-f, --force`                 | Force colour even if not a TTY                     |
| `-b, --box`                   | Draw ASCII box around content                      |
| `-B, --box-style <name>`      | Box style (e.g. `default`, `parchment`, `simple`)  |
| `-O, --orientation <h\|v\|d>` | Gradient orientation: horizontal/vertical/diagonal |
| `-P, --palette <file>`        | Custom HEX palette file                            |
| `-T, --theme <name>`          | Predefined themes (e.g. `fire`, `ice`, `sunset`)   |
| `-I, --image <file>`          | Render image as ASCII/ANSI art                     |
| `--blink`                     | Blinking text                                      |
| `--image-opacity <0–100>`     | ASCII image brightness / opacity                   |
| `-v, --version`               | Print version                                      |
| `-h, --help`                  | Show help                                          |

## Examples

```bash
# Rainbow scroll "hello" over 2 seconds
echo "hello" | chromacat -a -d 2

# Boxed diagonal reveal with a parchment-style frame
figlet "Docker" | chromacat -b -B parchment -aa -O d

# Render screenshot.png as ANSI art at 80% opacity (requires image backend)
chromacat -T ocean --image screenshot.png --image-opacity 80

# Use a fixed seed so colours are reproducible
echo "Consistent colours" | chromacat -S 42
```
