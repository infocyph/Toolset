#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('Network/netx')
t = p.read_text()

old = '''        local proto local remote pid comm user local_ip local_port remote_ip remote_port
        IFS='|' read -r proto local remote pid comm user <<<"$line"
        IFS='|' read -r local_ip local_port < <(split_endpoint "$local")
        IFS='|' read -r remote_ip remote_port < <(split_endpoint "$remote")
'''
new = '''        local proto local_ep remote_ep pid comm user local_ip local_port remote_ip remote_port
        IFS='|' read -r proto local_ep remote_ep pid comm user <<<"$line"
        IFS='|' read -r local_ip local_port < <(split_endpoint "$local_ep")
        IFS='|' read -r remote_ip remote_port < <(split_endpoint "$remote_ep")
'''
if old not in t:
    raise SystemExit('generated guard variable block not found')
t = t.replace(old, new, 1)

pattern = r'''json_escape\(\) \{.*?\n\}\n\nvalidate_json_file\(\)'''
replacement = r'''json_escape() {
  local data
  data="$(cat)"
  data=${data//\\/\\\\}
  data=${data//\"/\\\"}
  data=${data//$'\b'/\\b}
  data=${data//$'\f'/\\f}
  data=${data//$'\n'/\\n}
  data=${data//$'\r'/\\r}
  data=${data//$'\t'/\\t}
  printf '%s' "$data"
}

validate_json_file()'''
t2, count = re.subn(pattern, lambda _m: replacement, t, count=1, flags=re.S)
if count != 1:
    raise SystemExit('generated JSON escape function not found')

p.write_text(t2)
