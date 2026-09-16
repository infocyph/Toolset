#!/usr/bin/env python3
from pathlib import Path


def replace_once(text: str, old: str, new: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    return text


# netx: brace expansion before the regex character class.
path = Path("Network/netx")
text = path.read_text()
text = replace_once(
    text,
    'grep -E ":$port[[:space:]]"',
    'grep -E ":${port}[[:space:]]"',
)
path.write_text(text)


# phpx: replace malformed literal carriage-return content with explicit escapes.
path = Path("PHP/phpx")
text = path.read_text()
start_marker = "  _phpx_progress() {"
end_marker = "  # Collect file list (null-safe)"
if start_marker in text and end_marker in text:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    block = text[start:end]
    if "carriage return" in block and "printf '\\r\\033[2K%-*.*s'" not in block:
        replacement = "\n".join(
            [
                "  _phpx_progress() {",
                "    (( show_progress )) || return 0",
                '    local msg="$1"',
                "    # \\r = carriage return, \\033[2K = clear whole line",
                "    printf '\\r\\033[2K%-*.*s' \"$cols\" \"$cols\" \"$msg\" >&2",
                "  }",
                "",
                "  _phpx_clear_line() {",
                "    (( show_progress )) || return 0",
                "    printf '\\r\\033[2K' >&2",
                "  }",
                "",
                "",
            ]
        )
        text = text[:start] + replacement + text[end:]
path.write_text(text)


# dockex: help/version must not require Docker, jq, or awk.
path = Path("Docker/dockex")
text = path.read_text()
if 'VERSION="2.0.0-dev"' not in text:
    text = replace_once(text, "set -euo pipefail\n", 'set -euo pipefail\n\nVERSION="2.0.0-dev"\n')
text = replace_once(text, "require_cmd docker\nrequire_cmd jq\nrequire_cmd awk\n\n", "")
marker = "}\n\n# ------------------ container helpers ------------------- #"
if "printf 'dockex %s\\n'" not in text and marker in text:
    insert = "\n".join(
        [
            "}",
            "",
            'case "${1:-}" in',
            "-h | --help | help)",
            "  show_usage",
            "  exit 0",
            "  ;;",
            "-V | --version | version)",
            "  printf 'dockex %s\\n' \"$VERSION\"",
            "  exit 0",
            "  ;;",
            "esac",
            "",
            "require_cmd docker",
            "require_cmd jq",
            "require_cmd awk",
            "",
            "# ------------------ container helpers ------------------- #",
        ]
    )
    text = replace_once(text, marker, insert)
path.write_text(text)


# gitx: usage is informational; invalid-command failure belongs in dispatch.
path = Path("Git/gitx")
text = path.read_text()
if 'VERSION="2.0.0-dev"' not in text:
    text = replace_once(text, "#!/bin/bash\n", '#!/bin/bash\n\nVERSION="2.0.0-dev"\n')
text = replace_once(
    text,
    '  echo ""\n  exit 1\n}\n\nrequire_sudo() {',
    '  echo ""\n}\n\nrequire_sudo() {',
)
text = replace_once(
    text,
    'case "$cmd" in\nai-commit) generate_ai_commit ;;',
    "\n".join(
        [
            'case "$cmd" in',
            "-h | --help | help) usage ;;",
            "-V | --version | version) printf 'gitx %s\\n' \"$VERSION\" ;;",
            '"") usage ;;',
            "ai-commit) generate_ai_commit ;;",
        ]
    ),
)
text = replace_once(
    text,
    'summary) generate_git_summary "$@" ;;\n*) usage ;;\nesac',
    "\n".join(
        [
            'summary) generate_git_summary "$@" ;;',
            "*)",
            '  echo "Error: Unknown command \'$cmd\'." >&2',
            "  usage >&2",
            "  exit 2",
            "  ;;",
            "esac",
        ]
    ),
)
path.write_text(text)


# sqlitex: expose help/version before DB and sqlite dependency validation.
path = Path("Sqlite/sqlitex")
text = path.read_text()
if 'VERSION="2.0.0-dev"' not in text:
    text = replace_once(
        text,
        "#!/usr/bin/env bash\nset -euo pipefail\n",
        '#!/usr/bin/env bash\nset -euo pipefail\n\nVERSION="2.0.0-dev"\n',
    )
old = "\n".join(
    [
        "  tune             [--profile dev|prod|safe]",
        "EOF",
        "  exit 1",
        "}",
        "",
        "# Parse global options",
    ]
)
if old in text:
    new = "\n".join(
        [
            "  tune             [--profile dev|prod|safe]",
            "EOF",
            "}",
            "",
            'case "${1:-}" in',
            "-h | --help | help)",
            "  usage",
            "  exit 0",
            "  ;;",
            "-V | --version | version)",
            "  printf 'sqlitex %s\\n' \"$VERSION\"",
            "  exit 0",
            "  ;;",
            "esac",
            "",
            "# Parse global options",
        ]
    )
    text = replace_once(text, old, new)
path.write_text(text)
