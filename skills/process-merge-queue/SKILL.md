---
name: process-merge-queue
description: Process a workspace MERGE_QUEUE.md in order, rebasing, repairing CI, and merging authorized PRs while waiting for work or progressing checks.
---

# Process merge queue

- `MERGE_QUEUE.md` contains only a flat list of PR URLs. Keep operator instructions and status elsewhere.
- Sync the workspace safely. Process only the first URL; never skip ahead or work on multiple PRs concurrently.
- Confirm merge authorization and exclusive branch ownership from the session or handoff. Queue membership alone does not authorize merging.
- Verify the target branch and prerequisites. Rebase if straightforward, preserving qualified behavior; publish rewritten history with an exact lease.
- An empty queue or slow, progressing CI is not a blocker. Keep polling with bounded waits; remain responsive to new instructions.
- Diagnose CI failures and make high-confidence, scoped repairs. Run affected checks, push, and resume monitoring. Never bypass checks or weaken coverage.
- Stop and report only when progress requires missing authorization, an external prerequisite, or a decision beyond a high-confidence repair. Do not skip the blocked PR.
- Merge the verified head when eligible. If already merged, verify its outcome. Remove only that URL, commit and push the queue update, then reread the queue.
