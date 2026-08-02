---
name: map-workstreams
description: Create a temporary Mermaid Gantt of every Blocked, Authoring, and Ready nk task, using exact task slugs and earliest dependency-allowed equal-size slots. Use when someone needs to see the actionable task queue, its dependency chain, or available parallel work without Backlog noise.
---

# Map workstreams

Read `TODO.md` and the task documents for every included task. Write
`/tmp/WORKSTREAMS.md` unless the user explicitly names another destination.

Keep the output to:

- a short warning that the snapshot is nonauthoritative;
- one Mermaid Gantt containing every included task; and
- only the assumptions needed to interpret unresolved dependencies or blockers.

Use these Gantt rules:

- Include every task in Blocked, Authoring, and Ready. Exclude Backlog, Done,
  and Cancelled tasks.
- Use the exact task slug as the rendered row label. Do not substitute friendly
  names. Because nk slugs begin with an ISO date, prefix each source label with
  an invisible U+2060 word joiner so Mermaid treats it as task text rather than
  a date.
- Give every task one equal-size slot and place it in the earliest slot allowed
  by its declared task dependencies. Satisfied Done dependencies cost no slot.
- Treat dependencies on excluded Backlog tasks, external blockers, and
  undeclared sequencing as available at slot 1. State that assumption instead
  of inventing dependency edges or adding Backlog rows.
- Use plain section titles such as `section Slot 1`.
- Give task rows valid Mermaid syntax, for example:
  `⁠2026-07-11-task-validation-artifact-qualification :t1, 2026-01-01, 1d`.
- Do not add workstream prose, dependency flowcharts, structural-width
  calculations, resource analysis, or friendly task lists unless the user asks.

Before finishing, render or parse the block with an available Mermaid
implementation; do not add a project dependency for this check. Verify that
row labels after removing U+2060 exactly equal the Blocked, Authoring, and
Ready slugs in `TODO.md`, with no omissions or duplicates, and that each
included scheduled dependency precedes its dependent.
