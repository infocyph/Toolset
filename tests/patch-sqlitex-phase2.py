#!/usr/bin/env python3
from pathlib import Path
import re

path = Path('Sqlite/sqlitex')
text = path.read_text()


def replace_section(start: str, end: str, body: str) -> None:
    global text
    pat = re.escape(start) + r'.*?' + re.escape(end)
    repl = start + '\n' + body.rstrip() + '\n\n' + end
    out, count = re.subn(pat, repl, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'failed replacing {start!r}')
    text = out

text = text.replace('USE_LOCK="false"\nBUSY_TIMEOUT_MS=5000 # Used when --use-lock is enabled\n', 'USE_BUSY_TIMEOUT="false"\nBUSY_TIMEOUT_MS=5000\n', 1)

replace_section(
    '# ===========================================\n# Environment Checks & Utilities\n# ===========================================',
    '# ===========================================\n# Timing Helpers\n# ===========================================',
    r'''ensure_sqlite() { command -v sqlite3 >/dev/null 2>&1 || log_error "sqlite3 is required."; }
ensure_jq() { command -v jq >/dev/null 2>&1 || log_error "jq is required for JSON seeding."; }
ensure_db_exists() { [[ ! -f "$DB" ]] && log_error "Database '$DB' does not exist. Use 'create-db' first."; }

validate_identifier() {
  [[ "${1:-}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || log_error "Unsafe SQL identifier: ${1:-<empty>}"
}

quote_identifier() {
  validate_identifier "$1"
  printf '"%s"' "$1"
}

sql_literal() {
  local value="$1"
  value=${value//\'/\'\'}
  printf "'%s'" "$value"
}

human_size() {
  local bytes=$1 unit=B value=$bytes
  if ((bytes >= 1099511627776)); then unit=TB; value=$((bytes / 1099511627776));
  elif ((bytes >= 1073741824)); then unit=GB; value=$((bytes / 1073741824));
  elif ((bytes >= 1048576)); then unit=MB; value=$((bytes / 1048576));
  elif ((bytes >= 1024)); then unit=KB; value=$((bytes / 1024)); fi
  echo "${value}${unit}"
}

sqlite_invoke() {
  local -a args=()
  if [[ "$USE_BUSY_TIMEOUT" == true ]]; then args+=(-cmd ".timeout $BUSY_TIMEOUT_MS"); fi
  sqlite3 "${args[@]}" "$DB" "$@"
}

integrity_ok() {
  [[ "$(sqlite_invoke 'PRAGMA integrity_check;' 2>/dev/null)" == ok ]]
}

backup_db() {
  local base ts file escaped
  base=$(basename "${DB%.db}")
  ts=$(date +%Y%m%d_%H%M%S_%N)
  file="$BACKUP_DIR/${base}_${ts}.db"
  if is_dry_run; then
    log_info "DRY-RUN: would create SQLite-consistent backup at: $file"
    return 0
  fi
  mkdir -p -- "$BACKUP_DIR"
  escaped=${file//\'/\'\'}
  sqlite_invoke ".backup '$escaped'" || log_error "SQLite backup failed."
  [[ -s "$file" ]] || log_error "SQLite backup is empty: $file"
  [[ "$(sqlite3 "$file" 'PRAGMA integrity_check;' 2>/dev/null)" == ok ]] || log_error "Backup integrity check failed: $file"
  log_info "Backup created at: $file"
}''')

