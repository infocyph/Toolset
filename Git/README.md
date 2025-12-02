# gitx

`gitx` is an opinionated Git helper focused on:

- Branch workflows (`feature` / `bugfix` / `hotfix` / `release` / `docs` / `ci` / `experiment`)
- Cleanup, pruning, and branch hygiene
- Reporting / summaries / changelogs / worklogs
- Stash & WIP management
- Interactive commit helpers
- Light repo “doctor” and hook bootstrap

It never hides Git – it just wires composable commands into practical workflows.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Git/gitx" \
  -o /usr/local/bin/gitx && sudo chmod +x /usr/local/bin/gitx
````

## Usage

```bash
gitx <command> [arguments]
```

---

## Command Overview

### Repository & Branch Management

| Command                       | Description                                                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------- |
| `status`                      | Show repository status, tracking, and remote info                                        |
| `fetch`                       | Fetch remote branches and prune stale references                                         |
| `sync`                        | Sync `alpha` / `develop` (and optional branches) from main branch                        |
| `create <type> <name>`        | Create a new branch from main (`feature\|bugfix\|hotfix\|release\|docs\|ci\|experiment`) |
| `merge <source> <target>`     | Merge source branch into target branch                                                   |
| `reset-branch`                | Reset current branch to `origin/<branch>` (soft / hard / dry-run)                        |
| `prune`                       | Prune remote branches and delete local tracking branches marked `gone`                   |
| `cleanup`                     | Delete branches already merged into main (excludes core branches)                        |
| `orphan-branches [days]`      | List and optionally delete unmerged branches older than N days (default 30)              |
| `compare [branch1] [branch2]` | Compare two branches (commits + changed files)                                           |
| `initial-commit`              | Show the initial commit hash                                                             |
| `latest-tag`                  | Show the latest tag in the repo                                                          |

### Commit & Change Management

| Command                            | Description                                                       |
| ---------------------------------- | ----------------------------------------------------------------- |
| `commit`                           | Interactive commit helper (choose files by number, then commit)   |
| `amend`                            | Amend last commit message (inline or interactive)                 |
| `unstage`                          | Unstage all files in the index                                    |
| `cherry-pick`                      | Interactive cherry-pick by selecting commits from a numbered list |
| `revert`                           | Interactive revert (select commits; revert individually or amend) |
| `diff [output_file]`               | Show staged diff or save it to a file                             |
| `log-file <path>`                  | Show commit history or diffs for a specific file                  |
| `count-changes <start> [end]`      | Show shortstat (files/insertions/deletions) between two commits   |
| `list-changes <branch1> <branch2>` | List files changed between two branches                           |

### Reporting, Summary & Worklog

| Command                                 | Description                                                   |
| --------------------------------------- | ------------------------------------------------------------- |
| `summary [range] [include-all] [mode]`  | Per-author summary with surviving-code %, heavy or lite mode  |
| `summarize [short]`                     | Repository summary (branches, tags, contributors, size, etc.) |
| `commit-report <range>`                 | Author-based Markdown commit report for a commit range        |
| `commit-report <start_date> <end_date>` | Author-based report for a date range (`YYYY-MM-DD`)           |
| `worklog <range>`                       | CSV worklog for a commit range (per commit row)               |
| `worklog <start_date> <end_date>`       | CSV worklog for a date range (`YYYY-MM-DD`)                   |
| `report <start> [end] [outfile]`        | PR / merge / standalone commit report for a commit range      |
| `changelog <start> <end>`               | Changelog between two commits/tags                            |

### Stash, WIP & Cleanup

| Command                               | Description                                                                    |
| ------------------------------------- | ------------------------------------------------------------------------------ |
| `stash`                               | Interactive stash manager (save / list / apply / pop / drop / rename / clear)  |
| `stash save [msg]`                    | Save changes to stash with optional message                                    |
| `stash list`                          | List all stashes                                                               |
| `stash apply <n>`                     | Apply `stash@{n}`                                                              |
| `stash pop <n>`                       | Pop `stash@{n}`                                                                |
| `stash drop <n>`                      | Drop `stash@{n}`                                                               |
| `stash rename <n> <name>`             | Rename `stash@{n}` to a new name                                               |
| `stash clear`                         | Delete all stashes                                                             |
| `wip <save\|list\|pop\|apply\|clear>` | Opinionated WIP helper on top of `stash`                                       |
| `clean [--force]`                     | Clean untracked files/dirs (interactive by default; `--force` to skip prompts) |
| `large-files`                         | Show or save the largest Git-tracked blobs (by size)                           |

### Configuration & Utilities

