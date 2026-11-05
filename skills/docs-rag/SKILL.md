---
name: docs-rag
description: Use when the user asks a question that should be answered from their markdown documentation (guides, runbooks, internal docs), or wants to find which doc covers a topic. Uses the docs-rag MCP server tools search_docs, ask_docs and reindex. Not for general knowledge questions or non-markdown files.
---

# Searching documentation with docs-rag

Requires the `docs-rag` MCP server to be configured (see the repo README). Tools: `search_docs`, `ask_docs`, `reindex`.

## Choosing a tool

- **`search_docs(query, k=4)`**: default choice. Returns raw chunks with `source`, `heading`, `text` and `distance` (lower is closer). Read the chunks yourself, answer in your own words, and cite `source` and `heading`.
- **`ask_docs(question)`**: use when the user wants a ready, cited answer. It returns `answer`, `sources` and `grounded`. If `grounded` is false, the docs did not contain the answer: tell the user that, and do not fill the gap from general knowledge without saying so. Without `ANTHROPIC_API_KEY` it returns the best passage verbatim (prefixed "extractive, no LLM key set") with `grounded: true`: treat it as a quote, cite it, and paraphrase it if the user wants a direct answer.
- **`reindex()`**: only after the user says the docs changed, or when searches return nothing for topics they know exist. It rebuilds the whole index.

## How to search well

1. Rephrase the user's question into the terms the docs likely use (a short noun phrase beats a full sentence, e.g. "index not used in WHERE clause" rather than "why is my query still slow"). If the best distance is above 0.5, rephrase once to confirm: if the same chunk is still the best, answer from it; if not, try one more rephrasing before giving up.
2. Use a larger `k` (6-8) for broad questions that may span several docs.
3. Judge matches by `distance` (cosine, lower is closer). On the sample corpus, correct chunks mostly scored 0.3-0.65 (one at 0.68) and out-of-scope questions scored 0.85+. Use these as a guide:
   - below 0.5: strong match, answer from it.
   - 0.5-0.75: plausible, check that the chunk really answers the question.
   - above 0.75 (the `RAG_MAX_DISTANCE` default that `ask_docs` applies): treat as not covered. Say the docs do not seem to cover the topic rather than stretching a chunk to fit.
   Other corpora may score differently, so these numbers are a starting point.
4. `search_docs` always returns `k` chunks, even when nothing is relevant (the 0.75 cutoff is applied only by `ask_docs`). If the best distance is above 0.75, ignore the chunks and say the docs do not cover it.
5. Distance is not relevance. For ambiguous questions, pick the chunk that best matches the intent of the question, even if another has a slightly lower distance (for "why isn't my index used", "Common pitfalls" beats "Costs"). For "why / not working / still slow" questions, scan all returned chunks, not just the top one, and prefer the troubleshooting section (pitfalls, gotchas) even when another chunk is below 0.5.
6. Never present content as coming from the docs unless a returned chunk supports it.

## Answer format

- Lead with the answer, then list sources as `file.md > Heading`.
- Quote only the short passages that matter; summarize the rest.
- If chunks disagree, point out both and their sources.

## Limits to mention when relevant

- Only markdown is indexed (no PDF or images).
- Retrieval is dense-only, so exact identifiers or error codes can be missed. Try searching the surrounding concept instead.
