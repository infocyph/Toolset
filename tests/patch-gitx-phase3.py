#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('Git/gitx')
t = p.read_text()

def one(old: str, new: str, label: str) -> None:
    global t
    if old not in t:
        raise SystemExit(f'missing patch anchor: {label}')
    t = t.replace(old, new, 1)

def rx(pattern: str, repl: str, label: str) -> None:
    global t
    t2, n = re.subn(pattern, repl, t, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'failed regex patch: {label} ({n})')
    t = t2

# Shared hardening helpers remain internal to this single-file CLI.
anchor = '''if ! declare -F log_action >/dev/null 2>&1; then
  log_action() { :; }
fi
'''
helpers = r'''

GITX_CONFIG_DIR="${GITX_CONFIG_DIR:-${XDG_CONFIG_HOME:-${HOME:-/tmp}/.config}/gitx}"
GITX_CONFIG_FILE="${GITX_CONFIG_FILE:-$GITX_CONFIG_DIR/settings}"
GITX_CREDENTIAL_FILE="${GITX_CREDENTIAL_FILE:-$GITX_CONFIG_DIR/credentials}"
GITX_INSTRUCTION_FILE="${GITX_INSTRUCTION_FILE:-$GITX_CONFIG_DIR/instructions.b64}"
GITX_API_TIMEOUT="${GITX_API_TIMEOUT:-30}"
GITX_CONNECT_TIMEOUT="${GITX_CONNECT_TIMEOUT:-10}"
GITX_MAX_API_RESPONSE_BYTES="${GITX_MAX_API_RESPONSE_BYTES:-1048576}"
GITX_MAX_DIFF_BYTES="${GITX_MAX_DIFF_BYTES:-524288}"
GEMINI_API_KEY="${GEMINI_API_KEY:-}"
GEMINI_MODEL="${GEMINI_MODEL:-}"

is_uint() { [[ "${1:-}" =~ ^[0-9]+$ ]]; }

gitx_mktemp_dir() {
  local base="${TMPDIR:-/tmp}" dir
  mkdir -p -- "$base" || return 1
  dir="$(mktemp -d "$base/gitx.XXXXXX")" || return 1
  chmod 700 "$dir" || { rm -rf -- "$dir"; return 1; }
  printf '%s\n' "$dir"
}

gitx_remote() {
  local requested="${GITX_REMOTE:-}"
  if [[ -n "$requested" ]] && git remote get-url "$requested" >/dev/null 2>&1; then printf '%s\n' "$requested"; return 0; fi
  if git remote get-url origin >/dev/null 2>&1; then printf '%s\n' origin; return 0; fi
  git remote | head -n1
}

branch_checked_out_elsewhere() {
  local branch="$1" current_root line
  current_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  local worktree=""
  while IFS= read -r line; do
    case "$line" in
      worktree\ *) worktree="${line#worktree }" ;;
      "branch refs/heads/$branch") [[ "$worktree" != "$current_root" ]] && return 0 ;;
    esac
  done < <(git worktree list --porcelain 2>/dev/null)
  return 1
}

require_clean_worktree() {
  [[ -z "$(git status --porcelain --untracked-files=no)" ]] || {
    echo "Error: tracked working-tree changes must be committed or stashed first." >&2
    return 1
  }
}

gitx_status_paths() {
  local rec status path
  while IFS= read -r -d '' rec; do
    status="${rec:0:2}"
    path="${rec:3}"
    printf '%s\0' "$path"
    if [[ "$status" == *R* || "$status" == *C* ]]; then
      IFS= read -r -d '' _old || true
    fi
  done < <(git status --porcelain=v1 -z --untracked-files=all)
}

stage_status_indices() {
  local selection="$1" token idx
  local -a files=()
  mapfile -d '' -t files < <(gitx_status_paths)
  [[ ${#files[@]} -gt 0 ]] || return 0
  IFS=',' read -r -a tokens <<<"$selection"
  for token in "${tokens[@]}"; do
    token="${token//[[:space:]]/}"
    is_uint "$token" && ((10#$token >= 1 && 10#$token <= ${#files[@]})) || {
      echo "Invalid file selection: $token" >&2
      return 2
    }
    idx=$((10#$token - 1))
    git add -- "${files[$idx]}" || return 1
  done
}

load_gitx_config() {
  local key value
  if [[ -f "$GITX_CONFIG_FILE" ]]; then
    while IFS='=' read -r key value; do
      case "$key" in GEMINI_MODEL) [[ "$value" != *$'\n'* ]] && GEMINI_MODEL="$value" ;; esac
    done < "$GITX_CONFIG_FILE"
  fi
  if [[ -z "$GEMINI_API_KEY" && -f "$GITX_CREDENTIAL_FILE" ]]; then
    while IFS='=' read -r key value; do
      case "$key" in GEMINI_API_KEY) [[ "$value" != *$'\n'* ]] && GEMINI_API_KEY="$value" ;; esac
    done < "$GITX_CREDENTIAL_FILE"
  fi
}

save_gitx_config() {
  local persist_key="${1:-0}"
  mkdir -p -m 700 -- "$GITX_CONFIG_DIR" || return 1
  printf 'GEMINI_MODEL=%s\n' "$GEMINI_MODEL" > "$GITX_CONFIG_FILE"
  chmod 600 "$GITX_CONFIG_FILE"
  if [[ "$persist_key" == 1 ]]; then
    [[ -n "$GEMINI_API_KEY" ]] || return 1
    printf 'GEMINI_API_KEY=%s\n' "$GEMINI_API_KEY" > "$GITX_CREDENTIAL_FILE"
    chmod 600 "$GITX_CREDENTIAL_FILE"
  else
    rm -f -- "$GITX_CREDENTIAL_FILE"
  fi
}

is_sensitive_path() {
  local path="${1,,}"
  [[ "$path" =~ (^|/)(\.env($|\.)|id_rsa$|id_ed25519$|credentials?($|\.)|secrets?($|\.)|[^/]+\.(pem|key|p12|pfx|keystore)$) ]]
}

ai_staged_safety_check() {
  local allow_sensitive="${1:-0}" path sensitive=0 binary=0
  while IFS= read -r -d '' path; do
    if is_sensitive_path "$path"; then
      echo "Sensitive-looking staged path: $path" >&2
      sensitive=1
    fi
    if git show ":$path" 2>/dev/null | LC_ALL=C grep -Iq .; then :; else
      echo "Binary staged path will not expose binary bytes in the normal Git diff: $path" >&2
      binary=1
    fi
  done < <(git diff --cached --name-only -z --diff-filter=ACMR)
  if ((sensitive)) && [[ "$allow_sensitive" != 1 ]]; then
    echo "Refusing AI commit with sensitive-looking staged paths; rerun with --include-sensitive only after review." >&2
    return 2
  fi
  : "$binary"
}

prepare_ai_diff() {
  local output="$1" allow_sensitive="${2:-0}" size
  ai_staged_safety_check "$allow_sensitive" || return $?
  git diff --cached --no-ext-diff --no-textconv > "$output" || return 1
  [[ -s "$output" ]] || { echo "No textual staged diff available." >&2; return 1; }
  size="$(wc -c < "$output" | tr -d ' ')"
  is_uint "$size" || return 1
  if ((10#$size > GITX_MAX_DIFF_BYTES)); then
    echo "Staged diff is ${size} bytes; limit is ${GITX_MAX_DIFF_BYTES}. Stage a smaller change or raise GITX_MAX_DIFF_BYTES explicitly." >&2
    return 3
  fi
}

gemini_api_request() {
  local url="$1" payload="$2"
  curl --fail --silent --show-error --retry 2 \
    --connect-timeout "$GITX_CONNECT_TIMEOUT" --max-time "$GITX_API_TIMEOUT" \
    --max-filesize "$GITX_MAX_API_RESPONSE_BYTES" \
    -X POST "$url" -H 'Content-Type: application/json' \
    -H "x-goog-api-key: $GEMINI_API_KEY" --data-binary @"$payload"
}
'''
one(anchor, anchor + helpers, 'shared helpers')

