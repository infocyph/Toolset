#!/usr/bin/env python3
from pathlib import Path

VERSIONS = {
    'ChromaCat/chromacat': ('VERSION="1.3"', 'VERSION="2.0"'),
    'Clean/cleanx': ('readonly VERSION="1.7.0"', 'readonly VERSION="2.0"'),
    'Docker/dockex': ('VERSION="2.0.0-dev"', 'VERSION="2.0"'),
    'Git/gitx': ('VERSION="2.0.0-dev"', 'VERSION="2.0"'),
    'Network/netx': ('VERSION="0.5.0"', 'VERSION="2.0"'),
    'PHP/phpx': ('VERSION="2.0.0-dev"', 'VERSION="2.0"'),
    'Sqlite/sqlitex': ('VERSION="2.0.0-dev"', 'VERSION="2.0"'),
}

for filename, (old, new) in VERSIONS.items():
    path = Path(filename)
    text = path.read_text()
    if old not in text:
        raise SystemExit(f'{filename}: expected version declaration not found')
    path.write_text(text.replace(old, new, 1))

path = Path('tests/generate-manifest.py')
text = path.read_text()
old = 'SUITE_VERSION = os.environ.get("SUITE_VERSION", "2.0.0-dev")'
new = 'SUITE_VERSION = os.environ.get("SUITE_VERSION", "2.0")'
if old not in text:
    raise SystemExit('manifest generator: suite version default not found')
path.write_text(text.replace(old, new, 1))

path = Path('tests/distribution.sh')
text = path.read_text()
old = 'SUITE_VERSION="${SUITE_VERSION:-2.0.0-dev}" \\\n'
new = 'SUITE_VERSION="${SUITE_VERSION:-2.0}" \\\n'
if old not in text:
    raise SystemExit('distribution: suite version default not found')
text = text.replace(old, new, 1)
text = text.replace('    assert entry["version"]\n', '    assert entry["version"] == manifest["suite"]["version"]\n', 1)
path.write_text(text)

path = Path('tests/contracts.sh')
text = path.read_text()
anchor = 'failures=0\n\n'
if 'EXPECTED_VERSION=' not in text:
    text = text.replace(anchor, 'EXPECTED_VERSION="${TOOLSET_EXPECTED_VERSION:-2.0}"\nfailures=0\n\n', 1)
old = '''    if ! [[ "$version_output" =~ ^${name}[[:space:]][0-9]+\\.[0-9]+(\\.[0-9]+)?([.-][0-9A-Za-z][0-9A-Za-z.-]*)?$ ]]; then
      printf 'FAIL: %s --version output is not canonical: %s\\n' "$name" "$version_output" >&2
      failures=$((failures + 1))
      return
    fi
'''
new = '''    if [[ "$version_output" != "$name $EXPECTED_VERSION" ]]; then
      printf 'FAIL: %s --version must report suite version %s: %s\\n' "$name" "$EXPECTED_VERSION" "$version_output" >&2
      failures=$((failures + 1))
      return
    fi
'''
if old not in text:
    raise SystemExit('contracts: version validation block not found')
path.write_text(text.replace(old, new, 1))
