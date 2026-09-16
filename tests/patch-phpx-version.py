#!/usr/bin/env python3
from pathlib import Path

path = Path("PHP/phpx")
text = path.read_text()

if 'VERSION="2.0.0-dev"' not in text:
    text = text.replace(
        "#!/bin/bash\n",
        '#!/bin/bash\n\nVERSION="2.0.0-dev"\n',
        1,
    )

marker = 'setup_logging\nperform_system_checks "$1"\n'
preflight = '''case "${1:-}" in
-h | --help | help)
  display_usage
  exit 0
  ;;
-V | --version | version)
  printf 'phpx %s\\n' "$VERSION"
  exit 0
  ;;
esac

setup_logging
perform_system_checks "${1:-}"
'''

if "printf 'phpx %s\\n'" not in text:
    if marker not in text:
        raise SystemExit("phpx main preflight marker not found")
    text = text.replace(marker, preflight, 1)

path.write_text(text)
