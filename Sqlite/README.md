# sqlitex

`sqlitex` is a non-interactive, flag-based SQLite CLI:

- CRUD operations
- migrations + seeds
- backup/reset helpers
- CSV/JSON export
- DB info / health checks / optimization
- dry-run mode for safe mutations
- simple tuning, explaining and sampling

It’s ideal for scripts and CI where you want explicit flags instead of interactive shells.

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Sqlite/sqlitex" \
  -o /usr/local/bin/sqlitex && sudo chmod +x /usr/local/bin/sqlitex
````

## Usage

Global options must come **before** the command:

```bash
sqlitex [global options] <command> [command options]
```

### Global Options

| Option                     | Description                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| `--db <file>`              | **(required)** SQLite database file                                                               |
| `--env <env>`              | Environment name (default: `default`) — affects migration table name & optional subdir resolution |
| `--migrations-path <path>` | Migrations directory (default: `./migrations` or `./migrations/<env>` if that subdir exists)      |
| `--seeds-path <path>`      | Seeds directory (default: `./seeds` or `./seeds/<env>` if that subdir exists)                     |
| `--backup-path <path>`     | Backup directory (default: `./db_backups`)                                                        |
| `--export-path <path>`     | Export directory (default: `./exports`)                                                           |
| `--use-lock`               | Enable timeout-based lock handling (`.timeout 5000` ms) for sqlite3 CLI                           |
| `--dry-run`                | Print SQL / actions for mutating operations without applying changes or touching the DB           |

> ℹ️ `--env` is also used in the migration tracking table name: `migrations_<ENV_SAFE>`.

---

## Commands Overview

### Core CRUD & Schema

| Command                                                         | Description                         |
| --------------------------------------------------------------- | ----------------------------------- |
| `create-db`                                                     | Create a new SQLite database file   |
| `create-table --table <name> --columns "<col_defs>"`            | Create table if not exists          |
| `insert --table <name> --values "<vals>"`                       | Insert a single record              |
| `insert-batch --file <sql_file>`                                | Execute a SQL file of inserts / DML |
| `select --table <name> [--where "<cond>"] [--export csv\|json]` | Query rows (pretty/CSV/JSON)        |
| `update --table <name> --set "<set>" --where "<cond>"`          | Update rows (with backup)           |
| `delete --table <name> --where "<cond>"`                        | Delete rows (with backup)           |
| `schema --table <name>`                                         | Show table schema                   |
| `sample --table <name> [--limit N]`                             | Show first N rows from a table      |
| `exec [--sql "<statement>"] [--file <sql_file>]`                | Execute arbitrary SQL or a SQL file |

### Migrations & Seeds

| Command                                  | Description                                                           |
| ---------------------------------------- | --------------------------------------------------------------------- |
| `migrate [--rollback]`                   | Apply pending migrations or roll back the last applied migration      |
| `migrate-create <name> \| --name <name>` | Generate up/down migration skeleton files in the migrations directory |
| `seed`                                   | Import seed files (SQL, CSV, JSON)                                    |
| `reset`                                  | Backup → drop & recreate → migrate → seed                             |

### Backup, Export & Dump

| Command                           | Description                                           |
| --------------------------------- | ----------------------------------------------------- |
| `backup`                          | Create a timestamped backup copy of the database file |
| `dump [--file <dump.sql>]`        | Dump full schema + data to stdout or a file           |
| `export-all [--format csv\|json]` | Export all tables to CSV/JSON files in `EXPORT_DIR`   |

### Inspection, Health & Optimization

| Command                            | Description                                                     |
| ---------------------------------- | --------------------------------------------------------------- |
| `tables`                           | List all user tables                                            |
| `info`                             | Show database info (size, journal mode, tables, etc.)           |
| `doctor`                           | Run integrity & foreign-key checks + basic environment warnings |
| `optimize`                         | Backup then run `VACUUM;`, `ANALYZE;` and `PRAGMA optimize;`    |
| `explain --sql "<query>"`          | Show `EXPLAIN QUERY PLAN` for a SELECT query                    |
| `tune [--profile dev\|prod\|safe]` | Apply simple pragma profiles (journal_mode, sync, FKs, etc.)    |

