---
name: docs-rag
description: Use when the user asks a question that should be answered from their markdown documentation (guides, runbooks, internal docs), or wants to find which doc covers a topic. Uses the docs-rag MCP server tools search_docs, ask_docs and reindex. Not for general knowledge questions or non-markdown files.
---

# Searching documentation with docs-rag

Requires the `docs-rag` MCP server to be configured (see the repo README). Tools: `search_docs`, `ask_docs`, `reindex`.

## Choosing a tool

- **`search_docs(query, k=4)`**: default choice. Returns raw chunks with `source`, `heading`, `text` and `distance` (lower is closer). Read the chunks yourself, answer in your own words, and cite `source` and `heading`.
- **`ask_docs(question)`**: use when the user wants a ready, cited answer. It returns `answer`, `sources` and `grounded`. If `grounded` is false, the docs did not contain the answer: tell the user that, and do not fill the gap from general knowledge without saying so. Without `ANTHROPIC_API_KEY` it returns the best passage verbatim (prefixed "extractive, no LLM key set") with `grounded: true`: treat it as a quote, cite it, paraphrase it if the user wants a direct answer, and say that it is a verbatim passage because no LLM key is configured.
- **`reindex()`**: only after the user says the docs changed, or when searches return nothing for topics they know exist. It rebuilds the whole index.

## How to search well

1. Rephrase the user's question into the terms the docs likely use (a short noun phrase beats a full sentence, e.g. "index not used in WHERE clause" rather than "why is my query still slow"). If the best distance is above 0.5 and the top chunk looks plausibly relevant, rephrase once to confirm, using terms from the user's question rather than from a chunk you have already seen (the goal is to check that the match is stable, not to push the distance down). If the same chunk is still the best, answer from it; if not, try one more rephrasing before giving up. If rule 4 already shows that the top chunk only covers a related subject, skip the rephrase and say the docs do not cover it. A lower distance after rephrasing is not evidence that the topic is covered: apply rule 4 to the text again. If the best distance is above 0.75, one rephrase is enough before saying the docs do not cover it. For a question plainly outside the docs (general knowledge), one search is enough.
2. Use a larger `k` (6-8) for broad questions that may span several docs.
3. Judge matches by `distance` (cosine, lower is closer). On the sample corpus, correct chunks scored 0.3-0.75 (loosely worded questions reach 0.7+), unrelated questions scored 0.85+, and questions on a nearby topic that the docs do not cover (e.g. MongoDB indexes, `git cherry-pick`, Kubernetes) scored 0.54-0.76. Use these as a guide:
   - below 0.5: strong match, answer from it.
   - 0.5-0.75: plausible, but distance cannot tell a correct match from an off-topic one here. Verify with rule 4.
   - above 0.75 (the `RAG_MAX_DISTANCE` default that `ask_docs` applies): treat as not covered. Say the docs do not seem to cover the topic rather than stretching a chunk to fit.
   Other corpora may score differently, so these numbers are a starting point.
4. Check that the chunk answers the question, not just that it is on the same topic. Read the text and confirm it states what the user asked for (the specific tool, command, product or fact). If it only covers a related subject (a question about MongoDB indexes matching the SQL indexing doc, or `git cherry-pick` matching the rebase section), say the docs do not cover it, and mention the related section only as a pointer. This applies to `ask_docs` too: its 0.75 cutoff does not catch near-topic questions, so read its answer and sources critically before relaying it. In extractive mode (no LLM key), `grounded: true` only means the distance was under the cutoff, not that the passage answers the question: always apply this rule to the quoted chunk before relaying it.
5. `search_docs` always returns `k` chunks, even when nothing is relevant (the 0.75 cutoff is applied only by `ask_docs`). If the best distance is above 0.75, ignore the chunks and say the docs do not cover it.
6. Distance is not relevance. For any question, scan all `k` chunks for one that states the answer, even if it is not the top result (the right chunk was ranked 2nd or 3rd for "what does a 409 mean" and "run several services with one command"). For ambiguous questions, pick the chunk that best matches the intent of the question, even if another has a slightly lower distance (for "why isn't my index used", "Common pitfalls" beats "Costs"). For troubleshooting-style questions (why, not working, still slow, error), scan all returned chunks, not just the top one, and prefer the troubleshooting section (pitfalls, gotchas) even when another chunk is below 0.5.
7. Never present content as coming from the docs unless a returned chunk supports it.

## Answer format

- Lead with the answer, then list sources as `file.md > Heading`.
- Quote only the short passages that matter; summarize the rest.
- If chunks disagree, point out both and their sources.

## Limits to mention when relevant

- Only markdown is indexed (no PDF or images).
- Retrieval is dense-only, so exact identifiers or error codes can be missed. Try searching the surrounding concept instead.
