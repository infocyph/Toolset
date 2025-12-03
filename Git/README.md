# gitx

`gitx` is an opinionated Git helper focused on:

* Branch workflows (`feature` / `bugfix` / `hotfix` / `release` / `docs` / `ci` / `experiment`)
* Cleanup, pruning, and branch hygiene
* Reporting / summaries / changelogs / worklogs
* Stash & WIP management
* Interactive commit helpers
* Light repo “doctor” and hook bootstrap
* Author/code-level analytics (surviving code %, blame-heavy vs lite modes)

It never hides Git – it just wires composable commands into practical workflows.

---

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Git/gitx" \
  -o /usr/local/bin/gitx && sudo chmod +x /usr/local/bin/gitx
```

## Usage

```bash
gitx <command> [arguments]
```

If you call `gitx` with no or unknown command, it prints a categorized help with all commands.

---

## Command Overview

### Repository & Branch Management

| Command                       | Description                                                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------- |
| `status`                      | Show repository status, branch tracking info, and remotes                                |
| `fetch`                       | Fetch remote branches and prune stale references                                         |
| `sync`                        | Sync `alpha` / `develop` (and optional branches) from main branch                        |
| `create <type> <name>`        | Create a new branch from main (`feature\|bugfix\|hotfix\|release\|docs\|ci\|experiment`) |
| `merge <source> <target>`     | Merge source branch into target branch                                                   |
| `reset-branch`                | Reset current branch to `origin/<branch>` (soft / hard / dry-run)                        |
| `prune`                       | Prune remote branches and delete local branches tracking `: gone]` remotes               |
| `cleanup`                     | Delete branches already merged into main (excluding core branches)                       |
| `orphan-branches [days]`      | List and optionally delete unmerged branches older than N days (default 30)              |
| `compare [branch1] [branch2]` | Compare two branches (commits + changed files)                                           |
| `initial-commit`              | Show the initial commit hash                                                             |
| `latest-tag`                  | Show the latest tag in the repo                                                          |

### Commit & Change Management

| Command                            | Description                                                       |
| ---------------------------------- | ----------------------------------------------------------------- |
| `commit`                           | Interactive commit helper (numbered file selection + message)     |
| `amend`                            | Amend last commit message (inline or interactive)                 |
| `unstage`                          | Unstage all files in the index (with confirmation)                |
| `cherry-pick`                      | Interactive cherry-pick by selecting commits from a numbered list |
| `revert`                           | Interactive revert (select commits; per-commit or amend mode)     |
| `diff [output_file]`               | Show staged diff or save it to a file                             |
| `log-file <path>`                  | Show commit history or diffs for a specific file                  |
| `count-changes <start> [end]`      | Show shortstat (files/insertions/deletions) between two commits   |
| `list-changes <branch1> <branch2>` | List files changed between two branches                           |
| `stage-deleted`                    | Stage all deleted files                                           |
| `stage-deleted-dir <directory>`    | Stage deleted files under a specific directory                    |

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

### Configuration, Hooks & Utilities

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

Shows:

* `git status -sb --untracked-files=all`
* Upstream ahead/behind counts (`git rev-list --left-right --count @{upstream}...HEAD`) or a note if no upstream
* Remotes in compact `remote -> URL` form

---

#### `fetch`

```bash
gitx fetch
```

* Ensures we’re in a Git repo
* Runs: `git fetch --prune`
* Good pre-step before prune/cleanup/summary.

---

#### Main-branch detection

Several commands auto-detect the main branch using:

1. `origin/HEAD` symbolic ref
2. `origin/main`
3. `origin/trunk`
4. Fallback: `master`

All “main” references below use that detection.

---

#### `sync`

```bash
gitx sync
```

* Detects main branch.

* Updates main:

  ```bash
  git checkout <main> && git pull origin <main>
  ```

* Merges main into:

    * `alpha`
    * `develop`
    * Additional comma-separated branches you optionally enter interactively.

* For each branch:

  ```bash
  git checkout <branch>
  git merge --no-ff <main>
  git push origin <branch>
  ```

Branches that don’t exist locally are skipped with a message.

---

#### `create <type> <name>`

```bash
gitx create feature merchant-fy-summary
```

* Types: `feature`, `bugfix`, `hotfix`, `release`, `docs`, `ci`, `experiment`.
* Branch name: `<type>/<name>` (e.g., `feature/merchant-fy-summary`).
* Steps:

    1. Detect main branch.
    2. Checkout main and pull latest.
    3. Create new branch from main.
    4. Push to origin.

If the branch already exists locally, it aborts with an error.

---

#### `merge <source> <target>`

```bash
gitx merge feature/fy-summary main
```

* Validates both branches exist.

* Confirms before merging.

* Flow:

  ```bash
  git checkout <target>
  git pull origin <target>
  git merge --no-ff <source>
  git push origin <target>
  ```

* On merge conflicts:

    * Notifies you about conflicts
    * Instructs you to resolve manually (`git status`, `git add`, `git commit`) or `git merge --abort`.

---

#### `reset-branch`

```bash
gitx reset-branch
```

* Operates on **current** branch.
* Requires `origin/<branch>` to exist.
* Menu:

    1. **Soft reset** – keep local changes, reset only HEAD:

       ```bash
       git fetch origin
       git reset --soft origin/<branch>
       ```

    2. **Hard reset** – discard all local changes (with confirmation):

       ```bash
       git fetch origin
       git reset --hard origin/<branch>
       ```

    3. **Dry-run** – preview diff vs `origin/<branch>`:

       ```bash
       git fetch origin
       git diff --stat origin/<branch>
       ```

---

#### `prune`

```bash
gitx prune
```

* Runs:

  ```bash
  git fetch --prune
  ```

* Detects local branches whose upstream shows `: gone]` in `git branch -vv`.

* Offers:

    * Delete all such branches at once, or
    * Confirm deletion per-branch.

---

#### `cleanup`

```bash
gitx cleanup
```

* Lists branches merged into main (excluding `master`, `main`, `develop`, `alpha`).
* Options:

    * Delete all merged branches at once.
    * Or confirm deletion one by one.

---

#### `orphan-branches [days]`

```bash
gitx orphan-branches        # default: 30 days
gitx orphan-branches 60
```

* Detects main branch.
* Scans all local branches:

    * Skips core branches (`master`, `main`, `develop`, `alpha`, `trunk`).
    * Skips branches already merged into main.
    * Computes age (in days) from last commit timestamp.
* Lists branches **not merged into main** and **older than N days**.
* Then offers:

    * Delete all of them, or
    * Delete selected names.

---

#### `compare [branch1] [branch2]`

```bash
gitx compare            # current vs main
gitx compare develop main
```

* If arguments omitted:

    * `branch1` → current branch
    * `branch2` → main branch
* Output:

    * Commits unique to `branch2`:

      ```bash
      git log --oneline branch1..branch2
      ```

    * Files changed between branches:

      ```bash
      git diff --name-only branch1..branch2
      ```

---

#### `initial-commit` and `latest-tag`

```bash
gitx initial-commit
gitx latest-tag
```

* `initial-commit`:

  ```bash
  git rev-list --max-parents=0 HEAD
  ```

* `latest-tag`:

  ```bash
  git describe --tags --abbrev=0
  ```

If no commits/tags exist, prints a friendly error.

---

### Commit & Change Management

#### `commit` (interactive)

```bash
gitx commit
```

Workflow:

1. If no changes: prints “No changes to commit.”

2. Shows `git status -s` with numbered lines.

3. Prompt:

    * `a` → stage all.
    * Or e.g. `1,3,5` → stage selected files.

4. Shows staged files (`git diff --cached --name-only`).

5. Prompts for commit message.

6. Runs `git commit -m`.

---

#### `amend`

```bash
gitx amend
```

* Asks for a new commit message:

    * If blank: runs `git commit --amend` (opens editor).
    * Otherwise: `git commit --amend -m "<new message>"`.

---

#### `unstage`

```bash
gitx unstage
```

* Warns this will unstage all files.
* Asks for confirmation.
* Runs:

  ```bash
  git reset --staged .
  ```

---

#### `cherry-pick` (interactive)

```bash
gitx cherry-pick
```

* Shows recent commits as:

  ```text
  1. <hash> <subject>
  2. ...
  ```

* You enter a comma-separated list of numbers (`1,4,5`).

* For each commit (in order):

  ```bash
  git cherry-pick <hash>
  ```

* On conflict:

    * Asks if you want to `resolve` manually or `abort`:

        * `abort` → `git cherry-pick --abort` and exit.

---

#### `revert` (interactive)

```bash
gitx revert
```

* Same numbered list of recent commits.
* You select commit numbers.
* Then choose mode:

    1. **Revert with normal commits**:

       ```bash
       git revert <commit>
       ```

       for each selected commit.

    2. **Revert & amend last commit**:

       ```bash
       git revert --no-commit <commit1> ...
       git commit --amend -m "Amended revert: <previous message>"
       ```

---

#### `diff [output_file]`

```bash
gitx diff
gitx diff staged.patch
```

* No file: prints staged diff (`git diff --cached`).
* With file:

    * Overwrite confirm if exists.
    * Writes `git diff --cached` to file.

---

#### `log-file <path>`

```bash
gitx log-file src/Service/Payment.php
```

* Validates the file exists in the working tree.
* Menu:

    1. **Commit history**:

       ```bash
       git log --follow --pretty='%h - %s (%an, %ad)' --date=short -- <file>
       ```

    2. **Diffs**:

       ```bash
       git log --follow -p -- <file>
       ```

---

#### `count-changes <start> [end]`

```bash
gitx count-changes v1.0.0 v1.1.0
gitx count-changes HEAD~50
```

* Default `end` = `HEAD`.
* Prints `git diff --shortstat <start> <end>` which includes:

    * files changed
    * insertions(+)
    * deletions(-)

---

#### `list-changes <branch1> <branch2>`

```bash
gitx list-changes main develop
```

* Prints `git diff --name-only branch1 branch2`.

---

#### `stage-deleted` & `stage-deleted-dir`

```bash
gitx stage-deleted
gitx stage-deleted-dir src/
```

* `stage-deleted`:

    * Finds all Git-deleted files (`git ls-files --deleted -z`) and stages them (`git add`).
* `stage-deleted-dir <dir>`:

    * Same, but scoped to the given directory.
    * Validates directory exists.

---

### Reporting, Summary & Worklogs

#### `summary [range] [include-all] [mode]`

```bash
# Heavy (default) blame over current repo
gitx summary

