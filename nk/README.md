# nk

`nk` preserves task context across sessions. It manages a Markdown
index and task documents inside an initialized workspace.

The [durable task model](task-model.md) defines the files and state meanings.
Git and forge tools own commits, branches, pull requests, review, and merge.
Use `meta` separately when a workspace contains multiple repositories.

## Workspace data

Run `nk workspace init` at a Git control-repository root. It creates the
`.nk/workspace` marker, `TODO.md`, and `scratch/`. Resolve the owning workspace
from any descendant with `nk workspace root`.

`TODO.md` is the task index. Each entry links to one
`scratch/<slug>/README.md`. That file holds the current task definition.
`scratch/<slug>/JOURNAL.md` holds durable updates and the next restart point.

Create a task with `nk task create <slug>`. It starts in Needs More Info with
both documents ready for refinement.

## Slugs

Task slugs have this form:

```
YYYY-MM-DD[-gh-N|-lin-N|-PROJECT-N]-lowercase-kebab-description
```

The date and nonempty lowercase kebab-case description are required. The
optional tracker segment is a GitHub issue (`gh-N`), Linear issue (`lin-N`), or
uppercase project key and number (`PROJECT-N`).

## Task index

Active sections appear in this order: In Progress, Ready, then Needs More Info.
Done and Cancelled retain inactive tasks at the bottom.

Use `move` to change active placement. Use `archive` for Done or Cancelled.
Use `reopen` to return an archived task to an active section. Use `reorder` to
change priority within one section.

Run `nk task check <slug>` to validate the indexed task files. This command
does not assess specification quality. Use the `spec-ready` skill for that.

Run `nk task --help` for the complete command list. Run
`nk task <command> --help` for command arguments.

This release is a destructive format cutover. Existing workspaces must rewrite
their tracker and task files before the new commands can resolve them.