replace_section(
    '# ===========================================\n# SQL Execution Helpers (with optional timeout)\n# ===========================================',
    '# ===========================================\n# JSON/CSV Import Helpers\n# ===========================================',
    r'''run_sql() { sqlite_invoke "$1"; }
run_sql_file() {
  local file="$1" args=()
  [[ "$USE_BUSY_TIMEOUT" == true ]] && args=(-cmd ".timeout $BUSY_TIMEOUT_MS")
  sqlite3 "${args[@]}" "$DB" <"$file"
}

execute_sql_mutating() {
  local sql="$1"
  if is_dry_run; then log_info "DRY-RUN SQL: $sql"; else run_sql "$sql"; fi
}

execute_file_mutating() {
  local file="$1"
  if is_dry_run; then log_info "DRY-RUN FILE: $file"; else run_sql_file "$file"; fi
}

run_transaction_with_file() {
  local file="$1" trailing_sql="$2"
  if is_dry_run; then
    log_info "DRY-RUN TRANSACTION FILE: $file"
    log_info "DRY-RUN TRANSACTION SQL: $trailing_sql"
    return 0
  fi
  local -a args=()
  [[ "$USE_BUSY_TIMEOUT" == true ]] && args=(-cmd ".timeout $BUSY_TIMEOUT_MS")
  {
    printf 'BEGIN IMMEDIATE;\n'
    cat -- "$file"
    printf '\n%s\nCOMMIT;\n' "$trailing_sql"
  } | sqlite3 "${args[@]}" "$DB"
}''')

replace_section(
    '# ===========================================\n# JSON/CSV Import Helpers\n# ===========================================',
    '# ===========================================\n# Migration Functions\n# ===========================================',
    r'''detect_columns() {
  local table="$1" qtable
  qtable="$(quote_identifier "$table")"
  sqlite_invoke "PRAGMA table_info($qtable);" | awk -F'|' '{print $2}'
}

import_csv() {
  local file="$1" table="$2" skip_header="${3:-1}"
  validate_identifier "$table"
  [[ -f "$file" ]] || log_error "CSV seed not found: $file"
  if is_dry_run; then log_info "DRY-RUN: would import CSV '$file' into table '$table' (header-skip=$skip_header)"; return 0; fi
  local tmp
  tmp=$(mktemp) || log_error "Unable to allocate CSV import temp file."
  trap 'rm -f -- "$tmp"' RETURN
  cp -- "$file" "$tmp"
  if [[ "$skip_header" == 1 ]]; then
    sqlite_invoke <<EOF
.mode csv
.import --skip 1 "$tmp" "$table"
EOF
  else
    sqlite_invoke <<EOF
.mode csv
.import "$tmp" "$table"
EOF
  fi
}

import_json() {
  local file="$1" table="$2"
  ensure_jq
  validate_identifier "$table"
  [[ -f "$file" ]] || log_error "JSON seed not found: $file"
  jq -e 'type == "array" and all(.[]; type == "object")' "$file" >/dev/null || log_error "JSON seed must be an array of objects."
  if is_dry_run; then log_info "DRY-RUN: would import JSON '$file' into table '$table' preserving JSON null as SQL NULL"; return 0; fi
  [[ "$(sqlite_invoke "SELECT json_valid('[]');" 2>/dev/null)" == 1 ]] || log_error "SQLite JSON functions are required for JSON import."
  [[ "$(jq 'length' "$file")" != 0 ]] || return 0

  local -a keys=() actual=()
  mapfile -t keys < <(jq -r '[.[] | keys[]] | unique[]' "$file")
  mapfile -t actual < <(detect_columns "$table")
  ((${#keys[@]})) || return 0
  local key found columns='' expressions='' sep='' qtable path_literal file_abs file_literal
  for key in "${keys[@]}"; do
    validate_identifier "$key"
    found=0
    local col
    for col in "${actual[@]}"; do [[ "$col" == "$key" ]] && found=1 && break; done
    ((found)) || log_error "JSON key '$key' is not a column in table '$table'."
    columns+="$sep\"$key\""
    path_literal="$(sql_literal "$.${key}")"
    expressions+="$sep json_extract(value, $path_literal)"
    sep=','
  done
  qtable="$(quote_identifier "$table")"
  file_abs="$(cd -- "$(dirname -- "$file")" && pwd)/$(basename -- "$file")"
  file_literal="$(sql_literal "$file_abs")"
  sqlite_invoke "INSERT INTO $qtable ($columns) SELECT $expressions FROM json_each(CAST(readfile($file_literal) AS TEXT));"
}''')

