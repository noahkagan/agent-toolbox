---
name: minimize-change-complexity
description: Review every commit for net line growth and opportunities to simplify factoring, ownership, control flow, or interfaces, then repair findings. Use after a multi-commit change and before completion or review.
---

# Minimize Change Complexity

Determine the commit range. Ask only when its base is ambiguous.

For each commit, oldest first:

1. Measure the net lines added for its outcome.
2. Consider whether better factoring, more concise code, better ownership,
   clearer linearity, or uniform control surfaces could reduce overload or
   interface complexity.
3. Make each worthwhile repair in the current worktree.

Do not reduce lines at the expense of behavior, clarity, or verification.
Preserve history unless the user requests rewriting it.

Complete only after reviewing every commit, verifying repairs, and accounting
for remaining net additions.
