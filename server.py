"""MCP server exposing the document RAG pipeline as tools for Claude and other MCP clients."""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from rag.answer import answer
from rag.store import DocStore

ROOT = Path(__file__).parent
DOCS_DIR = Path(os.environ.get("RAG_DOCS_DIR", ROOT / "docs"))
store = DocStore(os.environ.get("RAG_DB_DIR", ROOT / ".chroma"))
if store.search("test", 1) == []:
    store.index(DOCS_DIR)

mcp = FastMCP("docs-rag")


@mcp.tool()
def search_docs(query: str, k: int = 4) -> list[dict]:
    """Return the k most relevant document chunks for a query, with source and distance."""
    return [
        {"source": h.source, "heading": h.heading, "text": h.text, "distance": round(h.distance, 3)}
        for h in store.search(query, k)
    ]


@mcp.tool()
def ask_docs(question: str) -> dict:
    """Answer a question from the indexed docs with citations, or say it does not know."""
    result = answer(store, question)
    return {"answer": result.text, "sources": result.sources, "grounded": result.grounded}


@mcp.tool()
def reindex() -> str:
    """Rebuild the index from the docs directory."""
    return f"Indexed {store.index(DOCS_DIR)} chunks from {DOCS_DIR}"


if __name__ == "__main__":
    mcp.run()
