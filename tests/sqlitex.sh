#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
# shellcheck source=tests/lib/assert.sh
source tests/lib/assert.sh

command -v sqlite3 >/dev/null 2>&1 || { echo 'SKIP: sqlite3 unavailable'; exit 0; }
command -v jq >/dev/null 2>&1 || { echo 'SKIP: jq unavailable'; exit 0; }

TMP_ROOT="$(mktemp -d)"
WAL_HOLDER=""
cleanup() {
  if [[ -n "$WAL_HOLDER" ]]; then kill "$WAL_HOLDER" 2>/dev/null || true; wait "$WAL_HOLDER" 2>/dev/null || true; fi
  rm -rf -- "$TMP_ROOT"
}
trap cleanup EXIT INT TERM

export SQLITEX_LIBRARY_MODE=1
# shellcheck source=Sqlite/sqlitex
source Sqlite/sqlitex
unset SQLITEX_LIBRARY_MODE

DB="$TMP_ROOT/app.db"
BACKUP_DIR="$TMP_ROOT/backups"
EXPORT_DIR="$TMP_ROOT/exports"
MIGRATIONS_PATH="$TMP_ROOT/migrations"
SEEDS_PATH="$TMP_ROOT/seeds"
ENV=test
MIG_TABLE=migrations_test
DRY_RUN=false
USE_BUSY_TIMEOUT=true
BUSY_TIMEOUT_MS=2500
mkdir -p "$MIGRATIONS_PATH" "$SEEDS_PATH"
sqlite3 "$DB" 'CREATE TABLE base(id INTEGER PRIMARY KEY, value TEXT); INSERT INTO base(value) VALUES("seed");'

# Native backup must include committed WAL content while a writer connection remains open.
ready="$TMP_ROOT/wal-ready"
python3 - "$DB" "$ready" <<'PY' &
import sqlite3, sys, time
conn = sqlite3.connect(sys.argv[1])
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('CREATE TABLE IF NOT EXISTS wal_data(id INTEGER PRIMARY KEY, value TEXT)')
conn.execute('INSERT INTO wal_data(value) VALUES (?)', ('from-wal',))
conn.commit()
open(sys.argv[2], 'w').close()
time.sleep(30)
PY
WAL_HOLDER=$!
for _ in {1..50}; do [[ -e "$ready" ]] && break; sleep 0.1; done
[[ -e "$ready" ]] || fail 'WAL writer did not initialize'
[[ -e "${DB}-wal" ]] || fail 'WAL sidecar was not present for consistency test'
backup_db >/dev/null
backup_file="$(find "$BACKUP_DIR" -type f -name '*.db' -print | sort | tail -n1)"
[[ -s "$backup_file" ]] || fail 'SQLite-native backup file missing'
assert_eq 'from-wal' "$(sqlite3 "$backup_file" 'SELECT value FROM wal_data ORDER BY id DESC LIMIT 1;')" 'backup should include committed WAL data'
assert_eq 'ok' "$(sqlite3 "$backup_file" 'PRAGMA integrity_check;')" 'backup integrity'
pass 'SQLite-native backup captures committed WAL state consistently'
kill "$WAL_HOLDER" 2>/dev/null || true; wait "$WAL_HOLDER" 2>/dev/null || true; WAL_HOLDER=""

# Migrations are filename-ordered and SQL+history are one transaction.
cat >"$MIGRATIONS_PATH/001_first.sql" <<'SQL'
CREATE TABLE first_table(id INTEGER PRIMARY KEY, value TEXT);
INSERT INTO first_table(value) VALUES('first');
SQL
cat >"$MIGRATIONS_PATH/001_first.down.sql" <<'SQL'
DROP TABLE first_table;
SQL
cat >"$MIGRATIONS_PATH/002_second.sql" <<'SQL'
CREATE TABLE should_rollback(id INTEGER PRIMARY KEY);
INSERT INTO definitely_missing_table(value) VALUES('boom');
SQL
cat >"$MIGRATIONS_PATH/002_second.down.sql" <<'SQL'
DROP TABLE second_table;
SQL

set +e
(migrate_up) >/dev/null 2>&1
migration_rc=$?
set -e
((migration_rc != 0)) || fail 'failing migration unexpectedly succeeded'
assert_eq '1' "$(sqlite3 "$DB" "SELECT COUNT(*) FROM $MIG_TABLE;")" 'only first migration should be tracked'
assert_eq '001_first.sql|1' "$(sqlite3 "$DB" "SELECT migration_file||'|'||sequence FROM $MIG_TABLE;")" 'deterministic migration sequence'
assert_eq '0' "$(sqlite3 "$DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='should_rollback';")" 'failed migration DDL should roll back'
pass 'migration failure rolls back schema and history together'

