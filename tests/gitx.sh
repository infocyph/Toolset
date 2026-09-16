#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=tests/lib/assert.sh
source "$ROOT_DIR/tests/lib/assert.sh"

TMP_ROOT="$(mktemp -d)"
cleanup() { rm -rf -- "$TMP_ROOT"; }
trap cleanup EXIT INT TERM

export HOME="$TMP_ROOT/home"
export XDG_CONFIG_HOME="$TMP_ROOT/config"
export TMPDIR="$TMP_ROOT/tmp"
mkdir -p -- "$HOME" "$XDG_CONFIG_HOME" "$TMPDIR"

export GITX_LIBRARY_MODE=1
# shellcheck source=/dev/null
source "$ROOT_DIR/Git/gitx"
unset GITX_LIBRARY_MODE

if grep -Eq '(^|[[:space:]])eval([[:space:]]|$)' "$ROOT_DIR/Git/gitx"; then
  fail "gitx still contains eval execution"
fi
if grep -Eq '/tmp/(gitx|git_(log|status))' "$ROOT_DIR/Git/gitx"; then
  fail "gitx still contains predictable shared temp paths"
fi
pass "no eval or predictable gitx temp state"

REPO="$TMP_ROOT/repo"
REMOTE="$TMP_ROOT/remote.git"
git init --bare "$REMOTE" >/dev/null
git init -b main "$REPO" >/dev/null
cd "$REPO"
git config user.name Tester
git config user.email tester@example.com
printf 'one\n' > README.md
git add README.md
git commit -m 'feat: initial' >/dev/null
git remote add origin "$REMOTE"
git push -u origin main >/dev/null

a=$(detect_main_branch)
assert_eq main "$a" "main branch detection"
assert_eq origin "$(gitx_remote)" "remote detection"
pass "local/remote main detection"

# Create-branch must use the detected base without an intermediate checkout of main.
printf 'work\n' > work.txt
git add work.txt
git commit -m 'feat: work' >/dev/null
git push >/dev/null
create_branch feature security-test >/dev/null
assert_eq feature/security-test "$(git branch --show-current)" "created branch"
git ls-remote --exit-code --heads origin refs/heads/feature/security-test >/dev/null
pass "branch creation works with configured remote"

