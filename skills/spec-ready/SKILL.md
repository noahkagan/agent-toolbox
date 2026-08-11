---
name: spec-ready
description: Review any nk task specification by slug and decide whether a fresh author can implement and validate it without inventing product intent, regardless of its current placement.
---

# Review specification readiness

Review the named task without editing files or changing its placement. Return
`Ready` only when a fresh session can implement and validate it without
choosing unstated product behavior.

Before reading task or repository content, run
`nk task check --workspace <workspace-root> <slug>`. If it fails, stop without
further investigation and return `Not ready` with one `Spec repair` finding
containing its diagnostic.

Read the task's `README.md`, applicable repository instructions, and linked
authoritative context. Read `JOURNAL.md` only when it contains relevant current
context.

Check that the outcome and boundaries are clear. Requirements must be possible,
consistent, and verifiable. Consequential unknowns must be resolved or explicit.
Acceptance evidence must prove the outcome. Preserve implementation freedom
unless a constraint is necessary.

Investigate the repository only as needed to answer three questions:

1. **Repository assumptions:** Do load-bearing entities and seams named by the
   task exist and plausibly support the outcome?
2. **Decision continuity:** Could the task reverse deliberate prior direction
   recorded in project notes, its journal, or relevant Git history?
3. **Compatibility provenance:** Reject any backward-compatibility, legacy
   runtime, migration, or history-retention requirement without an
   authoritative consumer contract or explicit human decision selecting it,
   even when the behavior is unambiguous.

Keep these checks bounded. Do not design the implementation or audit unrelated
history. Prior implementation is evidence, not policy. A task may supersede
durable direction through an explicit human decision.

Return exactly `Ready` when no blocker remains. Otherwise return `Not ready`,
then only blocking findings in this form:

```text
Not ready
- [Spec repair] <location> — <missing, ambiguous, or unverifiable contract>
- [Human decision] <location> — <intent or tradeoff that cannot be derived safely>
```

Use `Spec repair` for defects that can return to `write-spec`. Use `Human
decision` for missing intent, consequential tradeoffs, or implicit decision
regressions. Only a human may choose whether to preserve or supersede durable
direction.

Report unresolved load-bearing questions instead of guessing. Combine evidence
for one blocker into one finding. Do not add scores, suggestions, plans, or
file edits.
