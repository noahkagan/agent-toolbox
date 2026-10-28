---
name: design-from-transformations
description: Reduce an architecture, design, or implementation to its necessary data transformations and their physical realization. Use when evaluating or simplifying a system, choosing abstractions, designing an algorithm or data layout, or questioning whether components and actions are load-bearing.
---

# Design from transformations

Model the system as necessary transformations of data and the physical work that realizes them. Treat state, control flow, and coordination as part of that model.

1. State the required input, output, invariants, and performance objectives. Mark unknowns and avoid inventing requirements.
2. Derive producer → payload → transformation → consumer paths independently of existing classes, services, or deployment boundaries. Identify authoritative inputs, required representations, timestamps, and storage lifetime. Describe what each transformation changes and which guarantees survive it.
3. Trace its realization in the device: computation, storage, movement, ownership, synchronization, and interaction with the environment. Reason from the actual work performed, not from names of abstractions.
4. Identify every abstraction, component, process, and action that participates. Require each to justify itself by improving clarity, safety, or the stated performance objectives.
5. Propose removing, merging, or deferring anything that does not carry a required transformation or guarantee. Prefer direct representations and flows when they make the system easier to verify.
6. Re-evaluate the remaining design against its objectives, including correctness and the relevant latency, throughput, memory, reliability, or maintainability constraints.

## Derive boundaries instead of inheriting them

For each wait, identify the data availability, ordering, capacity, or lifetime requirement it protects. Compare these necessary dependencies with implementation-imposed dependencies; name any unsupported edge before optimizing its coordination.

Separate payload ownership, consumer progress, and execution ownership: who keeps bytes valid, what permits each consumer to advance, and which execution capacity performs the work. Shared data need not imply shared progress. Logical consistency need not require contiguous storage; establish readiness and lifetime for every part.

Challenge copies, intermediate representations, central forwarding, and duplicate lifecycle state. Ask whether contributors can fill one request before submission, or transformations can occur once near their source or only near consumers that need them.

Preserve externally required process boundaries, service authority, ordering, readiness, and lifetime guarantees. Distinguish those requirements from current placement; analysis does not authorize behavior or deployment changes.

## Output

Present:

1. **Current flow** — transformations and their physical realization.
2. **Necessary dependencies** — required inputs and guarantees versus implementation-imposed edges.
3. **Proposed flow** — ownership and placement, deleted coordination, and structure that must remain.
4. **Correctness and validation** — obligations, tradeoffs, and unknowns. For performance claims, state a falsifiable hypothesis and a measurement that could reject it; fewer components alone prove nothing.

Do not preserve an abstraction merely because it is conventional, extensible, or familiar.
