---
name: design-high-throughput
description: Assess whether a proposed or existing system design can achieve high throughput, even if it does not currently do so. Use when the user needs to find throughput bottlenecks, evaluate capacity or scalability, or reason about queueing, backpressure, partitioning, batching, or load shedding.
---

# Assess high-throughput designs

Treat throughput as useful, correct work completed per unit time under the required operating conditions. Do not optimize for parallelism alone.

1. Establish the target workload, service objectives, correctness requirements, and growth horizon. State unknowns and assumptions explicitly.
2. Map how work enters, moves through, waits in, and exits the system. Identify dependencies, shared ownership, blocking points, work-in-flight, and recovery paths.
3. Identify the constraint that limits sustained progress. Distinguish observed evidence from a hypothesis, and prefer measurement to intuition.
4. Assess whether overload remains controlled: work must be bounded, failure pressure must not amplify, and slow work must not unnecessarily stop independent work.
5. Recommend the smallest change that removes the demonstrated constraint. Explain the new flow of work and the correctness, operational, and complexity costs it introduces.
6. Define proof before implementation: a representative workload, success measures, saturation signals, failure cases, and the resulting capacity limit.

## Review output

Report, in order:

1. **Current execution model** — how work flows and where it waits.
2. **Throughput constraint** — the limiting resource or coordination point, with evidence and uncertainty.
3. **Recommended change** — the bottleneck addressed, expected effect, tradeoffs, and why it is the smallest viable intervention.
4. **Validation** — how to measure sustained throughput, latency, work-in-flight, errors, retries, and saturation before and after the change.

Prefer changes that remove unnecessary coordination and make flow control explicit. Do not add concurrency, asynchronous execution, queues, or distributed components unless they remove a specific constraint.
