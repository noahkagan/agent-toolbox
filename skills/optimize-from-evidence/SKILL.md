---
name: optimize-from-evidence
description: Iteratively improve a target system's measured performance using data-transformation and high-throughput reasoning. Use for evidence-driven optimization through reproducible baselines, focused experiments, and validated implementation changes.
---

# Optimize from evidence

Follow these steps in order, repeating where indicated and carrying accumulated improvements and evidence forward until the stopping condition is met.
Summarize each step to the user, progressively maintain tasks and notes in their designated locations, and commit and push those updates to make them durable.

1. **Establish or reuse evidence.** Use reproducible baselines for representative
   workloads and scales. Reuse baselines and profiling while relevant binaries,
   workloads, configuration, hardware, and operating conditions remain comparable.
   State what invalidates existing evidence before remeasuring. Measure completed
   useful work and consumer outcomes; distinguish execution, waiting, and overlap.
2. **Generate and rank hypotheses.** Trace costs from what the original producer
   provides to what the final consumer needs, across service boundaries.
   Identify the largest end-to-end opportunities. Check tasks and notes for
   previous findings and exclusions. Rank by expected benefit, confidence, and
   remaining cost. If no worthwhile hypothesis remains, go to step 6.
3. **Resolve ranking uncertainty.** Investigate underlying capabilities or physical
   throughput constraints only when the result could change which improvement
   to attempt next. State the ranking decision, possible outcomes, and cost
   bound. Use source inspection, targeted research, or the smallest experiment.
   Bound total investigation cost for this selection round. Re-rank after each
   result; repeat only when the expected value of changing the choice justifies
   the remaining cost. Park blocked or over-budget investigations.
4. **Test the leading improvement.** State the hypothesis, expected outcome, and
   evidence that would support or reject it. Implement on an isolated branch
   or worktree from the aggregate branch. Measure against both the previous
   accumulated version and original baseline under comparable conditions. Screen
   candidates cheaply; repeat measurements only when resolving uncertainty could
   change implementation or retention.
5. **Retain or exclude.** Qualify accumulated changes together across representative
   workloads, checking correctness, ownership, completion guarantees, and measurement
   variation. Targeted benefits are sufficient if other workloads do not regress.
   Add qualified improvements to the aggregate branch and update one draft PR
   per repository; do not merge it. Revert rejected implementation changes while
   preserving the tested hypothesis, evidence, and exclusion. Progressively record
   results, reproduction details, and unresolved questions in designated tasks
   and notes; distinguish facts from inference.
6. **Repeat from the accumulated system.** Return to step 1 with retained
   improvements and hypothesis history. Revisit exclusions only with new evidence.
   Stop only when no worthwhile hypothesis remains and a bounded search identifies
   no new worthwhile hypothesis.

Prefer eliminating unnecessary work over accelerating it. Question computation,
representations, copies, allocation, ownership transitions, and synchronization.
Consider simpler representations, batching, parallelization, pipelining, and
asynchronous execution; no mechanism is inherently faster. Treat cadence,
ordering, service boundaries, and work-in-flight limits as design choices unless
required. Preserve correctness and consumer guarantees, and reuse common logic.
Use subagents for independent research, implementation, and assumption checks
when they accelerate progress without conflicting edits or competing measurements.
