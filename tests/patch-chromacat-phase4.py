#!/usr/bin/env python3
from pathlib import Path

path = Path("ChromaCat/chromacat")
text = path.read_text()


def replace_once(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"missing transform anchor: {label}")
    text = text.replace(old, new, 1)


replace_once(
    'do_self_update=false\nno_color=false\n',
    'do_self_update=false\nno_color=false\ncat_mode=false\n',
    'defaults',
)

replace_once(
    'MISC\n  -H, --header <text>      Render banner (figlet if available)\n  -U, --self-update        Fetch latest chromacat and replace current script\n',
    'MISC\n      --cat                Raw byte-for-byte passthrough; disables presentation processing\n  -H, --header <text>      Render banner (figlet if available)\n  -U, --self-update        Fetch latest chromacat and replace current script\n',
    'usage cat option',
)

replace_once(
    '  -v|--version) printf \'%s %s\\n\' "$(basename "$0")" "$VERSION"; exit 0 ;;\n  -h|--help) usage; exit 0 ;;\n\n  -U|--self-update) do_self_update=true; shift ;;\n',
    '  -v|--version) printf \'%s %s\\n\' "$(basename "$0")" "$VERSION"; exit 0 ;;\n  -h|--help) usage; exit 0 ;;\n  --cat) cat_mode=true; shift ;;\n\n  -U|--self-update) do_self_update=true; shift ;;\n',
    'parse cat option',
)

replace_once(
    '  -*)\n  # unknown flag: behave like cat for maximum safety\n    exec cat "${ORIG_ARGS[@]}"\n    ;;\n',
    '  -*) die "Unknown option: $1" ;;\n',
    'unknown option',
)

replace_once(
    'while [[ $# -gt 0 ]]; do files+=("$1"); shift; done\n\n# ------------------ self-update early exit -----------------------\n',
    'while [[ $# -gt 0 ]]; do files+=("$1"); shift; done\n\n# Resolve stdin before any fast path. `--cat` is intentionally raw and takes\n# precedence over all presentation options so it can serve as an explicit\n# byte-for-byte escape hatch.\n[[ ${#files[@]} -eq 0 ]] && files=("-")\nif [[ $cat_mode == true ]]; then\n  exec cat -- "${files[@]}"\nfi\n\n# ------------------ self-update early exit -----------------------\n',
    'early raw path',
)

old_sanity = '''# -------------- environment / sanity checks -----------------------
if [[ -n ${NO_COLOR:-} ]]; then no_color=true; fi

truecolor=false
if [[ $want_truecolor == true && ( ${COLORTERM:-} == *truecolor* || ${COLORTERM:-} == *24bit* ) ]]; then
  truecolor=true
fi

# If stdout is not tty and not forced -> prefer plain cat unless explicit features requested.
if [[ ! -t 1 && $force == false ]]; then
  animation_style=none
  truecolor=false
fi

for v in spread freq duration speed; do
  [[ ${!v} =~ ^[0-9]+(\\.[0-9]+)?$ ]] || die "Invalid $v"
done
[[ $box_pad =~ ^[0-9]+$ ]] || die "Invalid --pad"
[[ $image_opacity =~ ^[0-9]+$ ]] || die "Invalid --image-opacity"
'''
new_sanity = '''# -------------- environment / sanity checks -----------------------
if [[ -n ${NO_COLOR:-} ]]; then no_color=true; fi

# Colour is an enhancement. Non-TTY output stays unstyled unless --force was
# explicitly requested; --no-color/NO_COLOR always wins.
color_enabled=true
if [[ $no_color == true || ( ! -t 1 && $force == false ) ]]; then
  color_enabled=false
fi

truecolor=false
if [[ $color_enabled == true && $want_truecolor == true && ( ${COLORTERM:-} == *truecolor* || ${COLORTERM:-} == *24bit* ) ]]; then
  truecolor=true
fi

for v in spread freq duration speed; do
  [[ ${!v} =~ ^[0-9]+(\\.[0-9]+)?$ ]] || die "Invalid $v"
done
[[ $seed =~ ^[0-9]+$ ]] || die "Invalid seed"
[[ $box_pad =~ ^[0-9]+$ ]] || die "Invalid --pad"
[[ $image_opacity =~ ^[0-9]+$ ]] || die "Invalid --image-opacity"
(( image_opacity <= 100 )) || die "Invalid --image-opacity"

num_gt_zero() { "$AWK" -v n="$1" 'BEGIN { exit !(n > 0) }'; }
num_ge_zero() { "$AWK" -v n="$1" 'BEGIN { exit !(n >= 0) }'; }
num_gt_zero "$spread" || die "Invalid spread: must be > 0"
num_ge_zero "$freq" || die "Invalid freq: must be >= 0"
num_ge_zero "$duration" || die "Invalid duration: must be >= 0"
num_gt_zero "$speed" || die "Invalid speed: must be > 0"

case $animation_style in
classic|line|none) ;;
*) die "Invalid animation style: $animation_style" ;;
esac

case $orientation in
horizontal) orientation="h" ;;
vertical) orientation="v" ;;
diagonal) orientation="d" ;;
h|v|d) ;;
*) die "Invalid orientation: $orientation" ;;
esac

if [[ $only_match == true && -z $match_regex ]]; then
  die "--only-match requires --match"
fi
'''
replace_once(old_sanity, new_sanity, 'sanity validation')

