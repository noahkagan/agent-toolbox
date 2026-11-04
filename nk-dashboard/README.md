# nk-dashboard

An interactive task board with PINNED tasks and one ASSIGNED slot per configured agent.
Every agent remains visible, including agents without a task. Search filters pinned tasks and dims unmatched assignments without hiding agent slots.

Requires Python 3.11 or later on POSIX. Uses the Python standard library and a loopback HTTP server.
Run `../install.sh` to install the `nk-dashboard` command.

## Configuration

Create `~/.config/nk-dashboard/config.json`, or pass `--config PATH`.
The path respects `XDG_CONFIG_HOME`. Configuration is required and reloaded for each operation.

```json
{
  "agents": [{"name": "worker-1"}, {"name": "worker-2"}],
  "commands": {
    "assign": ["my-dispatcher", "assign", "{agent}", "{id}", "{mission}"],
    "unassign": ["my-dispatcher", "unassign", "{agent}", "{id}"]
  }
}
```

Commands are argument arrays, executed directly without a shell. Supported placeholders are `{id}`, `{agent}`, `{task}`, `{mission}`, and `{url}`.
Each substituted value remains one argument. Escape literal braces as `{{` and `}}`.
Commands inherit the server or CLI environment and working directory. Each command has a 120-second timeout.
Omitting a command makes that transition update only the board.

[config.example.json](config.example.json) connects these actions to `codemux send` with editable prompt templates.
Codemux remains optional; configuration owns the integration. Agent names must match the configured dispatcher's names.
Removing an agent from configuration requires unassigning its task first.

## Commands

```sh
nk-dashboard pin TASK-ID --task 'Task title' --mission 'Task mission' --url https://example.org/task
nk-dashboard assign TASK-ID --agent worker-1
nk-dashboard unassign TASK-ID
nk-dashboard list
nk-dashboard serve --port 8765
```

`assign` replaces the former `set` command. It also accepts `--task`, `--mission`, and `--url` to create or edit a task.
`pin` creates or updates an unassigned task. Pinning an assigned task unassigns it first.
`unassign` returns the task to PINNED. `remove TASK-ID` deletes a task, unassigning it first when necessary.
Task IDs appear in full. One task occupies one location; each agent holds at most one task.

Running `nk-dashboard` without a subcommand starts the server. Open its printed loopback URL.
The old static `index.html` is no longer updated. The interactive page requires the running server.

Drag a pinned card into an empty agent slot to assign it. Drag an assigned card into PINNED to unassign it.
Dragging between empty agent slots runs unassign followed by assign. Occupied slots reject new cards; unassign their tasks first.
Select-and-Assign controls and Unassign buttons provide keyboard alternatives.
The page refreshes every minute and displays command errors.

## Action behavior

CLI commands and browser moves use the same transition logic and command templates.
Entering a slot invokes `assign`; leaving invokes `unassign`. Repeating an existing assignment does not resend its command.
Editing task text without changing ownership does not send a command.
Board mutations are serialized, including their configured commands. Stale browser moves are rejected before running commands.

Successful commands commit their transition. A failed unassign keeps the task assigned.
If unassign succeeds and the next assign fails, the task remains pinned.
Command failure, timeout, or process interruption may leave an unknown external outcome. Inspect the agent before retrying; commands are never automatically replayed.
The board records command success, not whether a remote agent has started or completed work.

The server binds to `127.0.0.1` only. Writes require a per-server request token, and requests reject unrecognized Host headers.
Do not expose the server through an untrusted proxy: configured commands run with your account's privileges.

## Storage

Existing assignments remain in `$XDG_STATE_HOME/dashboard`, or `~/.local/state/dashboard`.
`DASHBOARD_HOME` and `--store PATH` override the storage directory.
Version 1 assignments load without executing commands; the first mutation writes version 2 task records.
Include every existing assigned agent in configuration before opening the board.
The JSON store remains authoritative and uses locked, atomic updates. Back it up with the configuration.

## Journal summaries

Configure the nk workspace whose published task journals the board should follow:

```json
"workspace": {
  "path": "~/work",
  "remote": "origin",
  "branch": "main"
}
```

While the server runs, it fetches that branch at startup and every minute, then reads
`scratch/<task-id>/JOURNAL.md` for each pinned or assigned task.
The published branch must contain the nk workspace marker.
Fetch uses a dashboard-owned Git ref. It does not pull, merge, checkout, or modify
local files; unpublished journal edits are not displayed.

The latest entry is the last level-two Markdown heading (`## `) outside fenced code.
Cards show its heading and an excerpt of the first paragraph, limited to 320 characters.
This is an extractive summary, not generated prose.
Tasks without journal entries display no journal section.

Sync runs in the background, separate from assignment commands. Multiple open pages
share the same server refresh. Journal updates never trigger agent commands.
The page shows the last successful sync time. A failed fetch retains the previous
summaries and displays a stale-data notice; the next minute retries automatically.
Omit `workspace` to disable journal syncing. Summary data is derived in memory and
is not stored in the assignment ledger.
