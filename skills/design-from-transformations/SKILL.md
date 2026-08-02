---
name: design-from-transformations
description: Reduce an architecture, design, or implementation to its necessary data transformations and their physical realization. Use when evaluating or simplifying a system, choosing abstractions, designing an algorithm or data layout, or questioning whether components and actions are load-bearing.
---

# Design from transformations

Model the system as necessary transformations of data and the physical work that realizes them. Treat state, control flow, and coordination as part of that model.

1. State the required input, output, invariants, and performance objectives. Mark unknowns and avoid inventing requirements.
2. Describe each necessary transformation: what information changes, what representation it has before and after, and what guarantees must survive the change.
3. Trace its realization in the device: computation, storage, movement, ownership, synchronization, and interaction with the environment. Reason from the actual work performed, not from names of abstractions.
4. Identify every abstraction, component, process, and action that participates. Require each to justify itself by improving clarity, safety, or the stated performance objectives.
5. Remove, merge, or defer anything that does not carry a required transformation or guarantee. Prefer direct representations and flows when they make the system easier to verify.
6. Re-evaluate the remaining design against its objectives, including correctness and the relevant latency, throughput, memory, reliability, or maintainability constraints.

## Output

Present:

1. **Transformation model** — required changes of information and their guarantees.
2. **Physical model** — the work and resource behavior that realize them.
3. **Load-bearing structure** — what must remain and why.
4. **Removals or simplifications** — what does not earn its place, with any tradeoffs or uncertainty.

Do not preserve an abstraction merely because it is conventional, extensible, or familiar.
