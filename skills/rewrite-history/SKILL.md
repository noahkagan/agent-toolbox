---
name: rewrite-history
description: Rewrite Git commit history to optimize for reviewers. Use when asked to clean up, split, squash, or reorganize commits for review.
---

# Rewrite history

Rewrite the selected commit range into small, atomic, independent outcomes while preserving the intended behavior.

- By default, rewrite only commits authored by the user. Do not modify other authors’ commits unless explicitly requested.
- Have a subagent audit the selected changes for non-load-bearing changes, including remnants made stale by iteration. Cut changes that no longer support the intended outcomes before organizing commits.
- Make each commit the smallest complete change that delivers one atomic, independent outcome. Split changes that can be reviewed and accepted independently, even within the same feature, subsystem, or change type.
- Check each proposed commit for multiple outcomes before finalizing it. Order genuine dependencies first; no commit should require a later fixup to work.
- Separate pure refactors, features, performance optimizations, and pure documentation changes. Keep tests and documentation required by an outcome with that outcome.
- Fold churn, discovery, iteration, and fixups into their final outcomes. Drop changes that cancel out; do not preserve the development chronology.
- Write commit messages that explain the outcome and its reason.
