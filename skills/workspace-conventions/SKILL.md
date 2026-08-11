---
name: workspace-conventions
description: Locate an nk workspace and distinguish durable task context from meta repository management. Use when working across repositories or with workspace task artifacts.
---

# Workspace conventions

Use `nk` for durable task context. Use `meta` for the workspace
repository set. Git and forge tools own implementation and review state.

See the [agent-toolbox README](../../README.md) for installation and the
available tools.

## Task workspace

Before reading or changing task state, run `nk workspace root` from the current
path. Use only the returned directory for `TODO.md`, `scratch/`, and `nk task`
commands. Do not infer the workspace from a Git root or repository layout.

`nk` owns the task index, task documents, placement, and slug format. Use the
[durable task model](../../nk/task-model.md) and `nk task --help`.

Read `TODO.md` first when reorienting. Its active sections are In Progress,
Ready, and Needs More Info, in that order.

Read `scratch/<slug>/README.md` for the current task definition. Read
`JOURNAL.md` for durable updates and the next useful restart point.

Stage, refine, and decompose work in those Markdown files. Give each durable
subtask its own slug and link related tasks directly.

Keep product knowledge in the owning project's notes. Link those notes from
the task instead of copying them into the task documents. Use `maintain-notes`
when those notes change.

## Repository workspace

`.meta` maps workspace-relative repository paths to clone URLs. Use `meta git
update` to clone or update those repositories, `meta git status` to inspect
them, and `meta exec '<cmd>'` to run a command in each repository.

The workspace `.gitignore` must ignore every repository path listed in `.meta`.
`bootstrap.sh` is the fresh-machine setup entry point when present.
