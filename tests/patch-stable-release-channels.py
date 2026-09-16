#!/usr/bin/env python3
import re
from pathlib import Path

REPO = "infocyph/Toolset"


def stable_self_update(tool: str) -> str:
    return f'''self_update() (
  set -Eeuo pipefail
  local tool="{tool}"
  local invoked="$0"
  local current_path prefix tmp_dir checksum_line
  local base="https://github.com/{REPO}/releases/latest/download"

  for cmd in curl sha256sum mktemp install mv awk; do
    command -v "$cmd" >/dev/null 2>&1 || {{
      printf '%s: self-update requires %s\\n' "$tool" "$cmd" >&2
      return 1
    }}
  done

  if [[ "$invoked" != */* ]]; then
    invoked="$(command -v -- "$invoked" 2>/dev/null || printf '%s' "$invoked")"
  fi
  current_path="$(readlink -f -- "$invoked" 2>/dev/null || realpath -- "$invoked" 2>/dev/null || printf '%s' "$invoked")"
  prefix="$(dirname -- "$current_path")"

  [[ -w "$prefix" ]] || {{
    printf '%s: install directory is not writable: %s\\n' "$tool" "$prefix" >&2
    printf '%s: rerun with appropriate privileges or reinstall to a writable prefix.\\n' "$tool" >&2
    return 1
  }}

  tmp_dir="$(mktemp -d)"
  trap 'rm -rf -- "$tmp_dir"' EXIT INT TERM

  curl --fail --location --silent --show-error --retry 3 \\
    --connect-timeout 10 --max-time 120 \\
    "$base/SHA256SUMS" --output "$tmp_dir/SHA256SUMS"
  curl --fail --location --silent --show-error --retry 3 \\
    --connect-timeout 10 --max-time 120 \\
    "$base/install.sh" --output "$tmp_dir/install.sh"

  checksum_line="$(awk '$2 == "install.sh" {{print; exit}}' "$tmp_dir/SHA256SUMS")"
  [[ -n "$checksum_line" ]] || {{
    printf '%s: install.sh checksum is missing from latest stable release.\\n' "$tool" >&2
    return 1
  }}

  (
    cd "$tmp_dir"
    printf '%s\\n' "$checksum_line" | sha256sum -c - >/dev/null
  )
  bash -n "$tmp_dir/install.sh"
  bash "$tmp_dir/install.sh" --latest --prefix "$prefix" "$tool"
)
'''


def replace_self_update(path: str, tool: str) -> None:
    p = Path(path)
    text = p.read_text()
    pattern = re.compile(r"self_update\(\) \{\n.*?\n\}\n", re.S)
    updated, count = pattern.subn(stable_self_update(tool), text, count=1)
    if count != 1:
        raise SystemExit(f"could not replace self_update in {path}: matches={count}")
    p.write_text(updated)


replace_self_update("Git/gitx", "gitx")
replace_self_update("PHP/phpx", "phpx")
replace_self_update("ChromaCat/chromacat", "chromacat")
replace_self_update("Clean/cleanx", "cleanx")

# cleanx keeps explicit development channels, but stable release is now default.
clean = Path("Clean/cleanx")
text = clean.read_text()
text = text.replace(
    '# channels: main (default) or a branch/tag name\nCHANNEL="main"',
    '# channels: stable (default) or an explicit development branch/tag\nCHANNEL="stable"',
    1,
)
text = text.replace(
    'remote_url() { echo "${RAW_BASE}/${CHANNEL}/${SCRIPT_PATH_IN_REPO}"; }\nremote_checksum_url() { echo "${RAW_BASE}/${CHANNEL}/${CHECKSUM_PATH_IN_REPO}"; }',
    '''remote_url() {
  if [[ "$CHANNEL" == "stable" || "$CHANNEL" == "latest" ]]; then
    echo "https://github.com/${REPO_SLUG}/releases/latest/download/${TOOL_NAME}"
  else
    echo "${RAW_BASE}/${CHANNEL}/${SCRIPT_PATH_IN_REPO}"
  fi
}
remote_checksum_url() {
  if [[ "$CHANNEL" == "stable" || "$CHANNEL" == "latest" ]]; then
    echo "https://github.com/${REPO_SLUG}/releases/latest/download/SHA256SUMS"
  else
    echo "${RAW_BASE}/${CHANNEL}/${CHECKSUM_PATH_IN_REPO}"
  fi
}''',
    1,
)
clean.write_text(text)

# Per-tool installation docs: latest stable release installer, never mutable main.
docs = {
    "ChromaCat/README.md": "chromacat",
    "Clean/README.md": "cleanx",
    "Docker/README.md": "dockex",
    "Git/README.md": "gitx",
    "Network/README.md": "netx",
    "PHP/README.md": "phpx",
    "Sqlite/README.md": "sqlitex",
}

for filename, tool in docs.items():
    p = Path(filename)
    text = p.read_text()
    pattern = re.compile(
        r'sudo curl -fsSL "https://raw\.githubusercontent\.com/infocyph/Toolset/main/[^\"]+" \\\n\s*-o /usr/local/bin/' + re.escape(tool) + r' && sudo chmod \+x /usr/local/bin/' + re.escape(tool)
    )
    replacement = (
        'curl -fsSLO "https://github.com/infocyph/Toolset/releases/latest/download/install.sh"\n'
        f'bash install.sh {tool}'
    )
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"stable install block not found in {filename}")
    p.write_text(text)
