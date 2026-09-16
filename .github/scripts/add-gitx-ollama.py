#!/usr/bin/env python3
from pathlib import Path
import re


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


path = Path('Git/gitx')
text = path.read_text()

# Runtime provider/config variables.
needle = 'GEMINI_API_KEY="${GEMINI_API_KEY:-}"\nGEMINI_MODEL="${GEMINI_MODEL:-}"\n'
replacement = '''GEMINI_API_KEY="${GEMINI_API_KEY:-}"
GEMINI_MODEL="${GEMINI_MODEL:-}"
GITX_AI_PROVIDER="${GITX_AI_PROVIDER:-auto}"
GITX_OLLAMA_URL="${GITX_OLLAMA_URL:-http://127.0.0.1:11434}"
GITX_OLLAMA_COMMAND="${GITX_OLLAMA_COMMAND:-ollama}"
OLLAMA_MODEL="${OLLAMA_MODEL:-${GITX_OLLAMA_MODEL:-}}"
GITX_SELECTED_AI_PROVIDER=""
GITX_OLLAMA_TAGS_JSON=""
'''
if needle not in text:
    raise SystemExit('gitx: runtime variable anchor not found')
text = text.replace(needle, replacement, 1)

# Declarative config supports both provider model choices; only Gemini credential is secret/persisted separately.
old_load = '''      case "$key" in GEMINI_MODEL) [[ "$value" != *$'\\n'* ]] && GEMINI_MODEL="$value" ;; esac
'''
new_load = '''      case "$key" in
        GEMINI_MODEL) [[ "$value" != *$'\\n'* ]] && GEMINI_MODEL="$value" ;;
        OLLAMA_MODEL) [[ "$value" != *$'\\n'* ]] && OLLAMA_MODEL="$value" ;;
      esac
'''
if old_load not in text:
    raise SystemExit('gitx: config loader anchor not found')
text = text.replace(old_load, new_load, 1)
old_save = "  printf 'GEMINI_MODEL=%s\\n' \"$GEMINI_MODEL\" > \"$GITX_CONFIG_FILE\"\n"
new_save = "  printf 'GEMINI_MODEL=%s\\nOLLAMA_MODEL=%s\\n' \"$GEMINI_MODEL\" \"$OLLAMA_MODEL\" > \"$GITX_CONFIG_FILE\"\n"
if old_save not in text:
    raise SystemExit('gitx: config saver anchor not found')
text = text.replace(old_save, new_save, 1)

text = text.replace(
    '  echo "  ai-commit                                        Auto-generate commit message using Gemini AI"',
    '  echo "  ai-commit                                        Auto-generate commit message (local Ollama first, Gemini fallback)"',
    1,
)

# Preserve the existing encoded commit-message policy while replacing the provider-specific implementation.
default_match = re.search(
    r'if \[\[ -z "\$sys_instruction_b64" \]\]; then\n\s*sys_instruction_b64="([A-Za-z0-9+/=]+)"',
    text,
)
if not default_match:
    raise SystemExit('gitx: default AI instruction payload not found')
default_instruction = default_match.group(1)