replace_once(
    '    *) echo "Unknown theme: $theme" >&2 ;;\n',
    '    *) die "Unknown theme: $theme" ;;\n',
    'theme validation',
)

replace_once(
    '''case $orientation in
horizontal) orientation="h";;
vertical)   orientation="v";;
diagonal)   orientation="d";;
esac

# ---------------------- colouriser (portable AWK) -----------------
''',
    '''# ---------------------- plain/colour rendering -----------------
strip_sgr_stream() {
  "$AWK" '{ gsub(/\\033\\[[0-9;]*m/, ""); print; fflush() }'
}

plain_block() {
  "$AWK" -v color_enabled="$color_enabled" -v strip_ansi="$strip_ansi" \\
    -v match_regex="$match_regex" -v only_match="$only_match" '
  {
    line=$0
    if (color_enabled != "true" || strip_ansi == "true") {
      gsub(/\\033\\[[0-9;]*m/, "", line)
    }

    if (only_match == "true" && match_regex != "") {
      out=""
      start=1
      while (start <= length(line)) {
        rel=match(substr(line, start), match_regex)
        if (rel == 0) break
        pos=rel + start - 1
        if (RLENGTH <= 0) {
          start=pos + 1
          continue
        }
        out=out substr(line, pos, RLENGTH)
        start=pos + RLENGTH
      }
      print out
    } else {
      print line
    }
    fflush()
  }'
}

# ---------------------- colouriser (portable AWK) -----------------
''',
    'plain renderer helpers',
)

replace_once(
    '''        m = m + start - 1;
        e = m + RLENGTH - 1;
        for (k = m; k <= e; k++) in_match[k] = 1;
        start = e + 1;
''',
    '''        m = m + start - 1;
        if (RLENGTH <= 0) {
          start = m + 1;
          continue;
        }
        e = m + RLENGTH - 1;
        for (k = m; k <= e; k++) in_match[k] = 1;
        start = e + 1;
''',
    'zero length match',
)

replace_once(
    '''safe_colour() {
  if [[ $no_color == true ]]; then cat; return 0; fi
  set +e
  colour_block
  rc=$?
  set -e
  if (( rc != 0 )); then cat; fi
  return 0
}
''',
    '''safe_colour() {
  if [[ $color_enabled == false ]]; then
    plain_block
    return
  fi
  colour_block
}
''',
    'safe colour fallback',
)

# Theme validation must run before the raw non-TTY fast path, otherwise a typo
# could silently pass on a pipe. Sample/list modes remain explicit transforms.
anchor = '''if [[ $random_theme == true && ${#THEMES[@]} -eq 0 && -z $palette_file ]]; then
  themes_rand=(fire ice sunset ocean rainbow neon forest pastel mono)
  THEMES=("${themes_rand[RANDOM % ${#themes_rand[@]}]}")
fi

# --------------------------- palette ------------------------------
'''
replacement = '''if [[ $random_theme == true && ${#THEMES[@]} -eq 0 && -z $palette_file ]]; then
  themes_rand=(fire ice sunset ocean rainbow neon forest pastel mono)
  THEMES=("${themes_rand[RANDOM % ${#themes_rand[@]}]}")
fi

# --------------------------- palette ------------------------------
'''
# Keep this anchor untouched here; the byte-faithful fast path is inserted after
# palette/theme validation below.
if anchor not in text:
    raise SystemExit('missing transform anchor: theme/random block')

