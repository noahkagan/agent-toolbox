# dashboard

A standalone record of delegated work, with a searchable dark HTML page.
Each assignment contains an agent, task title, mission, optional link, and update time.
It has no progress notes, status tracking, session integration, or task-manager dependency.

Requires Python 3.11 or later on POSIX. No packages, server, frontend build, or network resources are required.
Run `../install.sh` from this directory, or use `../bin/dashboard` directly.

## Record and update assignments

```sh
dashboard set renderer-suppression \
  --agent gke-2 \
  --task 'Per-product render suppression' \
  --mission 'Find a supported way to suppress selected products while their siblings keep rendering.' \
  --url https://example.org/tasks/renderer-suppression

dashboard set renderer-suppression --agent gke-1
dashboard set renderer-suppression --mission 'The updated mission.'
```

The ID appears in full above the task title. Use the complete task stub when one exists, such as `2026-11-03-usd-lidar-policy`.
It identifies the assignment independently of its agent or title. Each agent can have only one assignment. Agent names are compared without surrounding whitespace or case differences.
New assignments require `--agent`, `--task`, and `--mission`. Updates retain unspecified fields.
Use `--url ''` to clear the optional link. Each update records its UTC time and regenerates the page.
Keep progress and results in the linked task. Remove an agent’s previous assignment before assigning a different task.
Updates to the existing assignment ID remain supported.

## View and inspect

```sh
dashboard                  # render and print the HTML path
dashboard list             # JSON for agents and scripts
dashboard remove ID        # remove a record and regenerate the page
```

Open the printed `index.html` in a browser. It works directly from disk and refreshes every minute.
Search persists across refreshes in browsers that permit session storage.
Links accept HTTP(S), file URLs, or absolute local paths. Browser rules may restrict local links when served over HTTP.
The HTML contains assignment details; share it only with the intended audience.

## Storage

Default: `$XDG_STATE_HOME/dashboard`, or `~/.local/state/dashboard`.
Set `DASHBOARD_HOME` or pass `--store /path/to/board` before the command for another board.
There is no workspace discovery or configuration inheritance.

- `assignments.json`: authoritative versioned data.
- `index.html`: generated page; rebuild with `dashboard render`.
- `.lock`: serializes CLI updates to the same store.

Updates are locked and files replaced atomically. Independent remote stores do not synchronize automatically.
Use the CLI for concurrent updates. Direct JSON editing requires exclusive access, followed by `dashboard render`.
If HTML generation fails after saving JSON, the record remains saved; rerender after fixing the error.
Old note and status fields are ignored and removed on the next data update.
