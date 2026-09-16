#!/usr/bin/env python3
from pathlib import Path

path = Path("Clean/cleanx")
text = path.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"expected block not found: {old!r}")
    text = text.replace(old, new, 1)


replace_once(
    'CONFIG_OVERRIDE_FILE=""\nEXCLUDE_GLOBS=()\n',
    'CONFIG_OVERRIDE_FILE=""\nCHANNEL_OVERRIDE=""\nEXCLUDE_GLOBS=()\n',
)

replace_once(
'''for arg in "$@"; do
  case "$arg" in
  --config=*) CONFIG_OVERRIDE_FILE="${arg#*=}" ;;
  --json) JSON_REPORT=1 ;;
  esac
done

load_default_configs
[[ -n "$CONFIG_OVERRIDE_FILE" ]] && load_config_file "$CONFIG_OVERRIDE_FILE" 1
resolve_target_user
''',
'''for arg in "$@"; do
  case "$arg" in
  --config=*) CONFIG_OVERRIDE_FILE="${arg#*=}" ;;
  --channel=*) CHANNEL_OVERRIDE="${arg#*=}" ;;
  --json) JSON_REPORT=1 ;;
  esac
done

load_default_configs
[[ -n "$CONFIG_OVERRIDE_FILE" ]] && load_config_file "$CONFIG_OVERRIDE_FILE" 1
[[ -n "$CHANNEL_OVERRIDE" ]] && CHANNEL="$CHANNEL_OVERRIDE"
resolve_target_user
''')

replace_once(
    '  tasks="report apt apt-residuals journal logs tmp tmpfiles usercache langcaches snap flatpak docker podman containerd kernels coredumps buildcache browsers timeshift pkgbig inode-scan fshints all"\n',
    '  tasks="report packages apt apt-residuals journal logs tmp tmpfiles usercache langcaches snap flatpak docker podman containerd kernels coredumps buildcache browsers timeshift pkgbig inode-scan fshints all"\n',
)

path.write_text(text)