# Robust main-branch detection works with or without origin and respects configured remote.
rx(r'''detect_main_branch\(\) \{.*?\n\}''', r'''detect_main_branch() {
  local remote="${1:-$(gitx_remote)}" ref candidate
  if [[ -n "$remote" ]] && ref="$(git symbolic-ref -q "refs/remotes/$remote/HEAD" 2>/dev/null)"; then
    printf '%s\n' "${ref#refs/remotes/$remote/}"
    return 0
  fi
  for candidate in main trunk master; do
    if git show-ref --verify --quiet "refs/heads/$candidate"; then printf '%s\n' "$candidate"; return 0; fi
  done
  if [[ -n "$remote" ]]; then
    for candidate in main trunk master; do
      if git show-ref --verify --quiet "refs/remotes/$remote/$candidate"; then printf '%s\n' "$candidate"; return 0; fi
    done
  fi
  git branch --show-current
}''', 'main detection')

rx(r'''create_branch\(\) \{.*?\n\}\n\n# Sync alpha''', r'''create_branch() {
  local branch_type="${1:-}" name="${2:-}"
  ensure_git_repo
  [[ -n "$branch_type" && -n "$name" ]] || { echo "Error: Branch type and name are required."; return 1; }
  [[ "$branch_type" =~ ^(feature|bugfix|hotfix|release|docs|ci|experiment)$ ]] || { echo "Error: Unsupported branch type '$branch_type'."; return 2; }
  local branch_name="${branch_type}/${name}" remote main_branch base_ref
  git check-ref-format --branch "$branch_name" >/dev/null 2>&1 || { echo "Error: Invalid branch name '$branch_name'."; return 2; }
  git show-ref --verify --quiet "refs/heads/$branch_name" && { echo "Error: Branch '$branch_name' already exists."; return 1; }
  remote="$(gitx_remote)"
  main_branch="$(detect_main_branch "$remote")"
  base_ref="$main_branch"
  if [[ -n "$remote" ]]; then
    git fetch --prune "$remote" >/dev/null 2>&1 || return 1
    git show-ref --verify --quiet "refs/remotes/$remote/$main_branch" && base_ref="$remote/$main_branch"
  fi
  git switch -c "$branch_name" "$base_ref" || return 1
  if [[ -n "$remote" ]]; then git push -u "$remote" "$branch_name" || return 1; fi
  echo "Branch created: $branch_name"
}

# Sync alpha''', 'create branch')