# NUL-safe status collection/staging, including whitespace and newline paths.
printf 'space\n' > 'file with spaces.txt'
newline_file=$'line\nbreak.txt'
printf 'newline\n' > "$newline_file"
mapfile -d '' -t paths < <(gitx_status_paths)
((${#paths[@]} >= 2)) || fail "status path collection lost files"
selected=""
for i in "${!paths[@]}"; do
  if [[ "${paths[$i]}" == 'file with spaces.txt' ]]; then selected="$((i+1))"; fi
done
[[ -n "$selected" ]] || fail "space-containing path not found"
stage_status_indices "$selected"
git diff --cached --name-only -z | grep -Fz 'file with spaces.txt' >/dev/null || fail "space-containing path was not staged"
pass "interactive status path selection is NUL-safe"
git reset --hard HEAD >/dev/null
git clean -fd >/dev/null

# Secure temp state must be private and unique.
t1="$(gitx_mktemp_dir)"
t2="$(gitx_mktemp_dir)"
[[ "$t1" != "$t2" ]] || fail "secure temp directories collided"
[[ "$(stat -c '%a' "$t1")" == 700 ]] || fail "secure temp directory mode is not 700"
pass "secure private temp state"

# Reporting/range fixtures.
printf 'two\n' >> README.md
git add README.md
git commit -m 'fix: second' >/dev/null
printf 'three\n' >> README.md
git add README.md
git commit -m 'docs: third' >/dev/null
worklog="$(generate_worklog HEAD~1..HEAD)"
grep -F 'Author,Email,CommitId,Type,DateTime,Subject,Body' <<<"$worklog" >/dev/null || fail "worklog CSV header missing"
grep -F 'docs: third' <<<"$worklog" >/dev/null || fail "worklog range missed commit"
summary="$(generate_git_summary HEAD~2 lite)"
grep -F '| Tester | tester@example.com |' <<<"$summary" >/dev/null || fail "summary fixture missing author"
report_file="$TMP_ROOT/report.txt"
fetch_prs_and_commits HEAD~1 HEAD "$report_file" >/dev/null
[[ -s "$report_file" ]] || fail "report fixture did not produce output"
pass "report/worklog/summary/range fixtures"

# Worktree safety: refuse switching to a target branch checked out elsewhere.
git switch main >/dev/null
OTHER_WT="$TMP_ROOT/other-wt"
git worktree add "$OTHER_WT" feature/security-test >/dev/null
if branch_checked_out_elsewhere feature/security-test; then :; else fail "worktree branch occupancy was not detected"; fi
git worktree remove "$OTHER_WT" --force >/dev/null
pass "worktree branch occupancy detection"

# Conflict recovery surface: cherry-pick must stop and expose abort/continue rather than marching on.
git switch -c conflict-a main >/dev/null
printf 'A\n' > conflict.txt
git add conflict.txt
git commit -m 'feat: conflict A' >/dev/null
CONFLICT_COMMIT="$(git rev-parse HEAD)"
git switch -c conflict-b main >/dev/null
printf 'B\n' > conflict.txt
git add conflict.txt
git commit -m 'feat: conflict B' >/dev/null
set +e
git cherry-pick "$CONFLICT_COMMIT" >/dev/null 2>&1
conflict_rc=$?
set -e
((conflict_rc != 0)) || fail "fixture did not produce cherry-pick conflict"
cherry_pick_commit --abort >/dev/null
[[ ! -f .git/CHERRY_PICK_HEAD ]] || fail "cherry-pick abort did not clear state"
pass "cherry-pick recovery commands"

git switch main >/dev/null

# Writable settings are data, never shell code.
mkdir -p -- "$GITX_CONFIG_DIR"
printf 'GEMINI_MODEL=gemini-test\nOLLAMA_MODEL=qwen-test:3b\nMALICIOUS=$(touch %s/pwned)\n' "$TMP_ROOT" > "$GITX_CONFIG_FILE"
unset GEMINI_MODEL GEMINI_API_KEY || true
load_gitx_config
assert_eq gemini-test "${GEMINI_MODEL:-}" "declarative Gemini model load"
assert_eq qwen-test:3b "${OLLAMA_MODEL:-}" "declarative Ollama model load"
[[ ! -e "$TMP_ROOT/pwned" ]] || fail "Gemini settings were shell-sourced"
pass "Gemini settings parser is declarative"

# API key persistence is opt-in and separated from non-secret settings.
GEMINI_MODEL=gemini-test
GEMINI_API_KEY=super-secret
save_gitx_config 0
if grep -R -F 'super-secret' "$GITX_CONFIG_DIR" 2>/dev/null; then fail "API key persisted without opt-in"; fi
save_gitx_config 1
[[ "$(stat -c '%a' "$GITX_CREDENTIAL_FILE")" == 600 ]] || fail "credential file mode is not 600"
grep -F 'super-secret' "$GITX_CREDENTIAL_FILE" >/dev/null || fail "opt-in API key persistence failed"
pass "API-key persistence is explicit opt-in"

# Sensitive staged files are blocked unless explicitly overridden; binary payloads are identified.
printf 'TOKEN=secret\n' > .env
git add .env
if ai_staged_safety_check 0 >/dev/null 2>&1; then fail "sensitive staged file was accepted by default"; fi
ai_staged_safety_check 1 >/dev/null
pass "AI commit sensitive-file confirmation boundary"
git reset --hard HEAD >/dev/null
rm -f .env

# Payload size enforcement happens before network access.
python3 - <<'PY' > large.txt
print('x' * 4096)
PY
git add large.txt
GITX_MAX_DIFF_BYTES=128
if prepare_ai_diff "$TMP_ROOT/too-large.diff" 1 >/dev/null 2>&1; then fail "oversized AI diff was accepted"; fi
GITX_MAX_DIFF_BYTES=1048576
prepare_ai_diff "$TMP_ROOT/ok.diff" 1 >/dev/null
[[ -s "$TMP_ROOT/ok.diff" ]] || fail "bounded AI diff was not produced"
pass "AI diff payload bounds"
git reset --hard HEAD >/dev/null
git clean -fd >/dev/null


# AI provider order: reachable local Ollama wins; absent Ollama falls back to Gemini.
OLLAMA_MODEL=""
GITX_OLLAMA_TAGS_JSON=""
GITX_AI_PROVIDER=auto
GITX_OLLAMA_URL='http://ollama.example.test:2244'
curl() {
  printf '%s\n' "$@" > "${GITX_OLLAMA_CURL_ARGS:?}"
  case " $* " in
    *'/api/tags'*) printf '{"models":[{"name":"qwen2.5:3b"},{"name":"llama3.2:3b"}]}' ;;
    *'/api/generate'*) printf '{"response":"feat: local ollama","done":true}' ;;
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
grep -F 'http://ollama.example.test:2244/api/generate' "$GITX_OLLAMA_CURL_ARGS" >/dev/null || fail "custom Ollama generate endpoint missing"
pass "local Ollama provider is preferred and bounded"

unset -f curl
curl() { return 7; }
GITX_OLLAMA_URL='http://127.0.0.1:65534'
GITX_OLLAMA_TAGS_JSON=""
OLLAMA_MODEL=""
GITX_AI_PROVIDER=auto
resolve_ai_provider
assert_eq gemini "$GITX_SELECTED_AI_PROVIDER" "Gemini fallback when Ollama is unavailable"
pass "Gemini fallback is selected only when Ollama is unavailable"
unset -f curl
GITX_OLLAMA_URL='http://127.0.0.1:11434'
GITX_AI_PROVIDER=auto

# API helper must carry finite connect/operation/response limits and key via header, not URL.
MOCK_BIN="$TMP_ROOT/mock-bin"
mkdir -p "$MOCK_BIN"
cat > "$MOCK_BIN/curl" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "${GITX_CURL_ARGS:?}"
printf '{"candidates":[{"content":{"parts":[{"text":"ok"}]}}]}'
EOF
chmod +x "$MOCK_BIN/curl"
export GITX_CURL_ARGS="$TMP_ROOT/curl.args"
OLD_PATH="$PATH"
PATH="$MOCK_BIN:$PATH"
GEMINI_API_KEY='header-secret'
gemini_api_request 'https://example.invalid/model' "$TMP_ROOT/ok.diff" >/dev/null
PATH="$OLD_PATH"
grep -Fx -- '--connect-timeout' "$GITX_CURL_ARGS" >/dev/null || fail "API connect timeout missing"
grep -Fx -- '--max-time' "$GITX_CURL_ARGS" >/dev/null || fail "API operation timeout missing"
grep -Fx -- '--max-filesize' "$GITX_CURL_ARGS" >/dev/null || fail "API response cap missing"
grep -F 'x-goog-api-key: header-secret' "$GITX_CURL_ARGS" >/dev/null || fail "API key header missing"
if grep -Fq 'key=header-secret' "$GITX_CURL_ARGS"; then fail "API key leaked into URL"; fi
pass "Gemini API request is bounded and header-authenticated"

printf '\nAll gitx security and AI-provider checks passed.\n'
