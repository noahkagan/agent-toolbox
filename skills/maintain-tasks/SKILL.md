---
name: maintain-tasks
description: Maintain durable nk task context across sessions. Use when locating a workspace, reorienting on tasks, creating or updating task documents, recording progress, decomposing work, or changing task placement.
---

# Maintain tasks

Run `nk root` before reading or changing tasks. Use only the returned workspace
for `TODO.md`, `scratch/`, and `nk task` commands. Do not infer it from a Git
root or repository layout.

Read `TODO.md` only when locating a task or checking priorities. Read the selected
task's `README.md` for scope and constraints, then recent `JOURNAL.md` entries for
current progress and next steps.

Read enough to identify the next action, its constraints, and how to verify it.
Follow older entries and linked sources when a decision, uncertainty, or
contradiction requires more context. Deepen reading before making decisions that
depend on missing history. Always follow applicable project instructions.

Use the [durable task model](../../nk/task-model.md) as the authority for file
roles, placement, and slugs.

## Preserve context

Keep the current task definition in `README.md`. Append concise, chronological
updates to `JOURNAL.md`. Record verified progress, decisions, failed
hypotheses, and the next useful action.

Keep product knowledge in the owning project's notes. Link those notes from
the task instead of copying them. Use `$maintain-notes` when they change.

## Refine work

Create tasks with `nk task create <slug>`. Stage undefined work in Needs More
Info. Use `$refine-spec` when the task needs an executable specification.

Task definitions list expected repository changes and expected file changes.
Use `None` when no changes are expected.

Decompose an independently useful outcome into its own task. Link related
tasks directly and keep each requirement in one canonical task.

Move a task to Ready only after `$refine-spec` returns `Ready`. Move it to In
Progress when implementation begins. Archive it when it no longer needs
attention.

Use `meta` for the workspace repository set. Git and forge tools own
implementation and review state.
