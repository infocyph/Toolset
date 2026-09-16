#!/usr/bin/env python3
from pathlib import Path

readme = Path('Git/README.md')
text = readme.read_text()
anchor = "Advanced overrides: `GITX_AI_PROVIDER=ollama|gemini|auto`, `GITX_OLLAMA_URL=<url>`.\n"
addition = '''Advanced overrides: `GITX_AI_PROVIDER=ollama|gemini|auto`, `GITX_OLLAMA_URL=<url>`.\n\n### Gemini fallback and API key\n\nWith the default `GITX_AI_PROVIDER=auto`, `gitx ai-commit` checks the configured Ollama endpoint first. If Ollama is unreachable or has no installed model, `gitx` automatically selects Gemini.\n\nGemini credentials are resolved in this order:\n\n1. `GEMINI_API_KEY` from the current environment.\n2. The opt-in Gitx credential file (`${XDG_CONFIG_HOME:-~/.config}/gitx/credentials`).\n3. An interactive prompt when neither source contains a key.\n\nThe recommended non-persistent setup is the environment variable:\n\n```bash\nexport GEMINI_API_KEY=\"your-api-key\"\ngitx ai-commit\n```\n\nThe environment value takes precedence over a persisted credential. Gitx does not persist the key unless persistence is explicitly requested (for example, `gitx ai-commit --persist-api-key` or `GITX_PERSIST_API_KEY=1`). Gemini requests send the key in the `x-goog-api-key` header rather than putting it in the request URL.\n'''
if '### Gemini fallback and API key' not in text:
    if anchor not in text:
        raise SystemExit('Git README provider anchor not found')
    text = text.replace(anchor, addition, 1)
    readme.write_text(text)

test = Path('tests/gitx.sh')
text = test.read_text()
anchor = '''pass "Gemini fallback is selected only when Ollama is unavailable"\nunset -f curl\nGITX_OLLAMA_URL='http://127.0.0.1:11434'\nGITX_AI_PROVIDER=auto\n'''
addition = '''pass "Gemini fallback is selected only when Ollama is unavailable"\nunset -f curl\n\n# Environment GEMINI_API_KEY takes precedence over the optional credential file.\nmkdir -p -- "$GITX_CONFIG_DIR"\nprintf 'GEMINI_API_KEY=file-key\\n' > "$GITX_CREDENTIAL_FILE"\nGEMINI_API_KEY='environment-key'\nload_gitx_config\nassert_eq environment-key "$GEMINI_API_KEY" "Gemini environment key precedence"\npass "Gemini environment key is preferred over persisted credential"\nrm -f -- "$GITX_CREDENTIAL_FILE"\n\nGITX_OLLAMA_URL='http://127.0.0.1:11434'\nGITX_AI_PROVIDER=auto\n'''
if 'Gemini environment key is preferred over persisted credential' not in text:
    if anchor not in text:
        raise SystemExit('gitx test fallback anchor not found')
    text = text.replace(anchor, addition, 1)
    test.write_text(text)
