#!/usr/bin/env python3
from pathlib import Path

p = Path('Git/gitx')
t = p.read_text()
replacements = {
    '[[ -z "$GEMINI_API_KEY" && -f "$GITX_CREDENTIAL_FILE" ]]': '[[ -z "${GEMINI_API_KEY:-}" && -f "$GITX_CREDENTIAL_FILE" ]]',
    '[[ -n "$GEMINI_API_KEY" ]] || return 1': '[[ -n "${GEMINI_API_KEY:-}" ]] || return 1',
    '[[ -z "$GEMINI_API_KEY" ]]': '[[ -z "${GEMINI_API_KEY:-}" ]]',
    '[[ -n "$GEMINI_API_KEY" ]] || return 1': '[[ -n "${GEMINI_API_KEY:-}" ]] || return 1',
    '[[ -n "$GEMINI_MODEL" ]] || return 1': '[[ -n "${GEMINI_MODEL:-}" ]] || return 1',
    '[[ -n "$GEMINI_MODEL" ]] || select_gemini_model': '[[ -n "${GEMINI_MODEL:-}" ]] || select_gemini_model',
    'if [[ -z "$GEMINI_API_KEY" || -z "$GEMINI_MODEL" ]]; then': 'if [[ -z "${GEMINI_API_KEY:-}" || -z "${GEMINI_MODEL:-}" ]]; then',
}
for old, new in replacements.items():
    t = t.replace(old, new)
p.write_text(t)
