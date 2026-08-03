---
name: write-spec
description: Draft or revise software work specifications that define verifiable outcomes without prescribing implementation. Use for features, fixes, refactors, acceptance criteria, scope decisions, or specification-readiness repairs.
---

# Write a software specification

Define the required outcome, its boundaries, and the evidence needed to prove
completion. Leave design choices to the implementer unless a contract or
explicit constraint fixes them.

Expose consequential unknowns instead of guessing:

```text
??? <question>. Blocks: <decision or outcome>
```

An unresolved question may remain only when it does not prevent an implementer
from choosing correct behavior or proving completion.

Treat backward compatibility, legacy runtime behavior, migration, and history
retention as product decisions. Do not infer them because older state exists.
Require an authoritative consumer contract or an explicit human decision that
selects breaking or resetting, one-time migration, or ongoing compatibility.
Otherwise record the choice as an unresolved question; do not select it.

## Set the scope

Prefer the fewest independently useful specifications. Split outcomes that can
land, provide value, and be verified alone. Keep inseparable outcomes together
when splitting would duplicate a contract or create an unusable intermediate
state.

Name external behavior and necessary constraints. Do not convert preferences,
likely designs, process steps, or validation tactics into requirements.

## Write nine sections

### Mission statement

State one observable outcome and its beneficiary in one sentence. Describe the
result, not work such as implementing, refactoring, or testing.

### Requirements

List the behavior needed to achieve the mission. Order items from fundamental
behavior to specific cases.

### Non-goals

Exclude work that a reasonable reader could infer from the mission. Do not list
unrelated work.

### Constraints

State only rules every acceptable solution must obey. Cite authoritative
contracts instead of copying details that can change elsewhere.

### Invariants

State truths that must remain true across the change.

### Contract or interface changes

Name each added, changed, or removed behavior and the consumer that relies on
it. Use `None` when no contract changes.

### Validation boundaries

Separate durable validation from temporary evidence. Keep validation that
protects a named consumer, contract, or invariant. Remove probes, logs, and
one-off migration checks unless something depends on them.

Require evidence without prescribing test design, counts, coverage, mocks, or
development sequence. State the evidence type only when the requirement would
otherwise be unclear.

### Acceptance criteria

List observable conditions that jointly prove the mission. Each criterion must
distinguish a correct result from a wrong result without selecting an internal
design.

Exclude process milestones such as review completion, code submission, or test
creation.

### Derisk sequence

Name the largest assumptions. Test them from highest risk to lowest using the
cheapest conclusive experiment. Name the assumption tested by each step. Use
`None` when no material assumption needs an experiment.

This sequence orders learning, not implementation.

## Review the result

Review from the mission downward. After any correction, restart the review.
Finish only when every answer is satisfactory.

1. Is the outcome clear without implementation instructions?
2. Do the requirements, constraints, and invariants reject every unacceptable
   outcome?
3. Are likely scope inferences either required or excluded?
4. Could a different correct design satisfy the specification?
5. Do the acceptance criteria prove the mission with available evidence?
6. Is every statement necessary, consistent, possible, and verifiable?
7. Does the specification reference authoritative facts instead of duplicating
   them?
8. Does the derisk sequence address the largest assumptions cheaply?
9. Should any independently useful outcome become its own specification?

When the specification spans several repositories, contracts, platforms, or
observable outcomes, request one fresh-context review of its contract size.
Accept only `accept`, `split candidates`, or `uncertain`. Resolve split
candidates, or record the operator's explicit decision, before finishing.

## Output

Return only the nine sections above, plus context required to understand them.
Use `None` when explicitly recording absence prevents confusion. Do not add an
implementation plan, task process, or detailed validation method unless the
user requests it.