# Worktree-aware sync and merge preserve the original checkout and avoid assuming origin.
rx(r'''sync_branches\(\) \{.*?\n\}\n\n# Merge branches''', r'''sync_branches() {
  ensure_git_repo
  require_clean_worktree || return 1
  local remote main_branch base_ref original branch sync_more additional_branches
  remote="$(gitx_remote)"
  main_branch="$(detect_main_branch "$remote")"
  original="$(git branch --show-current)"
  base_ref="$main_branch"
  if [[ -n "$remote" ]]; then
    git fetch --prune "$remote" || return 1
    git show-ref --verify --quiet "refs/remotes/$remote/$main_branch" && base_ref="$remote/$main_branch"
  fi
  local -a branches=(alpha develop)
  read -rp "Do you want to sync additional branches? (y/n): " sync_more
  if [[ "$sync_more" == y ]]; then IFS=',' read -r -a user_branches <<<"${additional_branches:-}"; branches+=("${user_branches[@]}"); fi
  for branch in "${branches[@]}"; do
    git show-ref --verify --quiet "refs/heads/$branch" || { echo "Branch '$branch' does not exist. Skipping."; continue; }
    branch_checked_out_elsewhere "$branch" && { echo "Branch '$branch' is checked out in another worktree. Skipping."; continue; }
    git switch "$branch" || return 1
    git merge --no-ff "$base_ref" || { echo "Merge conflict on '$branch'; resolve it or run git merge --abort."; return 2; }
    [[ -n "$remote" ]] && git push "$remote" "$branch" || true
  done
  [[ -n "$original" && "$(git branch --show-current)" != "$original" ]] && git switch "$original" >/dev/null || true
}

# Merge branches''', 'sync branches')

