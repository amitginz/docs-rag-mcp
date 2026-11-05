# docs-rag-mcp

A small retrieval-augmented generation (RAG) service over a folder of markdown documents, exposed as an **MCP server** so Claude (or any MCP client) can search and ask questions about the docs. It includes an **evaluation set and CI checks** so changes to chunking, retrieval or thresholds cannot silently make answers worse.

## How it works

```
docs/*.md ──> heading-aware chunking ──> embeddings (ChromaDB, all-MiniLM-L6-v2) ──> vector store
                                                                                         │
question ──> top-k retrieval ──> distance guardrail ──> LLM answer with [n] citations <──┘
                                       │
                              too far from every chunk  ──>  "I don't know"
```

- **Chunking** (`rag/chunking.py`): splits by markdown heading, then into ~120-word overlapping pieces; each chunk keeps its heading and source file.
- **Store** (`rag/store.py`): local persistent ChromaDB with cosine distance and its default ONNX embedding model (no GPU or API key needed for retrieval).
- **Answering** (`rag/answer.py`): retrieves the top chunks, drops those above `RAG_MAX_DISTANCE`, and asks the model to answer only from the numbered context and cite sources. If nothing relevant is retrieved it replies "I don't know" instead of guessing. Without `ANTHROPIC_API_KEY` it falls back to returning the best passage.
- **MCP server** (`server.py`): tools `search_docs`, `ask_docs` and `reindex`.

## Run it

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python cli.py index docs
python cli.py search "how do I avoid blocking the event loop"
ANTHROPIC_API_KEY=... python cli.py ask "When should I use git revert?"
```

### Use it from Claude

Add to your MCP client configuration (for example Claude Desktop's `claude_desktop_config.json`), with absolute paths:

```json
{
  "mcpServers": {
    "docs-rag": {
      "command": "/path/to/docs-rag-mcp/.venv/bin/python",
      "args": ["/path/to/docs-rag-mcp/server.py"],
      "env": { "ANTHROPIC_API_KEY": "..." }
    }
  }
}
```

Point it at your own documents with `RAG_DOCS_DIR=/path/to/markdown`.

### Agent skill

`skills/docs-rag/SKILL.md` tells an agent when and how to use the tools (which tool to pick, how to rephrase queries, how to treat weak matches). To use it in Claude Code, copy it to `~/.claude/skills/docs-rag/`.

## Evaluation and tests

`eval/eval_set.json` holds 12 questions with the document that should answer each, plus 3 out-of-scope questions that must be refused.

```bash
python eval/run_eval.py     # hit@3, mean reciprocal rank, refusal rate
python -m pytest -q         # unit tests + retrieval quality gate (also runs in CI)
```

Current results on the sample corpus: hit@3 = 1.0, MRR = 1.0, refusal rate = 1.0. The corpus is small, so these numbers mostly protect against regressions; they are not a general benchmark.

`eval/eval_hard.json` is a tougher held-out set: 16 loosely worded in-scope questions (all found in the top 3) and 6 out-of-scope questions on topics near the docs, such as MongoDB indexes or `git cherry-pick`. It is not part of the CI gate. Only 1 of those 6 is refused by the `RAG_MAX_DISTANCE` cutoff, because near-topic questions score 0.54-0.76 while correct matches score up to 0.75.

## Limitations

- The distance cutoff refuses unrelated questions but not near-topic ones the docs do not cover; they can be answered from an off-topic chunk. A relevance check (for example an LLM verifying that the chunk answers the question) would be needed to fix this. The agent skill tells the agent to check chunk content itself.

- Sample corpus is six short markdown files; real corpora need larger eval sets.
- Only markdown is supported (no PDF/OCR parsing yet).
- Retrieval is dense-only; hybrid search or a reranker would help on larger collections.
- The LLM answer path (`ask_docs` with an API key) is thin and not covered by automated tests, since it needs a live API call.
