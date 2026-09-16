#!/usr/bin/env python3
from pathlib import Path

path = Path("docs/plans/toolset-2.0-progress-tracker.md")
text = path.read_text()

replacements = [
    (
        "Current task: harden `cleanx` first, beginning with identity/config/locking and destructive execution boundaries, then add disposable-filesystem safety coverage before moving to the next high-impact tool.",
        "Current task: harden `phpx`, starting with capability/package/service boundaries and operation-specific privilege checks, then make installer/config mutation paths transactional and add disposable distro-container coverage.",
    ),
    ("- [-] Migrate legacy `cleanfy` identity/config paths to `cleanx` with compatibility handling.", "- [x] Migrate legacy `cleanfy` identity/config paths to `cleanx` with compatibility handling."),
    ("- [ ] Replace race-prone `/tmp/.cleanfy.lock` with `flock`/safe fallback.", "- [x] Replace race-prone `/tmp/.cleanfy.lock` with `flock`/safe fallback."),
    ("- [ ] Remove string-built destructive shell execution.", "- [x] Remove string-built destructive shell execution."),
    ("- [ ] Replace shell-sourced config with declarative parsing or safe compatibility boundary.", "- [x] Replace shell-sourced config with declarative parsing or safe compatibility boundary."),
    ("- [ ] Fix full-disk preflight so reclaim-only operations remain possible.", "- [x] Fix full-disk preflight so reclaim-only operations remain possible."),
    ("- [ ] Add package-manager capability backends / explicit skips.", "- [x] Add package-manager capability backends / explicit skips."),
    ("- [ ] Harden target-user/home validation.", "- [x] Harden target-user/home validation."),
    ("- [ ] Make JSON output machine-clean.", "- [x] Make JSON output machine-clean."),
    ("- [ ] Add disposable-filesystem tests.", "- [x] Add disposable-filesystem tests."),
    (
        "- [x] `cleanx` still carries legacy `cleanfy` config/lock naming; Phase 2 starts here.",
        "- [x] `cleanx` legacy `cleanfy` config paths now have data-only compatibility, preferred `cleanx` paths, safe runtime locking, argv-safe deletion, validated target identity and permanent disposable safety tests.",
    ),
    (
        "| 2026-09-16 | Phase 1 closed; Phase 2 started with `cleanx`. | in progress |",
        "| 2026-09-16 | Phase 1 closed; Phase 2 started with `cleanx`. | done |\n| 2026-09-16 | Completed `cleanx` Phase 2 hardening: declarative config, safe locking/deletion, package capability handling, clean JSON, resilient reports, docs and permanent safety tests. | done |\n| 2026-09-16 | Started `phpx` Phase 2 capability and mutation-path hardening. | in progress |",
    ),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f"tracker text not found: {old[:120]!r}")
    text = text.replace(old, new, 1)

next_marker = "## Next Task\n\n"
idx = text.find(next_marker)
if idx == -1:
    raise SystemExit("Next Task marker missing")
text = text[:idx] + next_marker + "Harden `phpx`: separate read-only PHP capabilities from package/service mutation, formalize package-manager and service-manager backends, make privilege checks operation-specific, then harden repository/Composer/PECL/config-write flows with disposable distro-container tests.\n"

path.write_text(text)