| Command                         | Description                                                                |
| ------------------------------- | -------------------------------------------------------------------------- |
| `add-remote <name> <url>`       | Add a new remote                                                           |
| `push-remote <remote> <branch>` | Push a specific branch to a specific remote                                |
| `pull-remote <remote> <branch>` | Pull a specific branch from a specific remote                              |
| `config`                        | Interactive Git configuration editor (global)                              |
| `set-lf`                        | Configure Git to prefer LF line endings (`core.autocrlf=false`)            |
| `doctor`                        | Repository health check (upstream, changes, stashes, .git size, big blobs) |
| `hooks init`                    | Install Git hook templates (prepare-commit-msg, pre-commit, pre-push)      |
| `self-update`                   | Update `gitx` from GitHub (with backup + hash check)                       |

---

## Detailed Command Notes

### Repository & Branch Management

#### `status`

```bash
gitx status
```

* Shows `git status -sb --untracked-files=all`
* Prints upstream ahead/behind counts (or “No upstream branch set”)
* Lists remotes in a compact `remote -> URL` form

#### `fetch`

```bash
gitx fetch
```

* Runs `git fetch --prune`
* Good pre-step before pruning / cleanup / summary.

#### `sync`

```bash
gitx sync
```

* Detects main branch (`origin/HEAD`, `origin/main`, `origin/trunk`, default `master`).
* Updates main: `git checkout <main> && git pull origin <main>`.
* Merges main into:

    * `alpha`
    * `develop`
    * Any extra comma-separated branches you specify interactively.
* Pushes back updated branches.

#### `create <type> <name>`

```bash
gitx create feature merchant-fy-summary
```

* Valid types: `feature`, `bugfix`, `hotfix`, `release`, `docs`, `ci`, `experiment`.
* Branch name pattern: `<type>/<name>`, e.g. `feature/merchant-fy-summary`.
* Steps:

    * Detect main branch
    * Checkout main and pull
    * Create new branch from main
    * Push to origin

#### `merge <source> <target>`

```bash
gitx merge feature/xyz main
```

* Confirms before merge.
* Ensures target is up-to-date (`git checkout <target> && git pull origin <target>`).
* Merges with `--no-ff`.
* Pushes target branch on success.
* If conflicts occur, it tells you to resolve manually and optionally run `git merge --abort`.

#### `reset-branch`

```bash
gitx reset-branch
```

* Operates on current branch; requires `origin/<branch>` to exist.
* Options:

    1. **Soft** reset: `git reset --soft origin/<branch>`
    2. **Hard** reset: `git reset --hard origin/<branch>` (with confirmation)
    3. **Dry-run**: shows diff vs `origin/<branch>` without changing anything.

#### `prune`

```bash
gitx prune
```

* Runs `git fetch --prune`.
* Lists local branches whose remote is `gone` (deleted remotely).
* Lets you:

    * Delete all such branches at once, or
    * Confirm per-branch deletion.

#### `cleanup`

```bash
gitx cleanup
```

* Lists branches already merged into `main`/`master`/`develop`/`alpha` (excluding those core branches).
* Lets you delete:

    * All merged branches
    * Or confirm per-branch.

#### `orphan-branches [days]`

```bash
gitx orphan-branches         # default: 30 days
gitx orphan-branches 60
```

* Detects main branch.
* Finds local branches **not merged** into main whose **last commit is older than N days** (default 30).
* Shows them with age in days and then offers to:

    * Delete all, or
    * Delete selected branches.

#### `compare [branch1] [branch2]`

```bash
gitx compare
gitx compare develop main
```

* If no args:

    * `branch1` defaults to current branch
    * `branch2` defaults to main branch
* Prints:

    * `git log --oneline branch1..branch2` (commits unique to branch2)
    * `git diff --name-only branch1..branch2` (changed files)

#### `initial-commit`, `latest-tag`

```bash
gitx initial-commit
gitx latest-tag
```

* `initial-commit`: uses `git rev-list --max-parents=0 HEAD`.
* `latest-tag`: uses `git describe --tags --abbrev=0`.

---

### Commit & Change Management

#### `commit` (interactive)

```bash
gitx commit
```

* Lists `git status -s` numbered.
* You can:

    * Enter `a` to stage all
    * Or specify `1,3,4` style selection.
* Shows staged files.
* Prompts for commit message and runs `git commit -m`.

#### `amend`

```bash
gitx amend
```

* Prompts for new commit message:

    * If message is empty → `git commit --amend` (interactive editor).
    * Otherwise → `git commit --amend -m "<message>"`.

#### `unstage`

```bash
gitx unstage
```

* Confirms then runs `git reset --staged .`.

#### `cherry-pick` (interactive)

```bash
gitx cherry-pick
```

* Shows `git log --oneline` numbered.
* You enter commit numbers (e.g. `1,5,6`).
* Cherry-picks them one by one.
* If conflict occurs:

    * You can choose to `resolve` manually or `abort`.

#### `revert` (interactive)

```bash
gitx revert
```

