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

### Range vs date windows

For commands that accept **date windows** (`YYYY-MM-DD YYYY-MM-DD`), `gitx` resolves the window to:

- **start_ref** = first commit in the window (chronological)
- **end_ref** = last commit in the window (newest)

Then it runs the same logic as commit/tag ranges. This keeps outputs consistent across repos and avoids off-by-one issues.

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
| `tag <version>`               | Create and push an annotated tag (e.g., `v1.2.3`)                                        |
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

| Command                                                | Description                                                   |
| ------------------------------------------------------ | ------------------------------------------------------------- |
| `summary [range] [include-all] [mode]`                 | Per-author summary with surviving-code %, heavy or lite mode  |
| `summary <start_date> <end_date> [include-all] [mode]` | Same, but for a date window (`YYYY-MM-DD`)                    |
| `summarize [short]`                                    | Repository summary (branches, tags, contributors, size, etc.) |
| `commit-report <range>`                                | Author-based Markdown commit report for a commit range        |
| `commit-report <start_date> <end_date>`                | Author-based report for a date window (`YYYY-MM-DD`)          |
| `worklog <range>`                                      | CSV worklog for a commit range (per commit row)               |
| `worklog <start_date> <end_date>`                      | CSV worklog for a date window (`YYYY-MM-DD`)                  |
| `report <start> [end] [outfile]`                       | PR / merge / standalone commit report for a commit range      |
| `report <start_date> <end_date> [outfile]`             | Same, but for a date window (`YYYY-MM-DD`)                    |
| `changelog <start> <end>`                              | Changelog between two commits/tags                            |
| `changelog <start_date> <end_date> [file]`             | Changelog for a date window (`YYYY-MM-DD`)                    |

### Stash, WIP & Cleanup

| Command                               | Description                                                                    |
| ------------------------------------- | ------------------------------------------------------------------------------ |
| `stash`                               | Interactive stash manager (save / list / apply / pop / drop / rename / clear)  |
| `stash save [msg]`                    | Save changes to stash with optional message                                    |
| `stash list`                          | List all stashes                                                               |
| `stash apply <n>`                     | Apply `stash@{n}`                                                              |
| `stash pop <n>`                       | Pop `stash@{n}`                                                                |
| `stash drop <n>`                      | Drop `stash@{n}`                                                               |
| `stash rename <n> <name>`             | Rename `stash@{n}` to a new name (multi-word supported)                        |
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

#### `tag <version>`

```bash
gitx tag v1.0.0
gitx tag 1.0.0     # also accepted (will create tag "1.0.0")
```

* Creates an **annotated tag**:
  ```bash
  git tag -a <version> -m "Release <version>"
  ```
* Pushes the tag:
  ```bash
  git push origin <version>
  ```
* Refuses to overwrite existing tags.

---

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
gitx compare            # current vs main (prompts if omitted)
gitx compare develop main
```

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

* Shows recent commits as a numbered list.
* You enter a comma-separated list of numbers (`1,4,5`).
* For each commit (in order):

  ```bash
  git cherry-pick <hash>
  ```

* On conflict: you choose `resolve` manually or `abort` (`git cherry-pick --abort`).

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
* With file: confirms overwrite if exists, then writes staged diff to the file.

---

#### `log-file <path>`

```bash
gitx log-file src/Service/Payment.php
```

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
* Prints `git diff --shortstat <start> <end>`.

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

* Stages deleted files tracked by Git.

---

### Reporting, Summary & Worklogs

#### `summary` (heavy/lite, range or date)

```bash
gitx summary
gitx summary HEAD~50 include-all heavy
gitx summary 2025-01-01 2025-01-31 lite
```

* Modes:
  * `heavy` (default): runs `git blame` to compute **surviving code share** per author.
  * `lite` / `fast` / `no-blame`: skips blame; Surviving Code % is `N/A`.

---

#### `commit-report`

```bash
gitx commit-report v1.0.0..v1.1.0
gitx commit-report 2025-01-01 2025-01-31
```

* Outputs Markdown grouped by author.

---

#### `worklog`

```bash
gitx worklog v1.0.0..v1.1.0
gitx worklog 2025-01-01 2025-01-31 >worklog-2025-01.csv
```

* Outputs CSV:
  ```text
  Author,Email,CommitId,Type,DateTime,Subject,Body
  ```

---

#### `report` (PR/merge/standalone)

```bash
gitx report v1.0.0 v1.1.0
gitx report 2025-01-01 2025-01-31 pr_report_jan.txt
```

* Sections:
  1. PR merges (subjects contain `"Merge pull request"`)
  2. Non-PR merges
  3. Standalone commits not inside merges

---

#### `changelog`

```bash
gitx changelog v1.0.0 v1.1.0
gitx changelog 2025-01-01 2025-01-31 changelog_jan.txt
```

* Produces a `changelog_*.txt` file with lines:
  ```text
  <hash> - <subject> (<author>, <date>)
  ```

---

### Stash, WIP & Cleanup

#### `stash` (interactive + CLI)

```bash
gitx stash
gitx stash save "Before refactor"
gitx stash rename 0 "WIP: dashboard refactor"
```

* `rename` supports multi-word names.

---

#### `wip`

```bash
gitx wip save "experimenting with API"
gitx wip list
gitx wip pop
```

---

### Configuration, Hooks & Utilities

#### `hooks init`

```bash
gitx hooks init
```

Creates hook templates in `.git/hooks`:

* `prepare-commit-msg.gitx`
* `pre-commit.gitx`
* `pre-push.gitx`

Optionally activates them by copying without `.gitx`.

---

#### `self-update`

```bash
gitx self-update
```

Downloads latest script from GitHub, compares SHA-256, backs up and replaces if newer.

---

## Examples

```bash
gitx status
gitx fetch
gitx sync
gitx create feature merchant-fy-summary
gitx merge feature/merchant-fy-summary main
gitx tag v1.0.0
gitx report 2025-01-01 2025-01-31
gitx changelog v1.0.0 v1.1.0
gitx summary HEAD~100 include-all heavy
gitx worklog 2025-01-01 2025-01-31 >worklog-2025-01.csv
gitx doctor
gitx hooks init
gitx self-update
gitx large-files
```