> 🔒 **Mutating commands** (`create-db`, `create-table`, `insert`, `insert-batch`, `update`, `delete`, `migrate`, `migrate-create`, `seed`, `reset`, `exec` with DML/DDL, `backup`, `dump --file`, `optimize`, `tune`, `export-all` writing files) all honor `--dry-run` and will only print what they would do.

---

## Command Details & Examples

### create-db

Create a new SQLite database file (and parent directory if needed).

```bash
sqlitex --db my.db create-db
```

With dry-run:

```bash
sqlitex --db my.db --dry-run create-db
# prints intent, does not create file
```

---

### create-table

Create a table if it doesn’t already exist.

```bash
sqlitex --db my.db create-table \
  --table users \
  --columns "id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE"
```

---

### insert

Insert a single row using a raw `VALUES (...)` clause.

```bash
sqlitex --db my.db insert \
  --table users \
  --values "NULL,'Alice','alice@example.com'"
```

---

### insert-batch

Execute a SQL file containing multiple statements (inserts / DML / DDL).

```bash
sqlitex --db my.db insert-batch --file seeds/users.sql
```

With dry-run, it only prints the file that would be executed.

---

### select

Query data and print as a table, CSV or JSON.

```bash
# Pretty-print with headers
sqlitex --db my.db select --table users --where "id > 5"

# Export result to CSV
sqlitex --db my.db select \
  --table users \
  --where "id > 5" \
  --export csv

# Export result to JSON (requires sqlite3 with -json support)
sqlitex --db my.db select \
  --table users \
  --where "email LIKE '%@example.com'" \
  --export json
```

CSV/JSON files are stored in `--export-path` (default: `./exports`).

---

### update

Update rows; a backup is taken before the change (unless `--dry-run`).

```bash
sqlitex --db my.db update \
  --table users \
  --set "name='Bob'" \
  --where "id=1"
```

With `--dry-run`, sqlitex prints the `UPDATE` query instead of executing it.

---

### delete

Delete rows; a backup is taken before the change (unless `--dry-run`).

```bash
sqlitex --db my.db delete \
  --table users \
  --where "last_login IS NULL"
```

---

### schema

Show `CREATE TABLE` definition.

```bash
sqlitex --db my.db schema --table users
```

---

### sample

Show the first N rows from a table.

```bash
# First 10 rows (default)
sqlitex --db my.db sample --table users

# First 3 rows
sqlitex --db my.db sample --table users --limit 3
```

---

### exec

Run arbitrary SQL or a SQL file.

```bash
# Single statement
sqlitex --db my.db exec --sql "VACUUM;"

# Multi-statement script
sqlitex --db my.db exec --file scripts/maintenance.sql
```

> Note: With `--dry-run`, the SQL or file path is printed instead of executed.

---

### tables

List all user tables (excluding internal `sqlite_` tables):

```bash
sqlitex --db my.db tables
```

---

### Migrations

Migrations are simple `.sql` files in the migrations directory.

* **Up** migrations: `*.sql`
* **Down** migrations: matching `*.down.sql`

Applied migrations are tracked in a table named `migrations_<ENV_SAFE>`.

#### migrate

Apply all pending migrations:

```bash
sqlitex --db my.db migrate
```

Rollback the last migration:

```bash
sqlitex --db my.db migrate --rollback
```

With `--dry-run`, sqlitex prints which files would be applied or rolled back.

#### migrate-create

Generate a timestamped up/down migration pair:

```bash
# Name can be argument or flag
sqlitex --db my.db migrate-create add_users_table

# or
sqlitex --db my.db migrate-create --name add_users_table
```

Creates (in `--migrations-path`):

* `YYYYMMDD_HHMMSS_add_users_table.sql`
* `YYYYMMDD_HHMMSS_add_users_table.down.sql`

Both with minimal comment skeletons.

---

### Seeds

Seed files live in `--seeds-path` and are handled by extension:

* `*.sql` → executed as SQL
* `*.csv` → imported as CSV into table name derived from filename (e.g. `users_seed.csv` → `users`)
* `*.json` → imported as JSON (converted to CSV under the hood) into table derived similarly

#### seed

