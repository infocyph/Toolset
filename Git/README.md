# gitx

`gitx` is an opinionated Git helper focused on:

- branch workflows (feature/bugfix/hotfix/release/docs/ci/experiment)
- cleanup and pruning
- reporting / summaries / changelogs
- stash management
- interactive commit helpers

It never hides the underlying Git commands – it just wires them together.

## Installation

```bash
sudo curl -fsSL "https://raw.githubusercontent.com/infocyph/Toolset/main/Git/gitx" \
  -o /usr/local/bin/gitx && sudo chmod +x /usr/local/bin/gitx
````

## Usage

```bash
gitx <command >[arguments]

```

## Commands

| Command                            | Description                                                              |
|------------------------------------|--------------------------------------------------------------------------|
| `status`                           | Show repo status, tracking & remote info                                 |
| `fetch`                            | Fetch remotes & prune stale refs                                         |
| `sync`                             | Merge `main` → `alpha`/`develop` (plus optional extras)                  |
| `create <type> <name>`             | Create branch (`feature\|bugfix\|hotfix\|release\|docs\|ci\|experiment`) |
| `merge <src> <dst>`                | Merge source branch into target                                          |
| `reset-branch`                     | Reset current branch to remote (soft/hard/dry-run)                       |
| `prune`                            | Prune remote-tracking branches & delete local stale ones                 |
| `cleanup`                          | Delete merged branches                                                   |
| `compare <branch1> <branch2>`      | Show commit & file diff between two branches                             |
| `commit`                           | Interactive commit helper                                                |
| `amend`                            | Amend last commit message                                                |
| `cherry-pick <hash>`               | Cherry-pick specific commits                                             |
| `revert`                           | Revert commits (interactive)                                             |
| `diff`                             | Show or save staged diff                                                 |
| `log-file <file>`                  | Show commit history & diffs for a file                                   |
| `large-files`                      | List largest files in repo                                               |
| `stash`                            | Manage stash (save, list, apply, pop, drop, rename, clear)               |
| `report <start> [end] [outfile]`   | Generate PR & merge commit report                                        |
| `summary [range] [include-all]`    | Summarize commits, changes, surviving code %                             |
| `count-changes`                    | Count insertions/deletions between two commits                           |
| `list-changes <branch1> <branch2>` | List files changed between branches                                      |
| `changelog <start> <end>`          | Generate changelog between refs                                          |
| `commit-report <start> <end>`      | Detailed commit report by author/type                                    |
| `add-remote <name> <url>`          | Add a new Git remote                                                     |
| `push-remote <remote> <branch>`    | Push to specific remote branch                                           |
| `pull-remote <remote> <branch>`    | Pull from specific remote branch                                         |
| `config`                           | Interactive Git config editor                                            |
| `set-lf`                           | Enforce LF line endings                                                  |
| `self-update`                      | Update the `gitx` script from GitHub                                     |

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

# Reset current branch to remote
gitx reset-branch

# Cleanup merged branches
gitx cleanup

# Compare branches
gitx compare main develop

# Interactive commit
gitx commit

# Amend last commit
gitx amend

# Stash operations
gitx stash

# Generate a report between tags
gitx report v1.0.0 v1.1.0 report.txt

# Generate a changelog between tags
gitx changelog v1.0.0 v1.1.0

# Update gitx itself
gitx self-update
```