rx(r'''merge_branch\(\) \{.*?\n\}\n\n# Tag a release''', r'''merge_branch() {
  local source="${1:-}" target="${2:-}"
  ensure_git_repo
  [[ -n "$source" && -n "$target" ]] || { echo "Error: Source and target branches are required."; return 1; }
  git show-ref --verify --quiet "refs/heads/$source" || { echo "Error: Source branch '$source' does not exist."; return 1; }
  git show-ref --verify --quiet "refs/heads/$target" || { echo "Error: Target branch '$target' does not exist."; return 1; }
  branch_checked_out_elsewhere "$target" && { echo "Error: Target branch '$target' is checked out in another worktree."; return 2; }
  require_clean_worktree || return 1
  read -rp "Merge '$source' into '$target'? (y/n): " confirm
  [[ "$confirm" == y ]] || { echo "Merge cancelled."; return 0; }
  local original remote
  original="$(git branch --show-current)"; remote="$(gitx_remote)"
  git switch "$target" || return 1
  if [[ -n "$remote" ]]; then
    git fetch --prune "$remote" || return 1
    if git show-ref --verify --quiet "refs/remotes/$remote/$target"; then git merge --ff-only "$remote/$target" || return 1; fi
  fi
  git merge --no-ff "$source" || { echo "Merge conflict; resolve it or run git merge --abort."; return 2; }
  [[ -n "$remote" ]] && git push "$remote" "$target" || true
  [[ -n "$original" && "$original" != "$target" ]] && git switch "$original" >/dev/null || true
}

# Tag a release''', 'merge branch')

# No predictable temp files; conflict state gets explicit recovery commands.
rx(r'''cherry_pick_commit\(\) \{.*?\n\}\n\nclean_untracked''', r'''cherry_pick_commit() {
  ensure_git_repo
  case "${1:-}" in
    --continue) git cherry-pick --continue; return $? ;;
    --abort) git cherry-pick --abort; return $? ;;
    --skip) git cherry-pick --skip; return $? ;;
  esac
  local -a commits=()
  mapfile -t commits < <(git log --format='%H')
  ((${#commits[@]})) || { echo "No commits available."; return 1; }
  echo "Recent Commit History:"
  local i
  for i in "${!commits[@]}"; do printf '%2d. %s\n' "$((i+1))" "$(git show -s --format='%h %s' "${commits[$i]}")"; done
  read -rp "Enter the numbers of the commits to cherry-pick (comma-separated): " selection
  local token idx
  IFS=',' read -r -a tokens <<<"$selection"
  for token in "${tokens[@]}"; do
    token="${token//[[:space:]]/}"
    is_uint "$token" && ((10#$token >= 1 && 10#$token <= ${#commits[@]})) || { echo "Invalid selection: $token"; return 2; }
    idx=$((10#$token - 1))
    if ! git cherry-pick "${commits[$idx]}"; then
      echo "Cherry-pick stopped on conflict. Resolve and run 'gitx cherry-pick --continue', or run 'gitx cherry-pick --abort'/'--skip'." >&2
      return 2
    fi
  done
}

clean_untracked''', 'cherry-pick')

rx(r'''revert_commit\(\) \{.*?\n\}\n\nreset_branch_to_remote''', r'''revert_commit() {
  ensure_git_repo
  case "${1:-}" in
    --continue) git revert --continue; return $? ;;
    --abort) git revert --abort; return $? ;;
    --skip) git revert --skip; return $? ;;
  esac
  local -a commits=()
  mapfile -t commits < <(git log --format='%H')
  echo "Recent Commit History:"
  local i
  for i in "${!commits[@]}"; do printf '%2d. %s\n' "$((i+1))" "$(git show -s --format='%h %s' "${commits[$i]}")"; done
  read -rp "Enter the numbers of the commits to revert (comma-separated): " selection
  local token idx
  IFS=',' read -r -a tokens <<<"$selection"
  for token in "${tokens[@]}"; do
    token="${token//[[:space:]]/}"
    is_uint "$token" && ((10#$token >= 1 && 10#$token <= ${#commits[@]})) || { echo "Invalid selection: $token"; return 2; }
    idx=$((10#$token - 1))
    if ! git revert "${commits[$idx]}"; then
      echo "Revert stopped on conflict. Resolve and run 'gitx revert --continue', or run 'gitx revert --abort'/'--skip'." >&2
      return 2
    fi
  done
}

reset_branch_to_remote''', 'revert')