new_ai = r'''# -------------------------- AI Commit Generator --------------------------

select_gemini_model() {
  echo "Fetching available Gemini models..."
  local response
  response=$(curl --fail --silent --show-error --retry 2 --connect-timeout "$GITX_CONNECT_TIMEOUT" --max-time "$GITX_API_TIMEOUT" --max-filesize "$GITX_MAX_API_RESPONSE_BYTES" -H "x-goog-api-key: $GEMINI_API_KEY" 'https://generativelanguage.googleapis.com/v1beta/models') || return 1
  local -a available_models=()
  mapfile -t available_models < <(jq -r '.models[]? | select(.name | startswith("models/gemini")) | .name | sub("^models/"; "")' <<<"$response")
  if ((${#available_models[@]} == 0)); then
    echo "No Gemini models returned; enter one manually." >&2
    read -rp "Model: " GEMINI_MODEL
  else
    local PS3="Select a model number: " model
    select model in "${available_models[@]}"; do [[ -n "$model" ]] && { GEMINI_MODEL="$model"; break; }; done
  fi
  [[ -n "${GEMINI_MODEL:-}" ]] || return 1
  save_gitx_config "${GITX_PERSIST_API_KEY:-0}"
}

load_or_prompt_gemini_config() {
  load_gitx_config
  if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "Gemini API key not found in the environment or opt-in credential file." >&2
    read -rsp "Paste Gemini API token: " GEMINI_API_KEY; echo
    [[ -n "${GEMINI_API_KEY:-}" ]] || return 1
  fi
  [[ -n "${GEMINI_MODEL:-}" ]] || select_gemini_model
}

ollama_base_url() {
  local base="${GITX_OLLAMA_URL%/}"
  case "$base" in
    http://*|https://*) ;;
    *) base="http://$base" ;;
  esac
  printf '%s\n' "$base"
}

ollama_tags_request() {
  curl --fail --silent --show-error \
    --connect-timeout "$GITX_CONNECT_TIMEOUT" --max-time "$GITX_API_TIMEOUT" \
    --max-filesize "$GITX_MAX_API_RESPONSE_BYTES" \
    "$(ollama_base_url)/api/tags"
}

ollama_available() {
  command -v "$GITX_OLLAMA_COMMAND" >/dev/null 2>&1 || return 1
  GITX_OLLAMA_TAGS_JSON="$(ollama_tags_request 2>/dev/null)" || return 1
  jq -e '.models | type == "array" and length > 0' <<<"$GITX_OLLAMA_TAGS_JSON" >/dev/null 2>&1
}

select_ollama_model() {
  local response="${GITX_OLLAMA_TAGS_JSON:-}"
  [[ -n "$response" ]] || response="$(ollama_tags_request)" || return 1
  local -a models=()
  mapfile -t models < <(jq -r '.models[]?.name // empty' <<<"$response")
  ((${#models[@]} > 0)) || return 1

  if [[ -n "${OLLAMA_MODEL:-}" ]]; then
    local model
    for model in "${models[@]}"; do
      [[ "$model" == "$OLLAMA_MODEL" ]] && return 0
    done
    echo "Configured Ollama model '$OLLAMA_MODEL' is not installed; using '${models[0]}' instead." >&2
  fi
  OLLAMA_MODEL="${models[0]}"
}

resolve_ai_provider() {
  case "${GITX_AI_PROVIDER:-auto}" in
    auto)
      if ollama_available && select_ollama_model; then
        GITX_SELECTED_AI_PROVIDER="ollama"
      else
        GITX_SELECTED_AI_PROVIDER="gemini"
      fi
      ;;
    ollama)
      ollama_available || {
        echo "Ollama was explicitly selected but no reachable local Ollama service with an installed model was found." >&2
        return 1
      }
      select_ollama_model || return 1
      GITX_SELECTED_AI_PROVIDER="ollama"
      ;;
    gemini)
      GITX_SELECTED_AI_PROVIDER="gemini"
      ;;
    *)
      echo "Invalid GITX_AI_PROVIDER: $GITX_AI_PROVIDER (expected auto, ollama, or gemini)." >&2
      return 2
      ;;
  esac
}

ollama_api_request() {
  local payload="$1"
  curl --fail --silent --show-error \
    --connect-timeout "$GITX_CONNECT_TIMEOUT" --max-time "$GITX_API_TIMEOUT" \
    --max-filesize "$GITX_MAX_API_RESPONSE_BYTES" \
    -X POST "$(ollama_base_url)/api/generate" \
    -H 'Content-Type: application/json' --data-binary @"$payload"
}

load_ai_system_instruction() {
  local encoded="${GITX_SYS_INSTRUCTION_B64:-}"
  if [[ -z "$encoded" && -f "$GITX_INSTRUCTION_FILE" ]]; then
    encoded="$(cat "$GITX_INSTRUCTION_FILE")"
  fi
  if [[ -z "$encoded" ]]; then
    encoded="__DEFAULT_INSTRUCTION__"
  fi
  printf '%s' "$encoded" | base64 --decode
}

build_ollama_payload() {
  local model="$1" system="$2" diff_file="$3" output="$4"
  jq -n --arg model "$model" --arg system "$system" --rawfile diff "$diff_file" \
    '{model:$model, system:$system, prompt:("Analyze the following git diff and generate a commit message:\n\n" + $diff), stream:false, options:{temperature:0.1}}' \
    > "$output"
}

build_gemini_payload() {
  local system="$1" diff_file="$2" output="$3"
  jq -n --arg system "$system" --rawfile diff "$diff_file" \
    '{system_instruction:{parts:[{text:$system}]}, contents:[{parts:[{text:("Analyze the following git diff and generate a commit message:\n\n" + $diff)}]}], generation_config:{temperature:0.1,topP:0.9,topK:1}}' \
    > "$output"
}

generate_ai_commit() {
  ensure_git_repo
  local include_sensitive=0 persist_api_key="${GITX_PERSIST_API_KEY:-0}"
  while (($#)); do
    case "$1" in
      --include-sensitive) include_sensitive=1 ;;
      --persist-api-key) persist_api_key=1; GITX_PERSIST_API_KEY=1 ;;
      *) echo "Unknown ai-commit option: $1" >&2; return 2 ;;
    esac
    shift
  done

  if git diff --cached --quiet; then
    echo -e "${RED}No staged changes found.${NC}"
    echo "Please stage your changes first using 'git add <files>'."
    return 1
  fi

  local dependency
  for dependency in jq curl base64; do
    command -v "$dependency" >/dev/null 2>&1 || {
      echo "Error: '$dependency' is required for AI commit generation." >&2
      return 1
    }
  done

  load_gitx_config
  resolve_ai_provider || return $?
  if [[ "$GITX_SELECTED_AI_PROVIDER" == "gemini" ]]; then
    load_or_prompt_gemini_config || return 1
  fi

  echo "Analyzing staged changes..."
  local temp_dir raw_diff payload_file system_instruction commit_msg="" response
  temp_dir="$(gitx_mktemp_dir)" || return 1
  trap 'rm -rf -- "$temp_dir"' RETURN
  raw_diff="$temp_dir/staged.diff"
  payload_file="$temp_dir/request.json"
  prepare_ai_diff "$raw_diff" "$include_sensitive" || return $?
  system_instruction="$(load_ai_system_instruction)" || {
    echo "Failed to decode AI system instruction." >&2
    return 1
  }

  if [[ "$GITX_SELECTED_AI_PROVIDER" == "ollama" ]]; then
    build_ollama_payload "$OLLAMA_MODEL" "$system_instruction" "$raw_diff" "$payload_file" || return 1
    echo "Generating commit message via local Ollama ($OLLAMA_MODEL)..."
    if ! response="$(ollama_api_request "$payload_file")"; then
      echo "Ollama generation failed or exceeded configured limits. Gemini fallback is only used when Ollama is unavailable during provider selection." >&2
      return 1
    fi
    jq -e . >/dev/null <<<"$response" || { echo "Ollama returned invalid JSON." >&2; return 1; }
    commit_msg="$(jq -r '.response // empty' <<<"$response")"
    [[ -n "$commit_msg" && "$commit_msg" != "null" ]] || {
      echo "Ollama returned an empty commit message." >&2
      return 1
    }
  else
    build_gemini_payload "$system_instruction" "$raw_diff" "$payload_file" || return 1
    while true; do
      echo "Generating commit message via Gemini ($GEMINI_MODEL)..."
      local api_url="https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent"
      if ! response="$(gemini_api_request "$api_url" "$payload_file")"; then
        echo "Gemini API request failed or exceeded configured limits." >&2
        return 1
      fi
      jq -e . >/dev/null <<<"$response" || { echo "Gemini returned invalid JSON." >&2; return 1; }
      commit_msg="$(jq -r '.candidates[0].content.parts[0].text // empty' <<<"$response")"
      if [[ -n "$commit_msg" && "$commit_msg" != "null" ]]; then
        break
      fi
      local err_code err_msg err_status retry_action
      err_code="$(jq -r '.error.code // "Unknown"' <<<"$response")"
      err_msg="$(jq -r '.error.message // "Unknown error"' <<<"$response")"
      err_status="$(jq -r '.error.status // "ERROR"' <<<"$response")"
      echo -e "\n${RED}API Error: [${err_code}] ${err_status}${NC}"
      echo -e "${YELLOW}Message: ${err_msg}${NC}\n"
      read -rp "Do you want to try with a different Gemini model? (y/n): " retry_action
      if [[ "$retry_action" =~ ^[Yy]$ ]]; then
        select_gemini_model || return 1
        save_gitx_config "$persist_api_key" || return 1
        continue
      fi
      echo "Aborting commit generation."
      return 1
    done
  fi

  echo -e "\n${YELLOW}================ Generated Commit Message ================${NC}\n"
  echo "$commit_msg"
  echo -e "\n${YELLOW}==========================================================${NC}\n"

  local action
  read -rp "Do you want to commit with this message? (y/e/n) [y=yes, e=edit, n=no]: " action
  case "$action" in
    y|Y)
      git commit -m "$commit_msg"
      echo -e "${GREEN}Committed successfully.${NC}"
      ;;
    e|E)
      local msg_file="$temp_dir/commit-message.txt"
      printf '%s\n' "$commit_msg" > "$msg_file"
      "${EDITOR:-vi}" "$msg_file"
      git commit -F "$msg_file"
      echo -e "${GREEN}Committed successfully.${NC}"
      ;;
    *) echo "Commit cancelled. Your changes remain staged." ;;
  esac
}

'''.replace('__DEFAULT_INSTRUCTION__', default_instruction)

