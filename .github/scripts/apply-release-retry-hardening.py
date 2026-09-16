#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected exactly one replacement target, found {text.count(old)}")
    p.write_text(text.replace(old, new, 1))


install_old = '''CURL_ARGS=(
  --fail
  --location
  --silent
  --show-error
  --retry 3
  --connect-timeout 10
  --max-time 120
)

printf 'Fetching Toolset %s checksums...\\n' "$RELEASE_LABEL"
curl "${CURL_ARGS[@]}" \\
  "$BASE_URL/SHA256SUMS" \\
  --output "$TMP_DIR/SHA256SUMS"
'''
install_new = '''CURL_ARGS=(
  --fail
  --location
  --silent
  --show-error
  --connect-timeout 10
  --max-time 120
)

DOWNLOAD_ATTEMPTS="${TOOLSET_DOWNLOAD_ATTEMPTS:-4}"
[[ "$DOWNLOAD_ATTEMPTS" =~ ^[1-9][0-9]*$ ]] || {
  printf 'install.sh: TOOLSET_DOWNLOAD_ATTEMPTS must be a positive integer\\n' >&2
  exit 2
}

download_with_retry() {
  local url="$1" output="$2"
  local attempt rc=1

  for ((attempt = 1; attempt <= DOWNLOAD_ATTEMPTS; attempt++)); do
    if curl "${CURL_ARGS[@]}" "$url" --output "$output"; then
      return 0
    else
      rc=$?
    fi

    if ((attempt < DOWNLOAD_ATTEMPTS)); then
      printf 'install.sh: download failed (attempt %d/%d); retrying...\\n' \\
        "$attempt" "$DOWNLOAD_ATTEMPTS" >&2
      sleep "$attempt"
    fi
  done

  return "$rc"
}

printf 'Fetching Toolset %s checksums...\\n' "$RELEASE_LABEL"
download_with_retry \\
  "$BASE_URL/SHA256SUMS" \\
  "$TMP_DIR/SHA256SUMS"
'''
replace_once('install.sh', install_old, install_new)

replace_once(
    'install.sh',
    '''  curl "${CURL_ARGS[@]}" \\
    "$BASE_URL/$tool" \\
    --output "$TMP_DIR/$tool"
''',
    '''  download_with_retry \\
    "$BASE_URL/$tool" \\
    "$TMP_DIR/$tool"
'''
)

updater_old = '''  curl --fail --location --silent --show-error --retry 3 \\
    --connect-timeout 10 --max-time 120 \\
    "$base/SHA256SUMS" --output "$tmp_dir/SHA256SUMS"
  curl --fail --location --silent --show-error --retry 3 \\
    --connect-timeout 10 --max-time 120 \\
    "$base/install.sh" --output "$tmp_dir/install.sh"
'''
updater_new = '''  toolset_download_with_retry() {
    local url="$1" output="$2"
    local max_attempts="${TOOLSET_DOWNLOAD_ATTEMPTS:-4}"
    local attempt rc=1

    [[ "$max_attempts" =~ ^[1-9][0-9]*$ ]] || {
      printf '%s: TOOLSET_DOWNLOAD_ATTEMPTS must be a positive integer\\n' "$tool" >&2
      return 2
    }

    for ((attempt = 1; attempt <= max_attempts; attempt++)); do
      if curl --fail --location --silent --show-error \\
        --connect-timeout 10 --max-time 120 \\
        "$url" --output "$output"; then
        return 0
      else
        rc=$?
      fi

      if ((attempt < max_attempts)); then
        printf '%s: download failed (attempt %d/%d); retrying...\\n' \\
          "$tool" "$attempt" "$max_attempts" >&2
        sleep "$attempt"
      fi
    done

    return "$rc"
  }

  toolset_download_with_retry "$base/SHA256SUMS" "$tmp_dir/SHA256SUMS"
  toolset_download_with_retry "$base/install.sh" "$tmp_dir/install.sh"
'''

for path in ['Git/gitx', 'PHP/phpx', 'Clean/cleanx', 'ChromaCat/chromacat']:
    replace_once(path, updater_old, updater_new)

# Remove this transformer after it has done its one-shot job.
Path('.github/scripts/apply-release-retry-hardening.py').unlink()
Path('.github/workflows/apply-release-retry-hardening.yml').unlink()
