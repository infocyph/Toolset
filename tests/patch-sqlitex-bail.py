#!/usr/bin/env python3
from pathlib import Path

p = Path('Sqlite/sqlitex')
t = p.read_text()
old = """    printf 'BEGIN IMMEDIATE;
'
"""
new = """    printf '.bail on
BEGIN IMMEDIATE;
'
"""
if old not in t:
    raise SystemExit('transaction begin block not found')
p.write_text(t.replace(old, new, 1))
