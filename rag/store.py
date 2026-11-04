"""Vector store backed by ChromaDB (local, persistent, default ONNX embedding model)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb

from .chunking import chunk_directory

COLLECTION = "docs"


@dataclass(frozen=True)
class Hit:
    source: str
    heading: str
    text: str
    distance: float


class DocStore:
    def __init__(self, persist_dir: str | Path = ".chroma") -> None:
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def index(self, docs_dir: str | Path) -> int:
        """Rebuild the index from every markdown file under docs_dir. Returns chunk count."""
        self._client.delete_collection(COLLECTION)
        self._collection = self._client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"}
        )
        chunks = chunk_directory(Path(docs_dir))
        if chunks:
            self._collection.add(
                ids=[c.id for c in chunks],
                documents=[c.text for c in chunks],
                metadatas=[{"source": c.source, "heading": c.heading} for c in chunks],
            )
        return len(chunks)

    def search(self, query: str, k: int = 4) -> list[Hit]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(query_texts=[query], n_results=min(k, self._collection.count()))
        return [
            Hit(meta["source"], meta["heading"], doc, dist)
            for doc, meta, dist in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0]
            )
        ]
