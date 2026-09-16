#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY="infocyph/Toolset"
PREFIX="${HOME}/.local/bin"
RELEASE="latest"

TOOLS=(chromacat cleanx dockex gitx netx phpx sqlitex)
SELECTED=()

usage() {
  cat <<'EOF'
Usage: bash install.sh [options] <tool> [tool ...]

Install one or more standalone Toolset CLIs from immutable GitHub release assets.

Options:
  --all                 Install all Toolset CLIs.
  --release <version>   Install an exact suite release (for example v2.0.0 or 2.0.0).
  --latest              Install from the latest stable GitHub release (default).
  --prefix <dir>        Installation directory (default: ~/.local/bin).
  --list                List available tool names.
  -h, --help            Show this help.

Examples:
  bash install.sh gitx
  bash install.sh --release v2.0.0 gitx netx
  bash install.sh --all
  bash install.sh --prefix /usr/local/bin dockex

The installer downloads SHA256SUMS from the same release, verifies every selected
asset, runs bash -n and --version, then atomically replaces the destination file.
When replacing an existing tool, the previous file is kept as <tool>.previous.
The installer never invokes sudo automatically.
EOF
}

is_tool() {
  local candidate="$1" tool
  for tool in "${TOOLS[@]}"; do
    [[ "$candidate" == "$tool" ]] && return 0
  done
  return 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'install.sh: required command not found: %s\n' "$1" >&2
    exit 1
  }
}

add_tool() {
  local candidate="$1" existing
  is_tool "$candidate" || {
    printf 'install.sh: unknown tool: %s\n' "$candidate" >&2
    exit 2
  }

  for existing in "${SELECTED[@]:-}"; do
    [[ "$existing" == "$candidate" ]] && return 0
  done
  SELECTED+=("$candidate")
}

while (($#)); do
  case "$1" in
  --all)
    SELECTED=("${TOOLS[@]}")
    shift
    ;;
  --release)
    (($# >= 2)) || {
      printf 'install.sh: --release requires a version\n' >&2
      exit 2
    }
    RELEASE="$2"
    shift 2
    ;;
  --latest)
    RELEASE="latest"
    shift
    ;;
  --prefix)
    (($# >= 2)) || {
      printf 'install.sh: --prefix requires a directory\n' >&2
      exit 2
    }
    PREFIX="$2"
    shift 2
    ;;
  --list)
    printf '%s\n' "${TOOLS[@]}"
    exit 0
    ;;
  -h | --help)
    usage
    exit 0
    ;;
  --*)
    printf 'install.sh: unknown option: %s\n' "$1" >&2
    exit 2
    ;;
  *)
    add_tool "$1"
    shift
    ;;
  esac
done

((${#SELECTED[@]} > 0)) || {
  usage >&2
  exit 2
}

if [[ "$RELEASE" != "latest" ]]; then
  RELEASE="v${RELEASE#v}"
  [[ "$RELEASE" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
    printf 'install.sh: release must use MAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH\n' >&2
    exit 2
  }
fi

require_cmd bash
require_cmd curl
require_cmd install
require_cmd mktemp
require_cmd mv
require_cmd sha256sum

if [[ "$RELEASE" == "latest" ]]; then
  BASE_URL="https://github.com/${REPOSITORY}/releases/latest/download"
  RELEASE_LABEL="latest stable release"
else
  BASE_URL="https://github.com/${REPOSITORY}/releases/download/${RELEASE}"
  RELEASE_LABEL="$RELEASE"
fi

mkdir -p -- "$PREFIX" 2>/dev/null || {
  printf 'install.sh: cannot create installation directory: %s\n' "$PREFIX" >&2
  printf 'Choose a writable --prefix or run this installer with appropriate privileges.\n' >&2
  exit 1
}

[[ -w "$PREFIX" ]] || {
  printf 'install.sh: installation directory is not writable: %s\n' "$PREFIX" >&2
  printf 'Choose a writable --prefix or run this installer with appropriate privileges.\n' >&2
  exit 1
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TMP_DIR"' EXIT INT TERM

CURL_ARGS=(
  --fail
  --location
  --silent
  --show-error
  --retry 3
  --connect-timeout 10
  --max-time 120
)

printf 'Fetching Toolset %s checksums...\n' "$RELEASE_LABEL"
curl "${CURL_ARGS[@]}" \
  "$BASE_URL/SHA256SUMS" \
  --output "$TMP_DIR/SHA256SUMS"

for tool in "${SELECTED[@]}"; do
  printf 'Installing %s from %s...\n' "$tool" "$RELEASE_LABEL"

  checksum_line="$(awk -v name="$tool" '$2 == name {print; exit}' "$TMP_DIR/SHA256SUMS")"
  [[ -n "$checksum_line" ]] || {
    printf 'install.sh: checksum entry missing for %s\n' "$tool" >&2
    exit 1
  }

  curl "${CURL_ARGS[@]}" \
    "$BASE_URL/$tool" \
    --output "$TMP_DIR/$tool"

  (
    cd "$TMP_DIR"
    printf '%s\n' "$checksum_line" | sha256sum -c - >/dev/null
  )

  bash -n "$TMP_DIR/$tool"
  NO_COLOR=1 PHPX_NO_LOG=1 NETX_COLOR=never TERM=dumb \
    bash "$TMP_DIR/$tool" --version >/dev/null

  target="$PREFIX/$tool"
  staged="$PREFIX/.${tool}.tmp.$$"
  previous="$PREFIX/${tool}.previous"

  rm -f -- "$staged"
  install -m 0755 -- "$TMP_DIR/$tool" "$staged"

  if [[ -e "$target" || -L "$target" ]]; then
    rm -f -- "$previous"
    mv -- "$target" "$previous"
  fi

  if ! mv -- "$staged" "$target"; then
    rm -f -- "$staged"
    if [[ -e "$previous" || -L "$previous" ]]; then
      mv -- "$previous" "$target" || true
    fi
    printf 'install.sh: failed to replace %s\n' "$target" >&2
    exit 1
  fi

  printf 'Installed %s -> %s\n' "$tool" "$target"
done

printf 'Toolset installation complete.\n'
