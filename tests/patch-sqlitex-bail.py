#!/usr/bin/env python3
from pathlib import Path
p = Path('Sqlite/sqlitex')
t = p.read_text()
old = "  {\n    printf 'BEGIN IMMEDIATE;\\n'\n    cat -- \"$file\"\n"
new = "  {\n    printf '.bail on\\nBEGIN IMMEDIATE;\\n'\n    cat -- \"$file\"\n"
if old not in t:
    raise SystemExit('transaction input block not found')
p.write_text(t.replace(old, new, 1))
