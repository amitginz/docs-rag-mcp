"""Answer questions from retrieved chunks, with citations and an 'I don't know' guardrail."""
from __future__ import annotations

import os
from dataclasses import dataclass

from .rerank import Gate, gate_from_env
from .store import DocStore, Hit

# Cosine distance above this means nothing relevant was found.
MAX_DISTANCE = float(os.environ.get("RAG_MAX_DISTANCE", "0.75"))
MODEL = os.environ.get("RAG_MODEL", "claude-sonnet-5-5")
NO_ANSWER = "I don't know: the indexed documents do not cover this question."

SYSTEM = (
    "Answer the question using only the numbered context passages. "
    "Cite passages like [1]. If the context does not contain the answer, reply exactly: "
    f"{NO_ANSWER}"
)


@dataclass(frozen=True)
class Answer:
    text: str
    sources: list[str]
    grounded: bool
    hits: tuple[Hit, ...] = ()  # the passages the answer was built from, best first


def build_prompt(question: str, hits: list[Hit]) -> str:
    context = "\n\n".join(f"[{i}] ({h.source}) {h.text}" for i, h in enumerate(hits, 1))
    return f"Context:\n{context}\n\nQuestion: {question}"


def relevant(hits: list[Hit]) -> list[Hit]:
    return [h for h in hits if h.distance <= MAX_DISTANCE]


_FROM_ENV = object()
CANDIDATE_FACTOR = 3  # with a gate, fetch more candidates so the reranker can promote good ones


def answer(store: DocStore, question: str, k: int = 4, gate: Gate | None | object = _FROM_ENV) -> Answer:
    """Answer from the docs. `gate` defaults to the RAG_RERANK environment setting; pass None to disable."""
    active: Gate | None = gate_from_env() if gate is _FROM_ENV else gate  # type: ignore[assignment]
    candidates = relevant(store.search(question, k * CANDIDATE_FACTOR if active else k))
    hits = active.apply(question, candidates)[:k] if active else candidates
    if not hits:
        return Answer(NO_ANSWER, [], grounded=False)
    sources = sorted({h.source for h in hits})
    if not os.environ.get("ANTHROPIC_API_KEY"):
        # No LLM available: fall back to the best matching passage, still with its source.
        return Answer(f"(extractive, no LLM key set) {hits[0].text}", sources, grounded=True, hits=tuple(hits))
    import anthropic

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(question, hits)}],
    )
    return Answer(message.content[0].text, sources, grounded=True, hits=tuple(hits))