palette_end = '''fi

get_seed() { (( seed > 0 )) && echo "$seed" || echo "$RANDOM"; }

# ---------------------- plain/colour rendering -----------------
'''
replace_once(
    palette_end,
    '''fi

# Default non-TTY execution with no structural/plain transform requested is an
# actual cat fast path. This preserves arbitrary bytes, existing ANSI and exact
# trailing-newline state instead of round-tripping through command substitution.
if [[ $color_enabled == false && $no_color == false && $build_box == false \\
      && -z $header_text && -z $ascii_image && $strip_ansi == false \\
      && $only_match == false && -z $sample_theme ]]; then
  exec cat -- "${files[@]}"
fi

get_seed() { (( seed > 0 )) && echo "$seed" || echo "$RANDOM"; }

# ---------------------- plain/colour rendering -----------------
''',
    'byte faithful non tty path',
)

replace_once(
    '''  if [[ $no_color == true ]]; then
    printf '%s\\n' "$header_payload"
  else
''',
    '''  if [[ $color_enabled == false ]]; then
    printf '%s\\n' "$header_payload" | plain_block
  else
''',
    'header plain path',
)

replace_once(
    '''# defaults: read stdin
[[ ${#files[@]} -eq 0 ]] && files=("-")

# -------------------- stream-safe fast path -----------------------
''',
    '''# -------------------- stream-safe fast path -----------------------
''',
    'remove duplicate stdin default',
)

replace_once(
    '''    if [[ $f == "-" ]]; then
      safe_colour
    else
      cat "$f" | safe_colour
    fi
''',
    '''    if [[ $f == "-" ]]; then
      safe_colour
    else
      safe_colour < "$f"
    fi
''',
    'stream file redirection',
)

replace_once(
    '''  if [[ -n $ascii_image ]]; then
    printf '%s\\n' "$ascii_payload"
    continue
  fi

  $build_box && input=$(printf '%s\\n' "$input" | box_draw)

  if [[ $no_color == true ]]; then
    printf '%s\\n' "$input"
    continue
  fi
''',
    '''  if [[ -n $ascii_image ]]; then
    if [[ $color_enabled == false ]]; then
      printf '%s\\n' "$ascii_payload" | plain_block
    else
      printf '%s\\n' "$ascii_payload"
    fi
    continue
  fi

  # Strip SGR before width-sensitive box rendering whenever plain/no-color was
  # explicitly requested. Unicode display width remains best-effort and is
  # documented because exact wcwidth would require a non-core dependency.
  if [[ $build_box == true && ( $color_enabled == false || $strip_ansi == true ) ]]; then
    input=$(printf '%s\\n' "$input" | strip_sgr_stream)
  fi
  $build_box && input=$(printf '%s\\n' "$input" | box_draw)

  if [[ $color_enabled == false ]]; then
    printf '%s\\n' "$input" | plain_block
    continue
  fi
''',
    'finite plain/image path',
)

# Re-clamp terminal dimensions after the image-specific tput refresh.
replace_once(
    '''TERM_WIDTH=$(tput cols 2>/dev/null || echo "$TERM_WIDTH")
TERM_HEIGHT=$(tput lines 2>/dev/null || echo "$TERM_HEIGHT")

if [[ -n $ascii_image ]]; then
''',
    '''TERM_WIDTH=$(tput cols 2>/dev/null || echo "$TERM_WIDTH")
TERM_HEIGHT=$(tput lines 2>/dev/null || echo "$TERM_HEIGHT")
(( TERM_WIDTH > 0 )) || TERM_WIDTH=80
(( TERM_HEIGHT > 0 )) || TERM_HEIGHT=24
(( TERM_WIDTH  > 160 )) && TERM_WIDTH=160
(( TERM_HEIGHT >  60 )) && TERM_HEIGHT=60

if [[ -n $ascii_image ]]; then
''',
    'terminal dimension clamp',
)

# ORIG_ARGS is no longer required now that unknown flags fail instead of being
# passed back to cat.
text = text.replace('ORIG_ARGS=("$@")\n', '', 1)

path.write_text(text)