replace_section(
    '# ===========================================\n# Migration Functions\n# ===========================================',
    '# ===========================================\n# Seed Function\n# ===========================================',
    r'''ensure_migration_table() {
  if is_dry_run; then return 0; fi
  sqlite_invoke "CREATE TABLE IF NOT EXISTS $MIG_TABLE (
    migration_file TEXT NOT NULL UNIQUE,
    sequence INTEGER,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
  );"
  local has_sequence
  has_sequence=$(sqlite_invoke "PRAGMA table_info($MIG_TABLE);" | awk -F'|' '$2=="sequence"{print 1}')
  if [[ -z "$has_sequence" ]]; then sqlite_invoke "ALTER TABLE $MIG_TABLE ADD COLUMN sequence INTEGER;"; fi
  sqlite_invoke "UPDATE $MIG_TABLE SET sequence=rowid WHERE sequence IS NULL;"
  sqlite_invoke "CREATE UNIQUE INDEX IF NOT EXISTS ${MIG_TABLE}_sequence_uq ON $MIG_TABLE(sequence);"
}

migrate_up() {
  ensure_db_exists
  ensure_migration_table
  local applied='' file name safe_name applied_any=false next_sequence=1
  if ! is_dry_run && [[ "$(sqlite_invoke "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=$(sql_literal "$MIG_TABLE");")" != 0 ]]; then
    applied=$(sqlite_invoke "SELECT migration_file FROM $MIG_TABLE;")
    next_sequence=$(sqlite_invoke "SELECT COALESCE(MAX(sequence),0)+1 FROM $MIG_TABLE;")
  fi
  local -a files=()
  if [[ -d "$MIGRATIONS_PATH" ]]; then mapfile -d '' -t files < <(find "$MIGRATIONS_PATH" -maxdepth 1 -type f -name '*.sql' ! -name '*.down.sql' -print0 | sort -z); fi
  for file in "${files[@]}"; do
    name=$(basename -- "$file")
    grep -Fxq "$name" <<<"$applied" && continue
    applied_any=true
    safe_name="$(sql_literal "$name")"
    log_info "Applying migration: $name"
    run_transaction_with_file "$file" "INSERT INTO $MIG_TABLE(migration_file,sequence) VALUES($safe_name,$next_sequence);" || log_error "Migration failed and was rolled back: $name"
    applied+=$'\n'"$name"
    next_sequence=$((next_sequence + 1))
    log_success "Migrated: $name"
  done
  [[ "$applied_any" == false ]] && log_info "No new migrations to apply."
}

rollback_migration() {
  ensure_db_exists
  ensure_migration_table
  if is_dry_run; then
    log_info "DRY-RUN: would rollback the most recently sequenced migration."
    return 0
  fi
  local last down_file safe_last
  last=$(sqlite_invoke "SELECT migration_file FROM $MIG_TABLE ORDER BY sequence DESC LIMIT 1;")
  [[ -z "$last" ]] && { log_info "No migrations to rollback."; return 0; }
  down_file="$MIGRATIONS_PATH/${last%.sql}.down.sql"
  [[ -f "$down_file" ]] || log_error "Down script not found: $down_file"
  safe_last="$(sql_literal "$last")"
  log_info "Rolling back: $last"
  run_transaction_with_file "$down_file" "DELETE FROM $MIG_TABLE WHERE migration_file=$safe_last;" || log_error "Rollback failed; migration history was preserved."
  log_success "Rolled back: $last"
}''')

# Reset removes SQLite sidecars and recreates through SQLite itself.
replace_section(
    '# ===========================================\n# Reset Database (migrate + seed)\n# ===========================================',
    '# ===========================================\n# Schema Inspection\n# ===========================================',
    r'''reset_db() {
  ensure_db_exists
  if is_dry_run; then log_info "DRY-RUN: would backup and reset '$DB', including WAL/SHM sidecars, then migrate and seed."; return 0; fi
  backup_db
  rm -f -- "$DB" "${DB}-wal" "${DB}-shm" "${DB}-journal"
  sqlite3 "$DB" '' || log_error "Failed to recreate database: $DB"
  log_success "Database reset: $DB"
  migrate_up
  seed_all
}''')

