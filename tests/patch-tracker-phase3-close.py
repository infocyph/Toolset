#!/usr/bin/env python3
from pathlib import Path

p = Path('docs/plans/toolset-2.0-progress-tracker.md')
t = p.read_text()

old_focus = '''## Current Focus

**Phase 3 — Security / Automation Paths**

Current task: harden `netx` first: remove user-controlled `eval`, make state creation XDG/lazy, correct endpoint/address handling, bound network operations, and add local safety fixtures before moving to `gitx`.
'''
new_focus = '''## Current Focus

**Phase 4 — Presentation Path**

Current task: harden `chromacat`: preserve faithful non-TTY/plain pipeline output, tighten option/no-color/Unicode/TERM behavior, keep streaming bounded, and add golden pipeline/stream fixtures.
'''
if old_focus not in t:
    raise SystemExit('Phase 3 current-focus block not found')
t = t.replace(old_focus, new_focus, 1)

start = t.index('## Phase 3 — Security / Automation Paths')
end = t.index('## Phase 4 — Presentation Path', start)
phase3 = t[start:end]
phase3 = phase3.replace('- [ ]', '- [x]')
t = t[:start] + phase3 + t[end:]

replacements = {
    '- [x] `gitx` uses predictable `/tmp` files in interactive flows; retained for Phase 3 hardening.': '- [x] `gitx` predictable shared `/tmp` state was replaced with private `mktemp` directories and NUL-safe interactive path handling.',
    '- [x] `gitx` sources a settings file containing Gemini configuration; retained for Phase 3 hardening.': '- [x] `gitx` Gemini settings are parsed declaratively; API-key persistence is explicit opt-in with private credential permissions.',
    '- [x] `netx` has TLS command construction through `eval`; retained for Phase 3 hardening.': '- [x] `netx` TLS execution is argv-safe, timeout-bounded, and no longer uses `eval`.',
    '- [x] `netx guard --exec` currently executes through `eval`; retained for Phase 3 hardening.': '- [x] `netx guard --exec` now has an argv-only hook boundary with alert data on stdin; shell `eval` was removed.',
}
for old, new in replacements.items():
    if old not in t:
        raise SystemExit(f'finding line not found: {old}')
    t = t.replace(old, new, 1)

# Add a concise completion record to the Work Log table immediately after its header.
log_header = '''| Date | Change | Status |
|---|---|---|
'''
log_row = '''| 2026-09-16 | Completed Phase 3: hardened `netx`/`gitx`, added permanent security/automation integration tests, and passed the full aggregate CI gate. | done |
'''
if log_header not in t:
    raise SystemExit('work log header not found')
if log_row not in t:
    t = t.replace(log_header, log_header + log_row, 1)

p.write_text(t)
