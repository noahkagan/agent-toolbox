---
name: workspace-conventions
description: Locate an nk workspace and distinguish nk task coordination from meta repository management. Use when working across repositories or with workspace task artifacts.
---

# Workspace conventions

Use `nk` for durable task lifecycle and coordination. Use `meta` for the
workspace repository set. Do not use either tool's state as a substitute for
the other.

See the [agent-toolbox README](../../README.md) for installation and the
available tools.

## Task workspace

Before reading or changing task state, run `nk workspace root` from the current
path. Use only the returned directory for `TODO.md`, `scratch/`, and `nk task`
commands. Do not infer the workspace from a Git root or repository layout.

`nk` owns the task tracker, task artifacts, lifecycle states, and slug format.
Use [nk](../../nk/README.md) and `nk task --help`.

## Repository workspace

`.meta` maps workspace-relative repository paths to clone URLs. Use `meta git
update` to clone or update those repositories, `meta git status` to inspect
them, and `meta exec '<cmd>'` to run a command in each repository.

The workspace `.gitignore` must ignore every repository path listed in `.meta`.
`bootstrap.sh` is the fresh-machine setup entry point when present.
