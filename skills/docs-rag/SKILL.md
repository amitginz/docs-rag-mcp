---
name: docs-rag
description: Use when the user asks a question that should be answered from their markdown documentation (guides, runbooks, internal docs), or wants to find which doc covers a topic. Uses the docs-rag MCP server tools search_docs, ask_docs and reindex. Not for general knowledge questions or non-markdown files.
---

# Searching documentation with docs-rag

Requires the `docs-rag` MCP server to be configured (see the repo README). Tools: `search_docs`, `ask_docs`, `reindex`.

## Choosing a tool

- **`search_docs(query, k=4)`**: default choice. Returns raw chunks with `source`, `heading`, `text` and `distance` (lower is closer). Read the chunks yourself, answer in your own words, and cite `source` and `heading`.
- **`ask_docs(question)`**: use when the user wants a ready, cited answer. It returns `answer`, `sources` and `grounded`. If `grounded` is false, the docs did not contain the answer: tell the user that, and do not fill the gap from general knowledge without saying so.
- **`reindex()`**: only after the user says the docs changed, or when searches return nothing for topics they know exist. It rebuilds the whole index.

## How to search well

1. Rephrase the user's question into the terms the docs likely use (a short noun phrase beats a full sentence). If the first search is weak, try one or two rephrasings before giving up.
2. Use a larger `k` (6-8) for broad questions that may span several docs.
3. Treat results with high `distance` as weak matches. If every chunk is far, say the docs do not seem to cover the topic rather than stretching a chunk to fit.
4. Never present content as coming from the docs unless a returned chunk supports it.

## Answer format

- Lead with the answer, then list sources as `file.md > Heading`.
- Quote only the short passages that matter; summarize the rest.
- If chunks disagree, point out both and their sources.

## Limits to mention when relevant

- Only markdown is indexed (no PDF or images).
- Retrieval is dense-only, so exact identifiers or error codes can be missed. Try searching the surrounding concept instead.
