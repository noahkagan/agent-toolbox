---
keywords:
  - durable tasks
  - task states
  - task updates
  - workspace tracker
---

# Durable task model

`nk` preserves work across sessions. It does not coordinate agents,
own implementation branches, publish candidates, or mirror external review.

`TODO.md` is the workspace entry point. Its active sections appear in attention
order: In Progress, Ready, then Needs More Info. In Progress means implementation
started. Ready means the task has a specification that a fresh session can execute
and validate. Needs More Info means the task has never reached that specification
granularity.

Done and Cancelled retain inactive tasks at the bottom of the same index. They are
archive dispositions rather than active workflow states. A task may move directly
between active sections because the index reports current orientation, not an
enforced lifecycle.

Each stable task slug may include a GitHub, Linear, or project tracker identifier.
Its `scratch/<slug>/README.md` holds the current task definition. Its
`scratch/<slug>/JOURNAL.md` holds durable updates and the next useful restart point.
Task updates link to canonical project notes instead of copying durable knowledge.
The owning project keeps that knowledge according to
[note maintenance](../skills/maintain-notes/SKILL.md).

Tasks begin in Needs More Info. Their README may be staged, revised, and split
until [specification review](../skills/spec-ready/SKILL.md) finds them Ready.
Decomposition creates smaller tasks and records their relationship in ordinary
Markdown links. No dependency graph or parent-child state propagation is required.

`nk` changes only workspace files. Git and forge tools independently own commits,
branches, pull requests, review, and merge.

## Uncertainty frontier

- At what archive size would the inactive sections obscure active work enough to
  justify a separate archive document?
