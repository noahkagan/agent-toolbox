---
name: maintain-notes
description: Write and maintain concise, linked Markdown notes without duplicated information. Use when creating, editing, splitting, organizing, auditing, or reviewing notes whose product needs, knowledge, decisions, experiments, or uncertainty evolve over time.
---

# Maintain Notes

Treat linked notes as an implicit graph.

## Choose note location by ownership

Before choosing a note location across repositories, identify the project that owns
the work, decision, or uncertainty. Write there. Referenced repositories own
notes only about their own work. If ownership is unclear, propose a location
and ask.

## Write

1. Inspect existing notes, code, tests, artifacts, and external sources before writing.
2. Give each piece of information one canonical home. Reference that source everywhere else. Never repeat or summarize another document.
3. Keep one concept per document. Name new files for that concept using lowercase kebab-case. Do not encode type, status, date, or sequence in filenames.
4. Keep each document at or below 500 words, excluding frontmatter. Split by concept before exceeding the limit.
5. Use frontmatter only for a maintained `keywords` list. Add only keywords that improve search. Do not encode state or relationships in metadata.
6. Write links in fluent prose that explains why the linked concept matters here. Prefer the most specific existing source over a new explanation.
7. State product needs, observations, uncertainty, and decisions directly. Do not present a guess, decision, or repeated assertion as knowledge.
8. Use one noun and verb for each concept. Normalize competing terms across the scope. Separate terms only when they name a real distinction.

## Keep a linear narrative

Write each note as a linear argument from the current decision, observation, or
product need through its evidence, constraints, and unselected alternatives to
the remaining uncertainty. Describe current state; include chronology only when
it affects current behavior. Give each version's scope one canonical home.

## Maintain the uncertainty frontier

Explicitly define the current uncertainty frontier: the boundary between settled product needs, knowledge, or decisions and undefined product needs or unanswered questions.

The frontier may span documents. Give each undefined product need or unanswered question one canonical home and mark it clearly. Link it to relevant observations, experiments, sources, or decisions. Other documents reference that canonical statement without summarizing it.

Progressively advance the frontier as people define product needs, develop knowledge, or make decisions. Define a product need only through an explicit product decision; never infer it from a technical design. Resolve unknowns through research, exploration, or experimentation that produces knowledge. A human may also resolve an unknown through an explicit decision without proof. Record the resulting knowledge or decision in its canonical document, then update the frontier. Add sharper or newly exposed unknowns when warranted. Advancement does not require the frontier to shrink.

## Revise

- Edit the canonical document when information changes.
- Update links when a document moves, splits, or changes meaning.
- Preserve undefined product needs until an explicit product decision defines them. Preserve other uncertainty until a finding or explicit decision resolves it.
- Remove repeated text after replacing it with a reference.
- Avoid indexes, registries, and directory hierarchies until links alone fail in a concrete case.

## Verify

Apply these checks to the requested notes during an audit and to changed documents after an edit.

- Confirm each scoped document has one concept and no more than 500 body words.
- Confirm each scoped document's frontmatter contains only `keywords`.
- Check each scoped link and its target.
- Search for repeated claims and competing terms. Replace copies with contextual canonical links and normalize every concept to its one noun and verb.
- Read every scoped note in order after structural edits. Check linear flow and contextual links.
- Confirm undefined product needs and unanswered questions are clearly marked, linked, and not implicitly closed.