* Shows recent commits numbered.
* You pick one or more by number.
* Mode selection:

    1. **Standard**: creates separate revert commits for each selected commit.
    2. **Revert + amend**: reverts with `--no-commit` then amends last commit.

#### `diff [output_file]`

```bash
gitx diff
gitx diff staged.patch
```

* If no file: prints `git diff --cached`.
* If file specified:

    * Confirms overwrite if file exists.
    * Writes staged diff to file.

#### `log-file <path>`

```bash
gitx log-file src/Feature/Service.php
```

* Validates file exists.
* Options:

    1. View commit history (`git log --follow`).
    2. View diffs (`git log --follow -p`).

#### `count-changes <start> [end]`

```bash
gitx count-changes v1.0.0 v1.1.0
gitx count-changes HEAD~20
```

* Calls `git diff --shortstat <start> <end>` and prints the summary.

#### `list-changes <branch1> <branch2>`

```bash
gitx list-changes main develop
```

* Runs `git diff --name-only branch1 branch2`.

---

### Reporting, Summary & Worklogs

#### `summary [range] [include-all] [mode]`

```bash
# Heavy (default) blame over whole repo
gitx summary
gitx summary HEAD~50 include-all heavy

# Lite mode (no blame, Surviving Code % = N/A)
gitx summary HEAD~200 lite
gitx summary HEAD~50 include-all lite
```

* Computes per-author metrics:

  | Column           | Meaning                                                |
    | ---------------- | ------------------------------------------------------ |
  | Author Name      | From `git log`                                         |
  | Author Email     | From `git log`                                         |
  | Commits          | Number of commits by this author in the range          |
  | Files Changed    | Sum of files changed for their commits                 |
  | Insertions       | Sum of insertions                                      |
  | Deletions        | Sum of deletions                                       |
  | Surviving Code % | Share of current blamed lines belonging to this author |

* Arguments:

    * `range` (optional): e.g. `HEAD~50` (interpreted as `HEAD~50..HEAD`).
    * `include-all` (optional): include all `text/*` files, not only code-ish extensions.
    * `mode` (optional):

        * `heavy` (default): runs `git blame` across all relevant files for **accurate** surviving code.
        * `lite` / `fast` / `no-blame`: skips blame; `Surviving Code %` becomes `N/A`, but all commit stats stay accurate.

* Includes a final `TOTAL` row aggregating all authors.

#### `summarize [short]`

```bash
gitx summarize
gitx summarize short
```

* Repo-level summary:

    * Current branch
    * Latest commit
    * Total commits
    * Number of tags
    * Number of stashes
    * `.git` directory size
    * Remotes
* If `short` is **not** provided:

    * Also prints branches and contributors (`git shortlog -sne`).

#### `commit-report`

```bash
# By commit range
gitx commit-report v1.0.0..v1.1.0

# By date range
gitx commit-report 2025-01-01 2025-01-31
```

* Emits a Markdown report grouped by author:

    * Author name & email
    * Number of commits
    * Table per author:

      | Commit Id | Type | Subject & Body | Date & Time |

* Detects `type` from Conventional Commit prefixes (`feat`, `fix`, `refactor`, `chore`, etc.), falls back to `misc`.

#### `worklog`

```bash
# Commit range
gitx worklog v1.0.0..v1.1.0

# Date range
gitx worklog 2025-01-01 2025-01-31
```

* Outputs **CSV** to stdout:

  ```text
  Author,Email,CommitId,Type,DateTime,Subject,Body
  ...
  ```

* Body is single-line (newlines stripped).

* Designed to be piped into your PHP “Commit → Task Log” processor.

#### `report <start> [end] [outfile]`

```bash
gitx report v1.0.0 v1.1.0
gitx report v1.0.0 v1.1.0 pr_report.txt
```

* Range: `<start>..[end]` (default `end=HEAD`).

* Splits report into:

    1. **PRs** (`Merge pull request ...` merges)
    2. **Non-PR merges**
    3. **Standalone commits**

* For each merge, shows subcommits included.

* Writes to `outfile` (default `pr_report_<start>_to_<end>.txt`) and also `tee` to stdout.

#### `changelog <start> <end>`

```bash
gitx changelog v1.0.0 v1.1.0
```

* Saves a log file:

  ```text
  changelog_<start>_to_<end>.txt
  ```

* Each line: `<hash> - <subject> (<author>, <date>)`.

---

### Stash, WIP & Cleanup

#### `stash` (interactive & CLI)

```bash
# Interactive menu
gitx stash

# Direct subcommands
gitx stash save "Before big refactor"
gitx stash list
gitx stash apply 0
gitx stash pop 1
gitx stash drop 2
gitx stash rename 0 "WIP: dashboard refactor"
gitx stash clear
```

