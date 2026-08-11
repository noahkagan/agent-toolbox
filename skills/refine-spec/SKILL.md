---
name: refine-spec
description: Draft, revise, or review software task specifications until a fresh session can implement and validate them without inventing product intent. Use for features, fixes, refactors, acceptance criteria, scope decisions, specification-readiness review, or readiness repairs.
---

# Refine a specification

Select the mode requested by the user:

- **Write:** draft or revise the specification.
- **Review:** inspect without editing and return only the readiness verdict.
- **Refine:** write, review, and repair until the specification is Ready or a
  human decision remains.

For an nk task, run `nk task check --workspace <workspace-root> <slug>` first.
If it fails, stop. In Review mode, return its diagnostic as one `Spec repair`
finding.

Read the task's `README.md`, applicable repository instructions, and linked
authoritative context. Read `JOURNAL.md` only when it contains relevant current
context.

## Define the outcome

State one observable outcome and its beneficiary. Define the required behavior,
boundaries, invariants, interface changes, and evidence that proves completion.
Leave design choices to the implementer unless a contract or explicit
constraint fixes them.

Classify each unknown before deciding whether it blocks the specification:

- Ask for a **product decision** when alternatives change user-visible behavior.
- Research a **technical fact**.
- Resolve an **empirical question** through an experiment.
- Choose a reasonable initial value for a **tunable default**.

Mark unresolved product decisions and other consequential unknowns:

```text
??? <question>. Blocks: <decision or outcome>
```

Only a missing product decision normally blocks readiness. Another unknown may
remain only when it cannot change correct behavior or proof. Treat compatibility,
migration, and history retention as product decisions. Require an authoritative
consumer contract or an explicit human decision.

Prefer the fewest independently useful specifications. Split outcomes that can
land, provide value, and be verified alone. Keep inseparable outcomes together
when splitting would duplicate a contract or create an unusable intermediate
state.

## Write the specification

Use these sections in order:

1. **Mission statement:** one observable outcome and beneficiary.
2. **Requirements:** behavior required to achieve the mission.
3. **Non-goals:** plausible scope inferences that are excluded.
4. **Constraints:** rules every acceptable solution must obey.
5. **Invariants:** truths that must remain true.
6. **Contract or interface changes:** affected behavior and consumers, or None.
7. **Validation boundaries:** durable evidence that protects named behavior.
8. **Acceptance criteria:** observable conditions that jointly prove success.
9. **Derisk sequence:** cheapest conclusive tests for material assumptions, or
   None.

Do not prescribe test design, implementation sequence, review milestones, or
internal structure. Cite authoritative contracts instead of copying them.

## Review readiness

Check whether a fresh session can implement and validate the task without
choosing unstated behavior. Inspect the repository only enough to verify:

1. Named entities and seams exist and plausibly support the outcome.
2. The task does not silently reverse a durable decision.
3. Compatibility requirements have authoritative provenance.

Confirm that every statement is necessary, consistent, possible, and
verifiable. Confirm that acceptance criteria distinguish a correct result from
an incorrect result. Report unresolved load-bearing questions instead of
guessing.

In Review mode, return exactly `Ready` when no blocker remains. Otherwise
return only blocking findings:

```text
Not ready
- [Spec repair] <location> — <missing, ambiguous, or unverifiable contract>
- [Human decision] <location> — <intent or tradeoff that cannot be derived safely>
```

Use `Spec repair` for correctable specification defects. Use `Human decision`
for missing intent, consequential tradeoffs, or implicit decision reversals.
Do not add scores, suggestions, plans, or file edits in Review mode.

In Write mode, return only the nine specification sections and required
context. In Refine mode, repeat writing and review until Ready. Return the
updated specification when Ready. Stop with the Review verdict when any `Human
decision` finding remains.