text, count = re.subn(
    r'# -------------------------- AI Commit Generator --------------------------\n.*?(?=# Hooks initializer)',
    new_ai,
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit('gitx: AI section replacement failed')
path.write_text(text)

# README: local-first provider contract.
readme = read('Git/README.md')
readme = readme.replace(
    'Repository workflow, reporting, safe interactive Git operations and optional Gemini-assisted commit generation.',
    'Repository workflow, reporting, safe interactive Git operations and optional AI-assisted commit generation with local Ollama preferred over Gemini.',
)
readme = readme.replace(
    'Bash and Git. Gemini-backed commands additionally need network access, `curl`, a valid API key and the JSON helpers used by that command.',
    'Bash and Git. `ai-commit` additionally needs `curl`, `jq`, and `base64`. When the `ollama` CLI is present, a reachable local Ollama service with at least one installed model is preferred automatically. If Ollama is unavailable, Gemini is used and requires a valid API key/network access.',
)
readme = readme.replace(
    'Repository-changing commands mutate the current Git repository. Interactive path handling is NUL-safe. Gemini settings are declarative, API-key persistence is explicit opt-in, sensitive-looking staged paths are rejected by default, and AI requests are timeout/size bounded.',
    'Repository-changing commands mutate the current Git repository. Interactive path handling is NUL-safe. AI provider selection is local-first: reachable Ollama is used automatically, otherwise Gemini is selected. Gemini settings are declarative, API-key persistence is explicit opt-in, sensitive-looking staged paths are rejected by default, and both Ollama/Gemini requests are timeout/size bounded. A failed Ollama generation is not silently resent to Gemini.',
)
insert = '''\n### AI commit provider order\n\n`gitx ai-commit` defaults to `GITX_AI_PROVIDER=auto`:\n\n1. If the `ollama` command exists, the local Ollama API is reachable (default `http://127.0.0.1:11434`), and at least one local model is installed, `gitx` uses Ollama. `OLLAMA_MODEL`/`GITX_OLLAMA_MODEL` can pin a model; otherwise the first installed model is selected.\n2. If Ollama is unavailable at provider selection, `gitx` falls back to Gemini. Gemini credentials remain opt-in and are never required for the local Ollama path.\n\nAdvanced overrides: `GITX_AI_PROVIDER=ollama|gemini|auto`, `GITX_OLLAMA_URL=<url>`, and `GITX_OLLAMA_COMMAND=<command>`.\n\n'''
marker = '## Command Overview\n'
if insert not in readme:
    readme = readme.replace(marker, insert + marker, 1)
write('Git/README.md', readme)

# Tests: declarative Ollama model config, local-first selection, bounded Ollama request, and Gemini fallback.
tests = read('tests/gitx.sh')
tests = tests.replace(
    "printf 'GEMINI_MODEL=gemini-test\\nMALICIOUS=$(touch %s/pwned)\\n' \"$TMP_ROOT\" > \"$GITX_CONFIG_FILE\"",
    "printf 'GEMINI_MODEL=gemini-test\\nOLLAMA_MODEL=qwen-test:3b\\nMALICIOUS=$(touch %s/pwned)\\n' \"$TMP_ROOT\" > \"$GITX_CONFIG_FILE\"",
)
tests = tests.replace(
    'assert_eq gemini-test "${GEMINI_MODEL:-}" "declarative model load"\n',
    'assert_eq gemini-test "${GEMINI_MODEL:-}" "declarative Gemini model load"\nassert_eq qwen-test:3b "${OLLAMA_MODEL:-}" "declarative Ollama model load"\n',
)
provider_tests = r'''
# AI provider order: reachable local Ollama wins; absent Ollama falls back to Gemini.
OLLAMA_MODEL=""
GITX_OLLAMA_TAGS_JSON=""
GITX_AI_PROVIDER=auto
GITX_OLLAMA_COMMAND=ollama_mock
GITX_OLLAMA_URL='http://127.0.0.1:11434'
ollama_mock() { :; }
curl() {
  printf '%s\n' "$@" > "${GITX_OLLAMA_CURL_ARGS:?}"
  case " $* " in
    *' /api/tags '*) printf '{"models":[{"name":"qwen2.5:3b"},{"name":"llama3.2:3b"}]}' ;;
    *' /api/generate '*) printf '{"response":"feat: local ollama","done":true}' ;;
    *) return 22 ;;
  esac
}
export GITX_OLLAMA_CURL_ARGS="$TMP_ROOT/ollama-curl.args"
resolve_ai_provider
assert_eq ollama "$GITX_SELECTED_AI_PROVIDER" "local Ollama is preferred"
assert_eq qwen2.5:3b "$OLLAMA_MODEL" "first installed Ollama model selected"
printf 'diff --git a/a b/a\n+local\n' > "$TMP_ROOT/ollama.diff"
build_ollama_payload "$OLLAMA_MODEL" 'system prompt' "$TMP_ROOT/ollama.diff" "$TMP_ROOT/ollama.json"
jq -e '.model == "qwen2.5:3b" and .system == "system prompt" and .stream == false and (.prompt | contains("+local"))' "$TMP_ROOT/ollama.json" >/dev/null || fail "Ollama payload contract invalid"
response="$(ollama_api_request "$TMP_ROOT/ollama.json")"
assert_eq 'feat: local ollama' "$(jq -r '.response' <<<"$response")" "Ollama response extraction"
grep -Fx -- '--connect-timeout' "$GITX_OLLAMA_CURL_ARGS" >/dev/null || fail "Ollama connect timeout missing"
grep -Fx -- '--max-time' "$GITX_OLLAMA_CURL_ARGS" >/dev/null || fail "Ollama operation timeout missing"
grep -F '/api/generate' "$GITX_OLLAMA_CURL_ARGS" >/dev/null || fail "Ollama generate endpoint missing"
pass "local Ollama provider is preferred and bounded"

unset -f ollama_mock curl
GITX_OLLAMA_COMMAND=gitx-ollama-definitely-missing
GITX_OLLAMA_TAGS_JSON=""
OLLAMA_MODEL=""
GITX_AI_PROVIDER=auto
resolve_ai_provider
assert_eq gemini "$GITX_SELECTED_AI_PROVIDER" "Gemini fallback when Ollama is unavailable"
pass "Gemini fallback is selected only when Ollama is unavailable"
GITX_OLLAMA_COMMAND=ollama
GITX_AI_PROVIDER=auto
'''
marker = '# API helper must carry finite connect/operation/response limits and key via header, not URL.\n'
if provider_tests not in tests:
    tests = tests.replace(marker, provider_tests + '\n' + marker, 1)
tests = tests.replace("printf '\\nAll gitx Phase 3 checks passed.\\n'", "printf '\\nAll gitx security and AI-provider checks passed.\\n'")
write('tests/gitx.sh', tests)