# Identifier safety on schema/select/update/delete and consistent export files.
text = text.replace('show_schema() {\n  ensure_db_exists\n  sqlite3 "$DB" ".schema $1"\n}', 'show_schema() {\n  ensure_db_exists\n  validate_identifier "$1"\n  sqlite3 "$DB" ".schema $1"\n}', 1)
replace_section(
    '# ===========================================\n# Record Operations\n# ===========================================',
    '# ===========================================\n# Command Implementations (cmd_*)\n# ===========================================',
    r'''select_records() {
  local table="$1" where_clause="${2:-1=1}" export_fmt="${3:-}" qtable
  ensure_db_exists; qtable="$(quote_identifier "$table")"; timer_start
  if [[ -n "$export_fmt" ]]; then
    [[ "$export_fmt" == csv || "$export_fmt" == json ]] || log_error "select: --export must be csv or json"
    local f="$EXPORT_DIR/${table}_$(date +%Y%m%d_%H%M%S).${export_fmt}"
    if is_dry_run; then log_info "DRY-RUN: would export $table as $export_fmt to $f"; timer_end; return 0; fi
    mkdir -p -- "$EXPORT_DIR"
    if [[ "$export_fmt" == csv ]]; then sqlite3 -header -csv "$DB" "SELECT * FROM $qtable WHERE $where_clause;" >"$f"; else sqlite3 -json "$DB" "SELECT * FROM $qtable WHERE $where_clause;" >"$f"; fi
    log_success "Exported ${export_fmt^^}: $f"
  else
    sqlite3 -header -column "$DB" "SELECT * FROM $qtable WHERE $where_clause;"
  fi
  timer_end
}

update_record() {
  local table="$1" set_clause="$2" where_clause="$3" qtable
  ensure_db_exists; qtable="$(quote_identifier "$table")"
  is_dry_run || backup_db
  timer_start; execute_sql_mutating "UPDATE $qtable SET $set_clause WHERE $where_clause"; timer_end
  log_success "Updated table: $table"
}

delete_record() {
  local table="$1" where_clause="$2" qtable
  ensure_db_exists; qtable="$(quote_identifier "$table")"
  is_dry_run || backup_db
  timer_start; execute_sql_mutating "DELETE FROM $qtable WHERE $where_clause"; timer_end
  log_success "Deleted from: $table"
}''')

# Create table/insert/sample table names must be validated before interpolation.
text = text.replace('  [[ -z $table || -z $cols ]] && usage\n  ensure_db_exists\n  execute_sql_mutating "CREATE TABLE IF NOT EXISTS $table ($cols)"', '  [[ -z $table || -z $cols ]] && usage\n  validate_identifier "$table"\n  ensure_db_exists\n  execute_sql_mutating "CREATE TABLE IF NOT EXISTS \"$table\" ($cols)"', 1)
text = text.replace('  [[ -z $table || -z $vals ]] && usage\n  ensure_db_exists\n  execute_sql_mutating "INSERT INTO $table VALUES ($vals)"', '  [[ -z $table || -z $vals ]] && usage\n  validate_identifier "$table"\n  ensure_db_exists\n  execute_sql_mutating "INSERT INTO \"$table\" VALUES ($vals)"', 1)
text = text.replace('  sqlite3 -header -column "$DB" "SELECT * FROM $table LIMIT $limit;"', '  validate_identifier "$table"\n  [[ "$limit" =~ ^[1-9][0-9]*$ ]] || log_error "sample: --limit must be a positive integer"\n  sqlite3 -header -column "$DB" "SELECT * FROM \"$table\" LIMIT $limit;"', 1)

# create-db and migration/export directory creation must be dry-run side-effect free.
text = text.replace('cmd_create_db() {\n  mkdir -p "$(dirname "$DB")"\n  if is_dry_run; then', 'cmd_create_db() {\n  if is_dry_run; then', 1)
text = text.replace('    return 0\n  fi\n  sqlite3 "$DB" "" &&', '    return 0\n  fi\n  mkdir -p -- "$(dirname "$DB")"\n  sqlite3 "$DB" "" &&', 1)
text = text.replace('  mkdir -p "$MIGRATIONS_PATH"\n  up_file=', '  up_file=', 1)
text = text.replace('    return 0\n  fi\n\n  cat >"$up_file"', '    return 0\n  fi\n\n  mkdir -p -- "$MIGRATIONS_PATH"\n  cat >"$up_file"', 1)
text = text.replace('  ensure_db_exists\n  mkdir -p "$EXPORT_DIR"\n\n  case "$format"', '  ensure_db_exists\n\n  case "$format"', 1)
text = text.replace('  local tables\n  tables=', '  is_dry_run || mkdir -p -- "$EXPORT_DIR"\n\n  local tables\n  tables=', 1)