cat >"$MIGRATIONS_PATH/002_second.sql" <<'SQL'
CREATE TABLE second_table(id INTEGER PRIMARY KEY, value TEXT);
INSERT INTO second_table(value) VALUES('second');
SQL
migrate_up >/dev/null
assert_eq $'001_first.sql|1\n002_second.sql|2' "$(sqlite3 "$DB" "SELECT migration_file||'|'||sequence FROM $MIG_TABLE ORDER BY sequence;")" 'migration ordering after retry'
rollback_migration >/dev/null
assert_eq '0' "$(sqlite3 "$DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='second_table';")" 'latest migration rollback'
assert_eq '001_first.sql|1' "$(sqlite3 "$DB" "SELECT migration_file||'|'||sequence FROM $MIG_TABLE;")" 'rollback history sequence'
pass 'rollback uses deterministic migration sequence and transaction'

# CSV header is skipped; JSON null remains SQL NULL.
sqlite3 "$DB" 'CREATE TABLE csv_items(id INTEGER, name TEXT); CREATE TABLE json_items(id INTEGER, name TEXT);'
printf 'id,name\n1,Alice\n' >"$TMP_ROOT/items.csv"
import_csv "$TMP_ROOT/items.csv" csv_items
assert_eq '1|Alice' "$(sqlite3 "$DB" 'SELECT id||"|"||name FROM csv_items;')" 'CSV header-aware import'
printf '[{"id":1,"name":null}]\n' >"$TMP_ROOT/items.json"
import_json "$TMP_ROOT/items.json" json_items
assert_eq '1|1' "$(sqlite3 "$DB" 'SELECT id||"|"||(name IS NULL) FROM json_items;')" 'JSON null preservation'
pass 'CSV headers and JSON null values import correctly'

# Table identifiers are structural, not arbitrary SQL fragments.
set +e
(validate_identifier 'json_items;DROP_TABLE') >/dev/null 2>&1
identifier_rc=$?
set -e
((identifier_rc != 0)) || fail 'unsafe identifier was accepted'
validate_identifier json_items
pass 'table identifier validation rejects SQL fragments'

# CSV and JSON select exports have the same file-output contract.
select_records json_items '1=1' csv >/dev/null
select_records json_items '1=1' json >/dev/null
[[ -n "$(find "$EXPORT_DIR" -maxdepth 1 -name 'json_items_*.csv' -print -quit)" ]] || fail 'CSV select export missing'
[[ -n "$(find "$EXPORT_DIR" -maxdepth 1 -name 'json_items_*.json' -print -quit)" ]] || fail 'JSON select export missing'
pass 'select export semantics are consistent across CSV and JSON'

# Dry-run must not create output directories, backups, exports or migration files.
DRY_RUN=true
DRY_BACKUP="$TMP_ROOT/dry-backups"
DRY_EXPORT="$TMP_ROOT/dry-exports"
DRY_MIG="$TMP_ROOT/dry-migrations"
BACKUP_DIR="$DRY_BACKUP"; EXPORT_DIR="$DRY_EXPORT"; MIGRATIONS_PATH="$DRY_MIG"
backup_db >/dev/null
select_records json_items '1=1' json >/dev/null
cmd_migrate_create --name dry_test >/dev/null
[[ ! -e "$DRY_BACKUP" && ! -e "$DRY_EXPORT" && ! -e "$DRY_MIG" ]] || fail 'dry-run created filesystem outputs'
pass 'dry-run is filesystem side-effect-free for backup/export/migration-create'
DRY_RUN=false
BACKUP_DIR="$TMP_ROOT/backups"; EXPORT_DIR="$TMP_ROOT/exports"; MIGRATIONS_PATH="$TMP_ROOT/migrations"

# Reset removes SQLite sidecars and leaves a valid database rebuilt from migrations/seeds.
sqlite3 "$DB" 'PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS reset_marker(id INTEGER);' >/dev/null
reset_db >/dev/null
[[ ! -e "${DB}-wal" && ! -e "${DB}-shm" && ! -e "${DB}-journal" ]] || fail 'reset left SQLite sidecars behind'
assert_eq 'ok' "$(sqlite3 "$DB" 'PRAGMA integrity_check;')" 'reset database integrity'
assert_eq '1' "$(sqlite3 "$DB" "SELECT COUNT(*) FROM $MIG_TABLE WHERE migration_file='001_first.sql';")" 'reset reapplied migrations'
pass 'reset is sidecar-aware and rebuilds a valid database'

# Optimize/tune both protect the database with integrity-checked backups.
backup_count_before="$(find "$BACKUP_DIR" -type f -name '*.db' | wc -l)"
cmd_optimize >/dev/null
cmd_tune --profile safe >/dev/null
backup_count_after="$(find "$BACKUP_DIR" -type f -name '*.db' | wc -l)"
((backup_count_after >= backup_count_before + 2)) || fail 'optimize/tune did not create protective backups'
assert_eq 'ok' "$(sqlite3 "$DB" 'PRAGMA integrity_check;')" 'post optimize/tune integrity'
pass 'optimize and tune are backup/integrity guarded'

printf '\nAll sqlitex disposable consistency checks passed.\n'
