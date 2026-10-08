---
name: minimize-change-complexity
description: Review every commit for net line growth, implementation-bound tests or documentation, and opportunities to simplify factoring, ownership, control flow, or interfaces, then repair findings. Use after a multi-commit change and before completion or review.
---

# Minimize Change Complexity

Determine the commit range. Ask only when its base is ambiguous.

For each commit, oldest first:

1. Measure the net lines added for its outcome.
2. Consider whether better factoring, more concise code, better ownership,
   clearer linearity, or uniform control surfaces could reduce overload or
   interface complexity.
   Split files that own unrelated concepts or transformations. Keep each file
   centered on one coherent ownership boundary; never split by line count alone.
3. Remove or rewrite tests that pin private helpers, internal structure,
   dependency choices, or intermediate steps. Test behavior only through public
   interface seams.
4. Remove documentation of private design choices, dependency choices,
   internal structure, or tuning constants. Document only durable behavior at
   public interface seams.
5. Make each worthwhile repair in the current worktree.

Do not reduce lines at the expense of behavior, clarity, or verification.
Preserve history unless the user requests rewriting it.

Complete only after reviewing every commit, verifying repairs, and accounting
for remaining net additions.
