---
name: design-high-throughput
description: Assess whether a proposed or existing system design can achieve high throughput, even if it does not currently do so. Use when the user needs to find throughput bottlenecks, evaluate capacity or scalability, or reason about queueing, backpressure, partitioning, batching, or load shedding.
---

# Assess high-throughput designs

Treat throughput as useful, correct work completed per unit time under the required operating conditions. Do not optimize for parallelism alone.

1. Establish the target workload, service objectives, correctness requirements, and growth horizon. State unknowns and assumptions explicitly.
2. Map how work enters, moves through, waits in, and exits the system. Distinguish required dependencies from coordination imposed by the implementation; identify blocking points, work-in-flight, and recovery paths.
3. Identify the constraint that limits sustained progress. Distinguish observed evidence from a hypothesis, and prefer measurement to intuition.
4. Assess whether overload remains controlled: work must be bounded, failure pressure must not amplify, and slow work must not unnecessarily stop independent work.
5. Recommend the simplest complete flow that addresses the constraint, not merely the smallest diff. Explain deleted coordination and new correctness, operational, and complexity costs.
6. Define proof before implementation: a representative workload, success measures, saturation signals, failure cases, and the resulting capacity limit.

## Examine progress and its cost

Ask whether production or admission can advance independently of downstream delivery through bounded storage. Preserve the meaning of acceptance and completion; buffering absorbs bursts but does not increase downstream capacity.

Keep completion handling short when substantial processing would prevent other work from progressing. Compare continuing locally with handing off to processing capacity. Fuse cheap work when safe; add a boundary only when independent progress justifies scheduling, synchronization, storage, and locality costs.

For each proposed asynchronous boundary, specify capacity, saturation behavior, payload storage lifetime, and ownership of shutdown, including draining or cancellation. Preserve required ordering, readiness, service authority, and external process boundaries. Analysis does not authorize behavior or deployment changes.

Estimate how per-consumer work, RPC chains, copies, contention, serialized fan-out, and slowest-consumer waits grow with load and consumer count. Distribution and extra queues can increase these costs even when a diagram looks simpler.

## Review output

Report, in order:

1. **Current execution model** — how work flows, where it waits, and which dependencies are required.
2. **Throughput constraint** — the limiting resource or coordination point. Distinguish structural hypotheses, measured bottlenecks, and demonstrated improvements; without measurements, propose an experiment rather than claim a speedup.
3. **Recommended flow** — deleted coordination, expected effect, correctness obligations, and tradeoffs. Explain why fusion or separation earns its cost.
4. **Validation** — a falsifiable performance hypothesis and comparison workload. Measure sustained throughput, latency, work-in-flight, errors, retries, and saturation before and after the change.

Prefer changes that remove unnecessary coordination and make flow control explicit. Do not add concurrency, asynchronous execution, queues, or distributed components unless they remove a specific constraint.
