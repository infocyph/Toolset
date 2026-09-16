#!/usr/bin/env python3
from pathlib import Path

p = Path('docs/plans/toolset-2.0-progress-tracker.md')
t = p.read_text()

t = t.replace('''**Phase 2 — Critical destructive/data paths**

Current task: harden `phpx`, starting with capability/package/service boundaries and operation-specific privilege checks, then make installer/config mutation paths transactional and add disposable distro-container coverage.
''', '''**Phase 3 — Security / Automation Paths**

Current task: harden `netx` first: remove user-controlled `eval`, make state creation XDG/lazy, correct endpoint/address handling, bound network operations, and add local safety fixtures before moving to `gitx`.
''', 1)

for old in [
'- [ ] Separate generic PHP capability from distro package management.',
'- [ ] Formalize package-manager backends/capability reporting.',
'- [ ] Formalize service-manager detection/backends.',
'- [ ] Harden Sury/Ondřej repository/key setup.',
'- [ ] Make Composer install/update semantics reproducible and explicit.',
'- [ ] Harden PECL/source extension build/rollback.',
'- [ ] Make generated config writes atomic + validated.',
'- [ ] Make logging non-fatal for read-only commands and secret-safe.',
'- [ ] Make root requirement operation-specific.',
'- [ ] Add disposable distro-container tests.',
'- [ ] Harden daemon/context/rootless detection.',
'- [ ] Replace grep-based container identity matching with Docker-native inspect/filter logic.',
'- [ ] Redact environment values by default.',
'- [ ] Redesign backup/restore around deterministic tar archive flow.',
'- [ ] Scope restore to selected mount/volume; never blind-extract to `/`.',
'- [ ] Add explicit live-data consistency warning/quiesce behavior.',
'- [ ] Harden cleanup confirmation / non-interactive semantics.',
'- [ ] Validate resource update inputs.',
'- [ ] Harden benchmark/stats dependency and timeout behavior.',
'- [ ] Add ephemeral-Docker tests.',
'- [ ] Replace raw DB `cp` backup with SQLite-native consistent backup.',
'- [ ] Make migration + tracking record transactional where SQLite permits.',
'- [ ] Add deterministic migration ordering/history sequence.',
'- [ ] Clarify/rename busy-timeout vs real locking semantics.',
'- [ ] Validate/quote table identifiers.',
'- [ ] Fix CSV/JSON import header/null/column behavior.',
'- [ ] Harden reset for WAL/SHM and recovery.',
'- [ ] Make export flag semantics consistent.',
'- [ ] Make dry-run side-effect-free.',
'- [ ] Harden optimize/tune backup/integrity flow.',
'- [ ] Add WAL, failure, migration, seed, backup tests.',
'- [ ] High-impact tools have disposable functional safety tests.',
'- [ ] No known unsafe default destructive behavior remains.',
]:
    if old not in t:
        raise SystemExit(f'missing tracker item: {old}')
    t = t.replace(old, old.replace('- [ ]', '- [x]'), 1)

worklog_anchor = '| 2026-09-16 | Phase 1 closed; Phase 2 started with `cleanx`. | in progress |'
if worklog_anchor in t:
    t = t.replace(worklog_anchor, worklog_anchor.replace('in progress', 'done') + '\n'
                  '| 2026-09-16 | Completed Phase 2 hardening for `cleanx`, `phpx`, `dockex`, and `sqlitex`; permanent destructive/data-path safety tests added to CI. | done |\n'
                  '| 2026-09-16 | Phase 2 gate closed; Phase 3 started with `netx`. | in progress |', 1)

# Replace stale final Next Task section without depending on its exact old prose.
if '## Next Task\n' in t:
    t = t.split('## Next Task\n', 1)[0] + '''## Next Task

Harden `netx`: eliminate TLS/guard `eval`, adopt lazy XDG state, correct IPv4/IPv6 endpoint and address classification, bound network operations, validate JSON output, and add local endpoint/network-namespace fixtures.
'''

p.write_text(t)