* Interactive mode lets you choose common operations via menu.
* CLI subcommands map to:

    * `save`: `git stash push -m "<name>"`
    * `list`: `git stash list`
    * `apply`: `git stash apply stash@{n}`
    * `pop`: `git stash pop stash@{n}`
    * `drop`: `git stash drop stash@{n}`
    * `rename`: `git stash store -m "<name>" stash@{n}`
    * `clear`: `git stash clear`

#### `wip`

```bash
gitx wip save "experimenting with API"
gitx wip list
gitx wip pop
gitx wip apply
gitx wip clear
```

* Convenience wrapper around stash for **Work-In-Progress**:

    * `save`: creates a `WIP: <branch> @ <timestamp> - <msg>` stash.
    * `list`: shows only WIP-like stashes (filtering by `WIP:`).
    * `pop` / `apply` / `clear`: operate on stashes, primarily WIP use-case.

#### `clean [--force]`

```bash
gitx clean              # interactive (dry-run or clean)
gitx clean --force      # immediate git clean -fd
```

* Interactive:

    1. Preview untracked (`git clean -fdn`)
    2. Clean untracked (`git clean -fd` with confirmation)
* `--force`:

    * Non-interactive `git clean -fd` (dangerous, but explicit).

#### `large-files`

```bash
gitx large-files
```

* Prompts:

    * How many files? (default 10)
    * Inline vs save-to-file.
* Scans Git object database (blobs) and sorts by size.
* Output: `<size> bytes  <path>`.

---

### Configuration & Utilities

#### `add-remote <name> <url>`

```bash
gitx add-remote origin git@github.com:org/repo.git
```

* You can also run without args; it will prompt.
* Runs `git remote add`.

#### `push-remote <remote> <branch>`

```bash
gitx push-remote origin feature/payment-flow
```

* If args omitted, prompts for them.
* Validates branch exists locally.

#### `pull-remote <remote> <branch>`

```bash
gitx pull-remote origin develop
```

* If args omitted, prompts.
* Validates remote exists.

#### `config`

```bash
gitx config
```

* Shows `git config --list`.
* Two options:

    1. Add/edit key (global)
    2. Remove key (global)

#### `set-lf`

```bash
gitx set-lf
```

* Sets `core.autocrlf=false` globally.

#### `doctor`

```bash
gitx doctor
```

* Health snapshot:

    * Repo root
    * Current vs main branch
    * Upstream ahead/behind (if tracking)
    * Count of working-tree changes and untracked files
    * Number of stashes
    * Branches merged into main but still present
    * `.git` size
    * Top 5 largest blobs (byte size + path)

#### `hooks init`

```bash
gitx hooks init
```

* Writes example hook templates into `.git/hooks`:

    * `prepare-commit-msg.gitx` – Conventional Commit hints appended as comments.
    * `pre-commit.gitx` – fails commit if conflict markers (`<<<<<<<`) exist in staged diff.
    * `pre-push.gitx` – runs `vendor/bin/pest` or `vendor/bin/phpunit` if present.
* Optionally copies them to actual hook names (`prepare-commit-msg`, `pre-commit`, `pre-push`) and marks them executable.

#### `self-update`

```bash
gitx self-update
```

* Downloads latest script from GitHub.
* Compares SHA-256 of local vs remote:

    * If identical → “already up-to-date”.
* Backs up existing `gitx` as `gitx.bak-<timestamp>`.
* Replaces binary and sets executable.

---

## Examples

```bash
# Basic status
gitx status

# Fetch & prune
gitx fetch

# Sync alpha & develop from main
gitx sync

# Create a new feature branch
gitx create feature merchant-fy-summary

# Merge feature into main
gitx merge feature/merchant-fy-summary main

# Reset current branch to remote (with menu)
gitx reset-branch

# Cleanup merged branches
gitx cleanup

# Find and trim old unmerged branches (>45 days)
gitx orphan-branches 45

# Compare branches quickly
gitx compare main develop

# Interactive commit
gitx commit

# Amend last commit
gitx amend

# Stash current work
gitx stash save "Before big refactor"

# WIP-friendly stash
gitx wip save "Experimenting with FY summary"

# Generate PR/merge/standalone report between tags
gitx report v1.0.0 v1.1.0 pr_report_v1.0.0_to_v1.1.0.txt

# Generate changelog between tags
gitx changelog v1.0.0 v1.1.0

# Heavy, full-accuracy author summary for last 100 commits
gitx summary HEAD~100 include-all heavy

# Lite (no blame) summary for last 200 commits
gitx summary HEAD~200 lite

# Date-based worklog CSV for a month
gitx worklog 2025-01-01 2025-01-31 >worklog-2025-01.csv

# Repo doctor
gitx doctor

# Initialize git hook templates
gitx hooks init

# Update gitx itself
gitx self-update

```
