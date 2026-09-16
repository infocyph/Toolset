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

# `head` closes its input early and can make upstream `sort` fail with SIGPIPE
# under `set -o pipefail`. Use sed for bounded display while consuming input.
replace_once(
    '    done | sort -nr | head -20\n',
    "    done | sort -nr | sed -n '1,20p'\n",
)
replace_once(
    '      done | sort -nr | head -15\n',
    "      done | sort -nr | sed -n '1,15p'\n",
)
replace_once(
    '    done | sort -nr | head -"$top"\n',
    '    done | sort -nr | sed -n "1,${top}p"\n',
)
replace_once(
    "    dpkg-query -Wf='${Installed-Size}\\t${Package}\\n' | sort -nr | head -30 |\n",
    "    dpkg-query -Wf='${Installed-Size}\\t${Package}\\n' | sort -nr | sed -n '1,30p' |\n",
)
replace_once(
    "    rpm -qa --qf '%{SIZE}\\t%{NAME}\\n' | sort -nr | head -30 |\n",
    "    rpm -qa --qf '%{SIZE}\\t%{NAME}\\n' | sort -nr | sed -n '1,30p' |\n",
)

# Read-only reporting must remain useful on partially restricted systems.
replace_once('  inode_top_current_dir\n', '  inode_top_current_dir || true\n')
replace_once('  inode_hotspots_var\n', '  inode_hotspots_var || true\n')
replace_once('  inode_deleted_open_files\n', '  inode_deleted_open_files || true\n')

path.write_text(text)
