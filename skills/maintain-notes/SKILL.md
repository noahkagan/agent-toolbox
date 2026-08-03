---
name: maintain-notes
description: Write and maintain concise, linked Markdown notes without duplicated information. Use when creating, editing, splitting, organizing, or reviewing a note set whose product needs, knowledge, decisions, experiments, or uncertainty evolve over time.
---

# Maintain Notes

Treat a note set as an implicit graph connected by Markdown links. Add structure only when a demonstrated navigation problem requires it.

## Write

1. Inspect existing notes, code, tests, artifacts, and external sources before writing.
2. Give each piece of information one canonical home. Reference that source everywhere else. Never repeat or summarize another document.
3. Keep one concept per document. Name new files for that concept using lowercase kebab-case. Do not encode type, status, date, or sequence in filenames.
4. Keep each document at or below 500 words, excluding frontmatter. Split by concept before exceeding the limit.
5. Use frontmatter only for a maintained `keywords` list. Add only keywords that improve search. Do not encode state or relationships in metadata.
6. Express relationships with links in prose. Prefer the most specific existing note, code, test, artifact, or external source over a new explanation.
7. State product needs, observations, uncertainty, and decisions directly. Do not present a guess, decision, or repeated assertion as knowledge.

## Maintain the uncertainty frontier

Explicitly define the note set's current uncertainty frontier: the boundary between settled product needs, knowledge, or decisions and undefined product needs or unanswered questions.

Maintain the frontier in its own concept-named document. Let it own undefined product needs and unanswered questions. Link them to relevant observations, experiments, sources, or decisions. Other documents link to the frontier without summarizing it.

Progressively advance the frontier as people define product needs, develop knowledge, or make decisions. Define a product need only through an explicit product decision; never infer it from a technical design. Resolve another unknown through a referenced finding or explicit decision. Record the result in its canonical document, then update the frontier. Add sharper or newly exposed unknowns when warranted. Advancement does not require the frontier to shrink.

## Revise

- Edit the canonical document when information changes.
- Update links when a document moves, splits, or changes meaning.
- Preserve undefined product needs until an explicit product decision defines them. Preserve other uncertainty until a finding or explicit decision resolves it.
- Remove repeated text after replacing it with a reference.
- Avoid indexes, registries, and directory hierarchies until links alone fail in a concrete case.

## Verify

- Confirm every changed document has one concept and no more than 500 body words.
- Confirm frontmatter contains only `keywords`.
- Check every changed link and its target.
- Search for repeated claims and replace copies with canonical references.
- Confirm the uncertainty frontier includes undefined product needs and reflects recorded knowledge and decisions without implicit closure.
