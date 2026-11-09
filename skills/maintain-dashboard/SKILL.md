---
name: maintain-dashboard
description: Maintain nk-dashboard task assignments and pinned coordination notes when delegating work, reconciling agent activity, or updating review and merge plans.
---

# Maintain dashboard

Read the [dashboard documentation](../../nk-dashboard/README.md) for commands,
storage, and hook behavior. Inspect the configured store and hooks, then run
`nk-dashboard list` before changing cards.

- Check the affected agent's current turn and latest response before assigning,
  unassigning, or retrying an action. Use `codemux read AGENT` when available;
  the board alone does not establish agent activity.
- Pin tasks using their full task slug, a concise mission, and a canonical link.
  Assign only when the agent's existing work and the requested handoff agree.
  Unassign when relinquishing responsibility; use removal only for card cleanup.
- Assignment hooks may send prompts. Do not send a duplicate prompt separately.
  Board maintenance does not authorize interrupting or redirecting unrelated work.
- Use pinned notes for cross-task plans, review/merge order, and unresolved
  decisions. Start with `nk-dashboard note-template`; update the existing Markdown
  note or use `pin-note`. Link task specifications instead of copying their scope.
- Remove superseded coordination text. Keep execution evidence in task journals,
  not notes. Commit changed dashboard data when it belongs to a workspace repo.

Read the board again to verify the requested changes. After dispatch, check the
agent received the instruction before reporting it delivered.
