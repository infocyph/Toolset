#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p reports
report="reports/security-audit.txt"
: >"$report"

sources=(
  Git/gitx
  PHP/phpx
  Docker/dockex
  Network/netx
  Sqlite/sqlitex
  Clean/cleanx
  ChromaCat/chromacat
  install.sh
)

failed=0

section() {
  printf '\n## %s\n' "$1" | tee -a "$report"
}

must_be_absent() {
  local label="$1" regex="$2"
  section "$label"
  if grep -nE -- "$regex" "${sources[@]}" | tee -a "$report"; then
    printf 'BLOCKED: prohibited pattern found: %s\n' "$label" | tee -a "$report" >&2
    failed=1
  else
    printf 'none\n' | tee -a "$report"
  fi
}

must_be_present() {
  local label="$1" regex="$2" path="$3"
  section "$label"
  if grep -nE -- "$regex" "$path" | tee -a "$report"; then
    return 0
  fi
  printf 'BLOCKED: required release-safety pattern missing from %s\n' "$path" | tee -a "$report" >&2
  failed=1
}

report_only() {
  local label="$1" regex="$2"
  section "$label"
  grep -nE -- "$regex" "${sources[@]}" | tee -a "$report" || printf 'none\n' | tee -a "$report"
}

# Hard blockers after the 2.0 hardening pass.
must_be_absent 'Internal eval execution' '(^|[;[:space:]])eval[[:space:]]'
must_be_absent 'Writable config sourced as shell' '(^|[;[:space:]])(source|\.)[[:space:]]+[^#]*(config|settings|credentials)'
must_be_absent 'Raw curl piped to a shell' 'curl[^|\n]*\|[[:space:]]*(sudo[[:space:]]+)?(bash|sh)([[:space:]]|$)'
must_be_absent 'World-writable chmod' 'chmod[[:space:]]+(-[^[:space:]]+[[:space:]]+)*777([[:space:]]|$)'
must_be_absent 'Mutable Toolset raw main/master URL' 'raw\.githubusercontent\.com/infocyph/Toolset/(main|master)/'
must_be_absent 'Predictable shared sensitive temp file' '/tmp/\.?((git|net|toolset|phpx|dockex|sqlitex|cleanx|chromacat)[A-Za-z0-9._-]*\.(tmp|txt|json|lock|state))(["[:space:]]|$)'
must_be_absent 'Interpolated shell -c command string' '(bash|sh)[[:space:]]+-c[[:space:]]+"'

# Stable delivery must survive transient transport errors without depending on
# newer curl-only retry flags. These assertions keep the portable Bash retry
# boundary present in the installer and every built-in self-updater.
must_be_present 'Installer bounded release retry' '^download_with_retry\(\)' install.sh
for updater in Git/gitx PHP/phpx Clean/cleanx ChromaCat/chromacat; do
  must_be_present "Self-update bounded release retry: $updater" '^  toolset_download_with_retry\(\)' "$updater"
done

# Reviewed high-impact constructs are retained only where they serve the tool's
# explicit purpose. Keep them visible in the uploaded report for every CI run.
report_only 'Recursive deletion call sites' 'rm[[:space:]]+-[^\n]*r[^\n]*f|rm[[:space:]]+-rf'
report_only 'find deletion call sites' 'find[^\n]*-delete'
report_only 'Explicit bash/sh -c call sites' '(bash|sh)[[:space:]]+-c([[:space:]]|$)'
report_only 'sudo/root call sites' 'sudo|EUID|id -u'
report_only 'Network download call sites' 'curl|wget'
report_only 'Background process call sites' '(^|[[:space:]])[^#\n]+[[:space:]]&([[:space:]]|$)'
report_only 'Trap cleanup call sites' 'trap[[:space:]]'

if ((failed)); then
  exit 1
fi

printf '\nSecurity audit hard blockers: PASS\n' | tee -a "$report"
