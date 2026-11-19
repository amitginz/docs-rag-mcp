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

### Optional relevance gate (cross-encoder)

Set `RAG_RERANK=1` (after `pip install -r requirements-rerank.txt`) to add a second stage: a small
cross-encoder (`ms-marco-MiniLM-L-6-v2` via ONNX, no torch) reads each *(question, passage)* pair
and drops passages scoring below `RAG_RERANK_MIN` (default -4.0), re-ordering the rest. If nothing
survives, the pipeline refuses. It is off by default.

Measured with AgentProbe on `eval/eval_holdout.json` (15 in-scope, 10 near-topic
out-of-scope questions, written before any tuning and scored once per configuration):

| Configuration | In-scope found | Refused | Pass |
|---|---|---|---|
| Default (distance 0.75, no gate) | 15/15 | 3/10 | 18/25 |
| Gate, min -10 (best on the training sets) | 15/15 | 5/10 | 20/25 |
| Gate, min -4 | 12/15 | 8/10 | 20/25 |
| Distance cutoff only, 0.60 | 13/15 | 8/10 | 21/25 |

The gate helps over the default (min -10 adds two correct refusals and loses nothing), but it did
**not** clearly beat simply tightening the distance cutoff, and none of the differences are
statistically significant at this sample size (exact McNemar p = 0.5 and 0.73 against the
default). Treat it as a modest, unproven improvement; a larger eval set is the next step.

#### Update: second held-out set (72 questions, pre-registered)

`eval/eval_holdout2.json` (36 in-scope, 36 near-topic out-of-scope) was written before scoring, and
four configurations were fixed in advance and scored once each:

| Configuration | In-scope found | Refused | vs default (exact McNemar) |
|---|---|---|---|
| Default (distance 0.75, no gate) | 36/36 | 10/36 | n/a |
| Gate, min -10 | 35/36 | 11/36 | p = 1.00 (no effect) |
| Gate, min -4 (the default `RAG_RERANK_MIN`) | 34/36 | 24/36 | p = 0.004 |
| Distance cutoff only, 0.60 | 32/36 | 26/36 | p = 0.012 |

The gate setting selected on the smaller sets (-10) did not replicate. A gate at -4 and a plain
`RAG_MAX_DISTANCE=0.60` both lift near-topic refusals from 28% to roughly 70% and are statistically
indistinguishable from each other, at the cost of 2-4 of 36 in-scope questions. If near-topic refusal
matters more than recall, lowering `RAG_MAX_DISTANCE` to about 0.60 is the simpler option; the gate
is the alternative if you want to keep a looser distance cutoff. The shipped default is unchanged.

## Limitations

- The distance cutoff refuses unrelated questions but not near-topic ones the docs do not cover; they can be answered from an off-topic chunk. The optional relevance gate above reduces this but does not eliminate it. The agent skill tells the agent to check chunk content itself.

- Sample corpus is six short markdown files; real corpora need larger eval sets.
- Only markdown is supported (no PDF/OCR parsing yet).
- Retrieval is dense-only; hybrid search or a reranker would help on larger collections.
- The LLM answer path (`ask_docs` with an API key) is thin and not covered by automated tests, since it needs a live API call.
