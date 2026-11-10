---
name: process-merge-queue
description: Process a workspace MERGE_QUEUE.md in order, rebasing and merging authorized PRs or stopping at the first blocker.
---

# Process merge queue

- `MERGE_QUEUE.md` contains only a flat list of PR URLs. Keep operator instructions and status elsewhere.
- Sync the workspace safely. Process only the first URL; never skip ahead or work on multiple PRs concurrently.
- Confirm merge authorization and exclusive branch ownership from the session or handoff. Queue membership alone does not authorize merging.
- Verify the target branch and prerequisites. Rebase if straightforward, preserving qualified behavior; publish rewritten history with an exact lease.
- Wait for required CI and reviews. Stop and report conflicts, failures, or missing prerequisites that need more than a straightforward rebase. Do not broaden repairs or bypass checks.
- Merge the verified head when eligible. If already merged, verify its outcome. Remove only that URL, commit and push the queue update, then reread the queue.