# Optimize/tune use backup + pre/post integrity, while dry-run remains pure.
replace_section(
    'cmd_optimize() {',
    'cmd_migrate_create() {',
    r'''cmd_optimize() {
  ensure_db_exists
  if is_dry_run; then log_info "DRY-RUN: would integrity-check, backup, VACUUM, ANALYZE, PRAGMA optimize, then integrity-check again."; return 0; fi
  integrity_ok || log_error "Pre-optimization integrity check failed."
  backup_db
  log_info "Running VACUUM; ANALYZE; PRAGMA optimize; ..."
  timer_start
  run_sql "VACUUM; ANALYZE; PRAGMA optimize;"
  timer_end
  integrity_ok || log_error "Post-optimization integrity check failed. Restore the backup."
  log_success "Optimization complete."
}

cmd_migrate_create() {''')
# The replacement includes the end function marker text; clean double marker if produced.
text = text.replace('cmd_migrate_create() {\n\ncmd_migrate_create() {', 'cmd_migrate_create() {', 1)

replace_section(
    'cmd_tune() {',
    '# ===========================================\n# Usage & Dispatcher\n# ===========================================',
    r'''cmd_tune() {
  local profile="safe"
  while [[ $# -gt 0 ]]; do
    case "$1" in --profile) profile="$2"; shift 2 ;; *) log_error "tune: unknown option $1" ;; esac
  done
  case "$profile" in dev|prod|safe) ;; *) log_error "tune: unknown profile '$profile' (use dev|prod|safe)" ;; esac
  ensure_db_exists
  if is_dry_run; then log_info "DRY-RUN: would integrity-check, backup, and apply '$profile' PRAGMAs."; return 0; fi
  integrity_ok || log_error "Pre-tune integrity check failed."
  backup_db
  case "$profile" in
    dev) run_sql "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA foreign_keys=ON; PRAGMA temp_store=MEMORY;" ;;
    prod) run_sql "PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;" ;;
    safe) run_sql "PRAGMA foreign_keys=ON;" ;;
  esac
  integrity_ok || log_error "Post-tune integrity check failed. Restore the backup."
  log_success "Tuning complete."
}''')

# Clarify busy-timeout CLI while retaining a compatibility alias.
text = text.replace('  --use-lock                  Enable timeout-based lock handling (.timeout ${BUSY_TIMEOUT_MS}ms)\n', '  --busy-timeout <ms>         Set SQLite busy timeout for lock contention (default when enabled: ${BUSY_TIMEOUT_MS}ms)\n  --use-lock                  Deprecated alias for --busy-timeout ${BUSY_TIMEOUT_MS}\n', 1)
text = text.replace('  --use-lock)\n    USE_LOCK="true"\n    shift\n    ;;', '  --busy-timeout)\n    [[ "${2:-}" =~ ^[0-9]+$ ]] || log_error "--busy-timeout requires a non-negative integer in milliseconds."\n    BUSY_TIMEOUT_MS="$2"\n    USE_BUSY_TIMEOUT="true"\n    shift 2\n    ;;\n  --use-lock)\n    USE_BUSY_TIMEOUT="true"\n    log_warn "--use-lock is deprecated; use --busy-timeout $BUSY_TIMEOUT_MS."\n    shift\n    ;;', 1)

# Library mode for direct helper tests.
marker = 'case "${1:-}" in\n-h | --help | help)'
text = text.replace(marker, 'if [[ "${SQLITEX_LIBRARY_MODE:-0}" == "1" ]]; then\n  return 0 2>/dev/null || exit 0\nfi\n\n' + marker, 1)

path.write_text(text)