# Specific range, include all text/* files, heavy mode
gitx summary HEAD~50 include-all heavy

# Lite mode (no blame, Surviving Code % = N/A)
gitx summary HEAD~200 lite
gitx summary HEAD~50 include-all lite
```

* Range semantics:

    * If `range` provided (e.g., `HEAD~50`), it is used as `range..HEAD`.
* `include-all`:

    * Without it, only “code-ish” and config/text extensions are blamed.
    * With it, all `text/*` files are included.
* Modes:

    * `heavy` (default): runs `git blame` on all chosen files to compute **surviving code share** per author.
    * `lite` / `fast` / `no-blame`: skips blame; Surviving Code % is `N/A`, but commit stats are still accurate.

Output table:

| Author Name | Author Email | Commits | Files Changed | Insertions | Deletions | Surviving Code % |

Plus a `TOTAL` row for aggregate stats.

---

#### `summarize [short]`

```bash
gitx summarize
gitx summarize short
```

Prints repository summary:

* Current branch
* Latest commit (hash, subject, author, date)
* Total commits
* Number of tags
* Number of stashes
* `.git` directory size
* Remotes

If `short` is not specified:

* Also prints:

    * All branches (`git branch -a`)
    * Contributors (`git shortlog -sne`).

---

#### `commit-report`

```bash
# Commit range
gitx commit-report v1.0.0..v1.1.0

# Date range
gitx commit-report 2025-01-01 2025-01-31
```

* For a **commit range** (`<start>..<end>`):

  ```bash
  git log --no-merges <range>
  ```

* For a **date range**:

    * Validates `YYYY-MM-DD` format.
    * Uses:

      ```bash
      git log --no-merges \
        --after="YYYY-MM-DD 00:00" \
        --before="YYYY-MM-DD 23:59"
      ```

* Output: Markdown grouped by author, each with:

    * Email, commit count
    * Table:

      | Commit Id | Type | Subject & Body | Date & Time |

* `Type` derived from Conventional Commit prefixes (`feat`, `fix`, `refactor`, `chore`, `ci`, `build`, `test`, etc.); otherwise `misc`.

---

#### `worklog`

```bash
gitx worklog v1.0.0..v1.1.0
gitx worklog 2025-01-01 2025-01-31 >worklog-2025-01.csv
```

* Same range/date semantics as `commit-report`.

* Outputs CSV:

  ```text
  Author,Email,CommitId,Type,DateTime,Subject,Body
  ...
  ```

* Bodies are flattened (newlines removed).

* Designed to pipe into your own task-log generator.

---

#### `report <start> [end] [outfile]`

```bash
gitx report v1.0.0 v1.1.0
gitx report v1.0.0 v1.1.0 pr_report_v1.0.0_to_v1.1.0.txt
```

* Range: `<start>..[end]`, default `end=HEAD`.

* Sections:

    1. **PRs**:

        * `git log --merges` with subjects containing `"Merge pull request"`.
        * For each merge, list contained non-merge commits.

    2. **Non-PR merges**:

        * `git log --merges` excluding PR merges.
        * For each merge, list contained commits.

    3. **Standalone commits**:

        * Non-merge commits not part of any merge in the range.

* Writes to `outfile` (default: `pr_report_<start>_to_<end>.txt`) and `tee`s to stdout.

---

#### `changelog <start> <end>`

```bash
gitx changelog v1.0.0 v1.1.0
```

* Prompts for refs if omitted.

* Saves:

  ```text
  changelog_<start>_to_<end>.txt
  ```

* Each line:

  ```text
  <hash> - <subject> (<author>, <date>)
  ```

---

### Stash, WIP & Cleanup

#### `stash` (interactive + CLI)

```bash
# Interactive menu
gitx stash

# Direct subcommands
gitx stash save "Before refactor"
gitx stash list
gitx stash apply 0
gitx stash pop 1
gitx stash drop 2
gitx stash rename 0 "WIP: dashboard refactor"
gitx stash clear
```

* Without subcommand: shows an interactive menu:

    1. Save
    2. List
    3. Apply
    4. Pop
    5. Drop
    6. Rename
    7. Clear all

* Subcommands map to:

    * `save` – `git stash push -m "<message>"`
    * `list` – `git stash list`
    * `apply` – `git stash apply stash@{n}`
    * `pop` – `git stash pop stash@{n}`
    * `drop` – `git stash drop stash@{n}`
    * `rename` – `git stash store -m "<new name>" stash@{n}`
    * `clear` – `git stash clear`

---

#### `wip`

```bash
gitx wip save "experimenting with API"
gitx wip list
gitx wip pop
gitx wip apply
gitx wip clear
```

* Wrapper around stash with WIP semantics:

    * `save`: `WIP: <branch> @ <timestamp> - <msg>`
    * `list`: filter `git stash list` by `WIP:`.
    * `pop` / `apply` / `clear`: operate on stashes (especially WIP ones).

---

#### `clean [--force]`

```bash
gitx clean           # interactive
gitx clean --force   # immediate clean
```

* Interactive mode:

    1. Preview untracked files/dirs (`git clean -fdn`).
    2. Full clean (`git clean -fd`) with confirmation.

* `--force` / `force`:

  ```bash
  git clean -fd
  ```

Non-interactive, destructive.

---

#### `large-files`

```bash
gitx large-files
```

Flow:

1. Ask how many files (default `10`).

2. Ask:

    * Display inline, or
    * Save to a file (default `large_files.txt`).

3. Computes via:

   ```bash
   git rev-list --objects --all |
   git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' |
   awk '$1=="blob" {print $3, $4}' |
   sort -k1 -nr |
   head -<count>
   ```

4. Prints `"<size> bytes  <path>"` per line.

---

### Configuration, Hooks & Utilities

#### `add-remote <name> <url>`

```bash
gitx add-remote origin git@github.com:org/repo.git
```

* Prompts if name or URL omitted.
* Runs `git remote add <name> <url>`.

---

#### `push-remote <remote> <branch>`

```bash
gitx push-remote origin feature/payment-flow
```

* Defaults remote to `origin` if omitted (prompt).
* Validates branch exists locally.
* Runs `git push <remote> <branch>`.

---

#### `pull-remote <remote> <branch>`

```bash
gitx pull-remote origin develop
```

* Defaults remote to `origin` if omitted (prompt).
* Validates remote exists.
* Runs `git pull <remote> <branch>`.

---

#### `config`

```bash
gitx config
```

* Shows `git config --list`.
* Menu:

    1. Add/Edit a global key:

       ```bash
       git config --global <key> <value>
       ```

    2. Remove a global key:

       ```bash
       git config --global --unset <key>
       ```

---

#### `set-lf`

```bash
gitx set-lf
```

* Sets:

  ```bash
  git config --global core.autocrlf false
  ```

---

#### `doctor`

```bash
gitx doctor
```

Repo health snapshot:

* Repo root
* Current branch and detected main
* Upstream ahead/behind (if tracking)
* Working tree status:

    * total changes
    * untracked count
* Stash count
* Branches merged into main but still present
* `.git` directory size
* Top 5 largest blobs (size + path) from Git history

---

#### `hooks init`

```bash
gitx hooks init
```

Creates hook templates in `.git/hooks`:

* `prepare-commit-msg.gitx` – appends Conventional Commit hints as comments.
* `pre-commit.gitx` – fails if conflict markers (`<<<<<<< HEAD`) exist in staged changes.
* `pre-push.gitx` – runs `vendor/bin/pest` or `vendor/bin/phpunit` if present, failing on test failure.

Then asks whether to activate them by copying to real hook names:

* `prepare-commit-msg`
* `pre-commit`
* `pre-push`

All marked executable.

---

#### `self-update`

```bash
gitx self-update
```

* Downloads latest script from GitHub into `/tmp/gitx_latest`.
* Computes SHA-256 of remote file vs current `gitx`.

    * If equal → “already up-to-date.”
* If different:

    1. Backs up current script as `gitx.bak-<timestamp>`.
    2. Moves new script into place.
    3. Marks it executable.

If the existing location is not writable, it warns you to rerun as sudo or install in a writable path.

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

# Reset current branch to remote (soft/hard/dry-run menu)
gitx reset-branch

# Cleanup merged branches
gitx cleanup

# Find and trim old unmerged branches (>45 days)
gitx orphan-branches 45

# Compare branches quickly
gitx compare main develop

# Interactive commit
gitx commit

# Amend last commit message
gitx amend

# Unstage everything
gitx unstage

# Stage deleted files
gitx stage-deleted
gitx stage-deleted-dir src/

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

# Show top 10 largest blobs
gitx large-files
```
