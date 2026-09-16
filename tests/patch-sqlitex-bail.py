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
t = t.replace(old, new, 1)

old = '''  [[ "$applied_any" == false ]] && log_info "No new migrations to apply."
}
'''
new = '''  if [[ "$applied_any" == false ]]; then
    log_info "No new migrations to apply."
  fi
  return 0
}
'''
if old not in t:
    raise SystemExit('migrate_up return block not found')
t = t.replace(old, new, 1)

p.write_text(t)
