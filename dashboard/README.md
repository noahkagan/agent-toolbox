# dashboard

A standalone record of delegated work, with a searchable HTML page.
It does not connect to agents, discover activity, or depend on a task manager.
An assignment is an explicit report, not proof that someone is currently running.

Requires Python 3.11 or later on POSIX. No Python packages, web server, frontend build, or network resources are required.
Run `../install.sh` from this directory, or use `../bin/dashboard` directly.

## Record an assignment

```sh
dashboard set renderer-suppression \
  --agent gke-2 \
  --task 'Per-product render suppression' \
  --mission 'Find a supported way to suppress selected products while their siblings keep rendering.' \
  --status queued \
  --note 'Prompt delivered; execution not yet confirmed.' \
  --url https://example.org/tasks/renderer-suppression
```

The ID identifies the assignment, independently of its agent or title.
One agent can have multiple assignments. Reassign with `--agent`; keep the ID.
Create a new ID for a new task if the previous assignment should remain visible.

Update only what changed:

```sh
dashboard set renderer-suppression --status working --note 'Native probe running.'
dashboard set renderer-suppression --status blocked --note 'Waiting for provider access.'
dashboard set renderer-suppression --status done --note 'Evidence and recommendation published.'
```

Statuses: `queued` (default), `working`, `blocked`, `paused`, and `done`.
New assignments require `--agent`, `--task`, and `--mission`. Updates retain unspecified fields.
Use `--note ''` or `--url ''` to clear an optional field.
Every update records its UTC report time and regenerates the HTML page.
Completed assignments remain until explicitly removed; there is no transition history or automatic expiration.

## View and inspect

```sh
dashboard                  # render and print the HTML path
dashboard list             # JSON for agents and scripts
dashboard remove ID        # remove a record and regenerate the page
```

Open the printed `index.html` in a browser. It works directly from disk and refreshes every minute.
Search and status filters persist across refreshes in browsers that permit session storage.
Links accept HTTP(S), file URLs, or absolute local paths. Browser rules may restrict local links when the page is served over HTTP.
The generated HTML contains assignment details; share it only with the intended audience.

## Storage

Default: `$XDG_STATE_HOME/dashboard`, or `~/.local/state/dashboard`.
Set `DASHBOARD_HOME` or pass `--store /path/to/board` before the command for another board.
There is no workspace discovery or configuration inheritance.

- `assignments.json`: authoritative versioned data.
- `index.html`: generated page; rebuild with `dashboard render`.
- `.lock`: serializes CLI updates to the same store.

The CLI locks updates and atomically replaces files. Independent remote stores do not synchronize automatically.
Use the CLI for concurrent updates. Direct JSON editing requires exclusive access, followed by `dashboard render`.
If HTML generation fails after saving JSON, the record remains saved; rerender after fixing the error.

## Agent handoff convention

After delegating, record the agent, task mission, and the status actually confirmed.
Use `queued` for a delivered prompt when execution is unverified.
Update on meaningful status changes; record a blocker or result in `--note`.
This convention is optional and has no dependency on a session launcher or task repository.
