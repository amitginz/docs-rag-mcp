"""Second-stage relevance gate: a cross-encoder reads (question, passage) together.

Embedding distance compares two independently computed vectors, so a near-topic question such as
"How do I create an index in MongoDB?" lands close to the SQL-indexing passage even though the
passage cannot answer it. A cross-encoder scores the pair jointly and separates "about the same
topic" from "actually answers this". Hits scoring below `min_score` are dropped; the survivors
are re-ordered by score. If nothing survives the caller refuses to answer.

Optional dependency: `pip install -r requirements-rerank.txt` (fastembed, ONNX, no torch).
"""
from __future__ import annotations

import os
from dataclasses import replace
from typing import Protocol

from .store import Hit

DEFAULT_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"


class Gate(Protocol):
    def apply(self, question: str, hits: list[Hit]) -> list[Hit]: ...


class CrossEncoderGate:
    def __init__(self, min_score: float, model: str = DEFAULT_MODEL) -> None:
        self.min_score = min_score
        self.model_name = model
        self._model = None  # loaded on first use: it downloads weights and takes seconds

    def _load(self):
        if self._model is None:
            try:
                from fastembed.rerank.cross_encoder import TextCrossEncoder
            except ImportError as exc:
                raise RuntimeError(
                    "the reranker gate needs fastembed: pip install -r requirements-rerank.txt"
                ) from exc
            self._model = TextCrossEncoder(self.model_name)
        return self._model

    def apply(self, question: str, hits: list[Hit]) -> list[Hit]:
        if not hits:
            return []
        scores = list(self._load().rerank(question, [h.text for h in hits]))
        scored = [replace(h, score=float(s)) for h, s in zip(hits, scores)]
        kept = [h for h in scored if h.score >= self.min_score]
        return sorted(kept, key=lambda h: h.score, reverse=True)


def gate_from_env() -> Gate | None:
    """RAG_RERANK=1 enables the gate; RAG_RERANK_MIN sets the score cutoff."""
    if os.environ.get("RAG_RERANK", "").lower() not in ("1", "true", "yes"):
        return None
    return CrossEncoderGate(float(os.environ.get("RAG_RERANK_MIN", "-4.0")))
