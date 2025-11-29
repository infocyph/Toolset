# sqlitex

`sqlitex` is a non-interactive, flag-based SQLite CLI:

- CRUD operations
- migrations + seeds
- backup/reset helpers
- CSV/JSON export

It’s ideal for scripts and CI where you want explicit flags instead of interactive shells.

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Sqlite/sqlitex" \
  -o /usr/local/bin/sqlitex && sudo chmod +x /usr/local/bin/sqlitex
````

## Usage

Global options must come **before** the command:

```bash
sqlitex [global options] <command >[command options]
```

### Global Options

| Option                     | Description                                          |
|----------------------------|------------------------------------------------------|
| `--db <file>`              | **(required)** SQLite database file                  |
| `--env <env>`              | Environment name (default: `default`)                |
| `--migrations-path <path>` | Migrations directory (default: `./migrations`)       |
| `--seeds-path <path>`      | Seeds directory (default: `./seeds`)                 |
| `--backup-path <path>`     | Backup directory (default: `./db_backups`)           |
| `--export-path <path>`     | Export directory (default: `./exports`)              |
| `--use-lock`               | Enable lock-retry behaviour on update/delete queries |

## Commands

| Command                                                         | Description                                   |
|-----------------------------------------------------------------|-----------------------------------------------|
| `create-db`                                                     | Create a new SQLite database file             |
| `create-table --table <name> --columns "<col_defs>"`            | Create table if not exists                    |
| `insert --table <name> --values "<vals>"`                       | Insert a single record                        |
| `insert-batch --file <sql_file>`                                | Execute a SQL file of inserts                 |
| `select --table <name> [--where "<cond>"] [--export csv\|json]` | Query rows (pretty/CSV/JSON)                  |
| `update --table <name> --set "<set>" --where "<cond>"`          | Update rows (with backup & transaction)       |
| `delete --table <name> --where "<cond>"`                        | Delete rows (with backup & transaction)       |
| `schema --table <name>`                                         | Show table schema                             |
| `migrate [--rollback]`                                          | Apply pending migrations or rollback last one |
| `seed`                                                          | Import seed files (SQL, CSV, JSON)            |
| `reset`                                                         | Backup → drop & recreate → migrate → seed     |

## Examples

```bash
# Create database file my.db
sqlitex --db my.db create-db

# Create users table with id & name columns
sqlitex --db my.db create-table --table users --columns "id INTEGER PRIMARY KEY, name TEXT"

# Insert a record
sqlitex --db my.db insert --table users --values "NULL,'Alice'"

# Batch inserts from a SQL file
sqlitex --db my.db insert-batch --file seeds/users.sql

# Select rows where id > 5 and pretty-print
sqlitex --db my.db select --table users --where "id>5"

# Export query to CSV
sqlitex --db my.db select --table users --where "id>5" --export csv

# Update name to Bob for id=1 (with transactional safety)
sqlitex --db my.db update --table users --set "name='Bob'" --where "id=1"

# Delete record with id=2 (with backup)
sqlitex --db my.db delete --table users --where "id=2"

# Show schema of users table
sqlitex --db my.db schema --table users

# Run all migrations
sqlitex --db my.db migrate

# Roll back last migration
sqlitex --db my.db migrate --rollback

# Seed the DB
sqlitex --db my.db seed

# Full reset: backup, recreate, migrate, seed
sqlitex --db my.db reset

# Use custom env + paths
sqlitex --db prod.db --env staging \
  --migrations-path ./db/migrations \
  --seeds-path ./db/seeds \
  reset
```
