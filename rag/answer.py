"""Answer questions from retrieved chunks, with citations and an 'I don't know' guardrail."""
from __future__ import annotations

import os
from dataclasses import dataclass

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


def build_prompt(question: str, hits: list[Hit]) -> str:
    context = "\n\n".join(f"[{i}] ({h.source}) {h.text}" for i, h in enumerate(hits, 1))
    return f"Context:\n{context}\n\nQuestion: {question}"


def relevant(hits: list[Hit]) -> list[Hit]:
    return [h for h in hits if h.distance <= MAX_DISTANCE]


def answer(store: DocStore, question: str, k: int = 4) -> Answer:
    hits = relevant(store.search(question, k))
    if not hits:
        return Answer(NO_ANSWER, [], grounded=False)
    sources = sorted({h.source for h in hits})
    if not os.environ.get("ANTHROPIC_API_KEY"):
        # No LLM available: fall back to the best matching passage, still with its source.
        return Answer(f"(extractive, no LLM key set) {hits[0].text}", sources, grounded=True)
    import anthropic

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(question, hits)}],
    )
    return Answer(message.content[0].text, sources, grounded=True)
