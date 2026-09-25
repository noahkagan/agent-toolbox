---
name: optimize-from-evidence
description: Iteratively improve a target system's measured performance using data-transformation and high-throughput reasoning. Use for evidence-driven optimization through reproducible baselines, focused experiments, and validated implementation changes.
---

# Optimize from evidence

Start from required outputs and actual consumer needs. Before optimizing any
cost, determine whether the work is necessary. Prefer eliminating unnecessary
work over accelerating it.

## Establish the model and baseline

Trace computation, representation changes, data movement, allocation,
ownership, and synchronization from inputs to consumed outputs. Identify what
limits completed useful work.

Treat cadence, ordering, synchronization, and work-in-flight limits as design
variables unless explicitly required. Evaluate changes through end-to-end
performance and consumer behavior, not conformity to existing execution.
Preserve correctness, ownership, and completion guarantees.

Establish reproducible baselines for representative workloads and scales.
Record the revision, environment, inputs, commands, measurement boundaries,
and run-to-run variation needed to reproduce comparisons.

Use existing evidence first. Choose instrumentation and profiling tools to
resolve important uncertainties. Distinguish execution, waiting, and overlapping
work; do not sum overlapping durations as elapsed time. Measure completion,
not merely submission or work moved outside the measurement boundary.

## Experiment and qualify

Trace end-to-end producer-to-consumer paths across systems and services,
starting from what the original producer naturally provides and what the
final consumer actually needs. Treat service boundaries as design choices,
not limits on the analysis. Question intermediate representations, copies,
ownership transitions, and synchronization.

Use source inspection and targeted web research to develop competing ways
to connect those endpoints. Keep promising implementations selectable,
reuse common logic, and compare them across representative workloads and scales.

Rank hypotheses by expected performance impact, supporting evidence, and
experiment cost. Consider removing work, simplifying representations, batching,
parallelization, pipelining, and asynchronous execution. No mechanism is
inherently faster.

Before each leading experiment, recheck the assignment's tasks and notes for
previous findings and exclusions. State the hypothesis, expected outcome, and
evidence that would support or reject it. Revisit exclusions when new evidence
justifies doing so, and record that evidence.

Implement the leading hypothesis on top of accumulated improvements. Run
focused experiments that distinguish the proposed explanation from alternatives.
Keep measurements free from competing experiments or resource contention
introduced by the investigation.

Qualify the accumulated changes together against representative workloads.
Compare completed useful work and relevant consumer outcomes against both the
previous accumulated version and the original baseline under comparable
conditions. Measure incremental and total benefit. Check correctness, ownership,
and completion guarantees alongside performance. Distinguish measured changes
from run-to-run variation.

Improvements may target specific situations or scales; they need not benefit
every workload, provided they do not regress others. State the demonstrated
benefit and the limits of qualification. Make each improvement durable after
qualification passes, before starting the next iteration. Re-rank hypotheses
using the new evidence; the limiting constraint may have changed.
Stop when remaining hypotheses lack enough expected value to justify experiments.

## Preserve results

Make all demonstrated improvements durable in one draft PR per repository.
Update that PR as improvements accumulate. Include reproduction details,
before-and-after measurements, correctness checks, and qualification limits.
Do not merge the PRs.

Progressively publish concise tasks and notes to the assignment's designated
locations. Record hypotheses, expectations, observations, outcomes, exclusions,
reproduction details, and unresolved questions. Distinguish verified facts
from inference. Link canonical evidence instead of duplicating it.

Use subagents for independent research, implementation, and assumption checks
when they accelerate progress without conflicting edits or competing
measurements. Give each subagent a bounded scope and coordinate access to
measurement resources.