```bash
sqlitex --db my.db seed
```

This iterates over all files in the seeds directory and applies them.

---

### reset

Full reset: backup, drop DB, recreate, migrate & seed.

```bash
sqlitex --db my.db reset
```

With `--dry-run`, nothing is touched — only the planned actions are printed.

---

### backup

Create a timestamped copy of the DB in `--backup-path`:

```bash
sqlitex --db my.db backup
# e.g. ./db_backups/my_20251203_120304.db
```

---

### dump

Full `.dump` with schema + data:

```bash
# Dump to stdout
sqlitex --db my.db dump

# Dump to file
sqlitex --db my.db dump --file backup.sql
```

With `--dry-run`, the file path is printed but not written.

---

### export-all

Export all user tables to CSV or JSON in `--export-path`:

```bash
# All tables to CSV
sqlitex --db my.db export-all --format csv

# All tables to JSON
sqlitex --db my.db export-all --format json
```

Each table becomes `EXPORT_DIR/<table>.csv` or `EXPORT_DIR/<table>.json`.

---

### info

Quick DB metadata snapshot:

```bash
sqlitex --db my.db info
```

Shows:

* SQLite version
* DB size (bytes + human-readable)
* Page size & page count
* Journal mode
* Foreign key status
* User table count and up to 20 table names

---

### doctor

Run health checks:

```bash
sqlitex --db my.db doctor
```

Performs:

* `PRAGMA integrity_check;`
* `PRAGMA foreign_key_check;`
* Checks for:

    * Migration table existing but no migration files
    * Missing seeds directory
    * Large DB not in WAL mode (warns, does not auto-change)

Returns non-zero exit code if integrity or FK checks fail.

---

### optimize

Backup then run standard optimizations:

```bash
sqlitex --db my.db optimize
```

Steps:

1. Backup DB file
2. `VACUUM;`
3. `ANALYZE;`
4. `PRAGMA optimize;` (ignored if unsupported)

With `--dry-run`, only the planned operations are printed.

---

### explain

View query plan to help with indexing and performance:

```bash
sqlitex --db my.db explain --sql "SELECT * FROM users WHERE email = 'a@b.com';"
```

Under the hood uses:

```sql
EXPLAIN QUERY PLAN <your_query>;
```

---

### tune

Apply simple pragma-based tuning profiles:

```bash
# Development profile
sqlitex --db my.db tune --profile dev

# Production-ish profile
sqlitex --db my.db tune --profile prod

# Safe minimal profile (default)
sqlitex --db my.db tune          # same as --profile safe
```

Profiles:

* `dev`:

    * `PRAGMA journal_mode = WAL;`
    * `PRAGMA synchronous = NORMAL;`
    * `PRAGMA foreign_keys = ON;`
    * `PRAGMA temp_store = MEMORY;`
* `prod`:

    * `PRAGMA journal_mode = WAL;`
    * `PRAGMA synchronous = FULL;`
    * `PRAGMA foreign_keys = ON;`
* `safe`:

    * `PRAGMA foreign_keys = ON;`

With `--dry-run`, the PRAGMAs are printed but not applied.

---

## More Examples

```bash
# Create DB and basic schema
sqlitex --db app.db create-db
sqlitex --db app.db create-table \
  --table users \
  --columns "id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE"

# Seed using CSV & JSON
sqlitex --db app.db seed

# See a quick data sample
sqlitex --db app.db sample --table users --limit 5

# Export everything for debugging
sqlitex --db app.db export-all --format csv

# Check DB health
sqlitex --db app.db doctor

# Optimize DB (VACUUM + ANALYZE)
sqlitex --db app.db optimize

# See how a query will run
sqlitex --db app.db explain --sql "SELECT * FROM users WHERE email = 'x@y.com';"

# Tune for dev
sqlitex --db app.db tune --profile dev

# Dry-run a dangerous update to see the SQL only
sqlitex --db app.db --dry-run update \
  --table users \
  --set "is_active = 0" \
  --where "last_login IS NULL"

# Using env-specific migrations/seeds
sqlitex --db prod.db --env staging \
  --migrations-path ./db/migrations \
  --seeds-path ./db/seeds \
  migrate
```
