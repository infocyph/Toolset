#!/usr/bin/env python3
from pathlib import Path

path = Path('Docker/dockex')
text = path.read_text()
old = '''  elif docker exec "$container_name" command -v telnet >/dev/null 2>&1; then
    if docker exec "$container_name" sh -c "echo quit | telnet '$host' '$port'" >/dev/null 2>&1; then
      echo "telnet: TCP connect to $host:$port succeeded."
    else
      echo "telnet: TCP connect to $host:$port FAILED."
    fi
'''
new = '''  elif docker exec "$container_name" command -v telnet >/dev/null 2>&1; then
    if printf 'quit\\n' | docker exec -i "$container_name" telnet "$host" "$port" >/dev/null 2>&1; then
      echo "telnet: TCP connect to $host:$port succeeded."
    else
      echo "telnet: TCP connect to $host:$port FAILED."
    fi
'''
if old not in text:
    raise SystemExit('dockex telnet shell interpolation anchor not found')
path.write_text(text.replace(old, new, 1))