rx(r'''interactive_commit\(\) \{.*?\n\}\n\nshow_status''', r'''interactive_commit() {
  ensure_git_repo
  local -a files=()
  mapfile -d '' -t files < <(gitx_status_paths)
  ((${#files[@]})) || { echo "No changes to commit."; return 0; }
  echo "Select files to stage:"
  local i
  for i in "${!files[@]}"; do printf '%2d. %q\n' "$((i+1))" "${files[$i]}"; done
  read -rp "Enter file numbers (comma-separated, 'a' for all): " selection
  if [[ "$selection" == a ]]; then git add -A -- .; else stage_status_indices "$selection" || return $?; fi
  git diff --cached --name-only
  read -rp "Enter your commit message: " commit_message
  [[ -n "$commit_message" ]] || { echo "Commit message cannot be empty."; return 2; }
  git commit -m "$commit_message"
}

show_status''', 'interactive commit')

rx(r'''show_large_files\(\) \{.*?\n\}\n\nfetch_and_prune''', r'''show_large_files() {
  ensure_git_repo
  read -rp "How many large files do you want to display? (default 10): " count
  count="${count:-10}"
  is_uint "$count" && ((10#$count > 0 && 10#$count <= 10000)) || { echo "Invalid count."; return 2; }
  echo "Choose an action:"; echo "1. Display results inline"; echo "2. Save results to a file"
  read -rp "Enter your choice: " choice
  local output_file=""
  [[ "$choice" == 2 ]] && { read -rp "Enter output file (default: large_files.txt): " output_file; output_file="${output_file:-large_files.txt}"; }
  [[ "$choice" == 1 || "$choice" == 2 ]] || { echo "Invalid choice."; return 2; }
  if [[ "$choice" == 1 ]]; then
    git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '$1=="blob" {print $3, $4}' | sort -k1,1nr | head -n "$count" | awk '{printf "%s bytes  %s\n", $1, $2}'
  else
    git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '$1=="blob" {print $3, $4}' | sort -k1,1nr | head -n "$count" | awk '{printf "%s bytes  %s\n", $1, $2}' > "$output_file"
    echo "Results saved to $output_file"
  fi
}

fetch_and_prune''', 'large files')

# Heavy summary path traversal is NUL-safe and does not marshal filenames through shell words.
rx(r'''    # Heavy mode: blame over entire repo \(accurate surviving code\).*?    fi\n  fi\n\n  echo "\| Author Name''', r'''    # Heavy mode: blame over the repository using NUL-delimited tracked paths.
    while IFS= read -r -d '' f; do
      local mime
      mime=$(file --mime-type -b -- "$f" 2>/dev/null || true)
      local include=0
      if [[ "$include_all" == true && "$mime" =~ ^text/ ]]; then include=1
      else
        case "$f" in
          *.sh|*.py|*.js|*.ts|*.go|*.java|*.c|*.cpp|*.php|*.rb|*.html|*.css|*.scss|*.sql|*.xml|*.json|*.yaml|*.yml|*.md|*.toml|*.ini|*.cfg|*.conf|*.properties|Makefile|makefile|Dockerfile|.env|.gitignore) include=1 ;;
        esac
      fi
      ((include)) || continue
      git blame --line-porcelain -- "$f" 2>/dev/null | grep -E '^author-mail' >> "$blame_file" || true
    done < <(git ls-files -z)
  fi

  echo "| Author Name''', 'summary NUL paths')

# Replace unsafe Gemini config loader/model fetcher. API keys are header-authenticated and persistence is opt-in.
rx(r'''GITX_CONFIG_DIR="\$HOME/\.config/gitx".*?\n\}\n\ngenerate_ai_commit\(\)''', r'''select_gemini_model() {
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
  [[ -n "$GEMINI_MODEL" ]] || return 1
  save_gitx_config "${GITX_PERSIST_API_KEY:-0}"
}

load_or_prompt_gemini_config() {
  load_gitx_config
  if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "Gemini API key not found in the environment or opt-in credential file." >&2
    read -rsp "Paste Gemini API token: " GEMINI_API_KEY; echo
    [[ -n "$GEMINI_API_KEY" ]] || return 1
  fi
  [[ -n "$GEMINI_MODEL" ]] || select_gemini_model
}

generate_ai_commit()''', 'Gemini config/model')

# Add flags and staged safety at AI entry.
one('''generate_ai_commit() {
  ensure_git_repo

  # 1. Check for staged changes
''', '''generate_ai_commit() {
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

  # 1. Check for staged changes
''', 'AI args')

