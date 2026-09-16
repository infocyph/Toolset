#!/usr/bin/env python3
from pathlib import Path


def edit(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f'{path}: expected block not found')
    p.write_text(text.replace(old, new, 1))

edit('Git/gitx', 'GITX_OLLAMA_COMMAND="${GITX_OLLAMA_COMMAND:-ollama}"\n', '')
edit('Git/gitx', '''ollama_available() {
  command -v "$GITX_OLLAMA_COMMAND" >/dev/null 2>&1 || return 1
  GITX_OLLAMA_TAGS_JSON="$(ollama_tags_request 2>/dev/null)" || return 1
  jq -e '.models | type == "array" and length > 0' <<<"$GITX_OLLAMA_TAGS_JSON" >/dev/null 2>&1
}
''', '''ollama_available() {
  GITX_OLLAMA_TAGS_JSON="$(ollama_tags_request 2>/dev/null)" || return 1
  jq -e '.models | type == "array" and length > 0' <<<"$GITX_OLLAMA_TAGS_JSON" >/dev/null 2>&1
}
''')
edit('Git/gitx', '        echo "Ollama was explicitly selected but no reachable local Ollama service with an installed model was found." >&2\n', '        echo "Ollama was explicitly selected but the configured Ollama endpoint is unreachable or has no installed model." >&2\n')

p = Path('Git/README.md')
text = p.read_text()
text = text.replace('When the `ollama` CLI is present, a reachable local Ollama service with at least one installed model is preferred automatically. If Ollama is unavailable, Gemini is used and requires a valid API key/network access.', 'A reachable Ollama API with at least one installed model is preferred automatically. The default endpoint is `http://127.0.0.1:11434`; `GITX_OLLAMA_URL` can point to any trusted local or remote Ollama base URL. If the configured/default Ollama endpoint is unavailable, Gemini is used and requires a valid API key/network access.')
text = text.replace('If the `ollama` command exists, the local Ollama API is reachable (default `http://127.0.0.1:11434`), and at least one local model is installed, `gitx` uses Ollama.', 'If the Ollama API is reachable (default `http://127.0.0.1:11434`) and at least one model is installed, `gitx` uses Ollama. `GITX_OLLAMA_URL` may point to a custom trusted Ollama endpoint.')
text = text.replace(', and `GITX_OLLAMA_COMMAND=<command>`', '')
p.write_text(text)

p = Path('tests/gitx.sh')
text = p.read_text()
text = text.replace('GITX_OLLAMA_COMMAND=ollama_mock\nGITX_OLLAMA_URL=\'http://127.0.0.1:11434\'\nollama_mock() { :; }\n', "GITX_OLLAMA_URL='http://ollama.example.test:2244'\n")
text = text.replace("grep -F '/api/generate' \"$GITX_OLLAMA_CURL_ARGS\" >/dev/null || fail \"Ollama generate endpoint missing\"\n", "grep -F 'http://ollama.example.test:2244/api/generate' \"$GITX_OLLAMA_CURL_ARGS\" >/dev/null || fail \"custom Ollama generate endpoint missing\"\n")
text = text.replace('unset -f ollama_mock curl\nGITX_OLLAMA_COMMAND=gitx-ollama-definitely-missing\nGITX_OLLAMA_TAGS_JSON=""\nOLLAMA_MODEL=""\nGITX_AI_PROVIDER=auto\nresolve_ai_provider\n', '''unset -f curl
curl() { return 7; }
GITX_OLLAMA_URL='http://127.0.0.1:65534'
GITX_OLLAMA_TAGS_JSON=""
OLLAMA_MODEL=""
GITX_AI_PROVIDER=auto
resolve_ai_provider
''')
text = text.replace('GITX_OLLAMA_COMMAND=ollama\nGITX_AI_PROVIDER=auto\n', "unset -f curl\nGITX_OLLAMA_URL='http://127.0.0.1:11434'\nGITX_AI_PROVIDER=auto\n")
p.write_text(text)