# Replace predictable raw diff temp with private directory and bounded source diff.
one('''  echo "Analyzing staged changes..."

  # Generate base64 diff into a temp file to avoid "argument list too long"
  # when passing large staged diffs to jq.
  local diff_b64_file="/tmp/gitx_diff_b64_$$.txt"
  git diff --cached | base64 | tr -d '\\n' > "$diff_b64_file"

  if [[ ! -s "$diff_b64_file" ]]; then
    rm -f "$diff_b64_file"
    echo -e "${RED}Error: Failed to read or encode git diff.${NC}"
    exit 1
  fi
''', '''  echo "Analyzing staged changes..."
  local temp_dir raw_diff diff_b64_file
  temp_dir="$(gitx_mktemp_dir)" || return 1
  trap 'rm -rf -- "$temp_dir"' RETURN
  raw_diff="$temp_dir/staged.diff"
  diff_b64_file="$temp_dir/diff.b64"
  prepare_ai_diff "$raw_diff" "$include_sensitive" || return $?
  base64 < "$raw_diff" | tr -d '\\n' > "$diff_b64_file"
  [[ -s "$diff_b64_file" ]] || { echo "Failed to encode staged diff." >&2; return 1; }
''', 'AI diff temp')

# Payload temp belongs to private temp directory.
t = t.replace('local payload_file="/tmp/gitx_payload_$$.json"', 'local payload_file="$temp_dir/payload.json"')

# API URL contains no credential; bounded helper owns the request.
rx(r'''    local api_url="https://generativelanguage\.googleapis\.com/v1beta/models/\$\{GEMINI_MODEL\}:generateContent\?key=\$GEMINI_API_KEY"\n\n    local response\n    response=\$\(curl -s -X POST "\$api_url" \\\n      -H 'Content-Type: application/json' \\\n      -d @"\$payload_file"\)''', r'''    local api_url="https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent"

    local response
    if ! response=$(gemini_api_request "$api_url" "$payload_file"); then
      echo "Gemini API request failed or exceeded configured limits." >&2
      return 1
    fi
    jq -e . >/dev/null <<<"$response" || { echo "Gemini returned invalid JSON." >&2; return 1; }''', 'AI API call')

# Opt-in persistence after configuration selection.
t = t.replace('select_gemini_model\n        echo "Retrying..."', 'select_gemini_model || return 1\n        save_gitx_config "$persist_api_key" || return 1\n        echo "Retrying..."')

# Secure edit temp file inside private temp dir.
one('''    local msg_file="/tmp/gitx_commit_msg_$$.txt"
    echo "$commit_msg" > "$msg_file"
    ${EDITOR:-vi} "$msg_file"
    git commit -F "$msg_file"
    rm -f "$msg_file"
''', '''    local msg_file="$temp_dir/commit-message.txt"
    printf '%s\\n' "$commit_msg" > "$msg_file"
    "${EDITOR:-vi}" "$msg_file"
    git commit -F "$msg_file"
''', 'AI edit temp')

# Library mode makes permanent helper tests deterministic and bypasses signal/main side effects.
one('''trap "echo -e '${RED}Process interrupted. Exiting.${NC}'; exit 6" SIGINT SIGTERM

# Main script logic
''', '''if [[ "${GITX_LIBRARY_MODE:-0}" == 1 ]]; then
  return 0 2>/dev/null || exit 0
fi

trap "echo -e '${RED}Process interrupted. Exiting.${NC}'; exit 6" SIGINT SIGTERM

# Main script logic
''', 'library mode')

# Pass ai-commit options through.
one('ai-commit) generate_ai_commit ;;', 'ai-commit) generate_ai_commit "$@" ;;', 'AI dispatcher')
one('revert) revert_commit ;;', 'revert) revert_commit "$@" ;;', 'revert dispatcher')
one('cherry-pick) cherry_pick_commit ;;', 'cherry-pick) cherry_pick_commit "$@" ;;', 'cherry dispatcher')

# Final invariants for Phase 3.
if re.search(r'(^|\s)eval(\s|$)', t, flags=re.M):
    raise SystemExit('eval remains in gitx')
if re.search(r'/tmp/(gitx|git_(?:log|status))', t):
    raise SystemExit('predictable sensitive temp path remains in gitx')
if 'source "$GITX_CONFIG_FILE"' in t:
    raise SystemExit('Gemini settings source remains')

p.write_text(t)
