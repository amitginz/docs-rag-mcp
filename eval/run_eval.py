"""Retrieval evaluation: hit rate@k, mean reciprocal rank, and out-of-scope refusal rate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.answer import MAX_DISTANCE  # noqa: E402
from rag.store import DocStore  # noqa: E402


def evaluate(store: DocStore, k: int = 3) -> dict[str, float]:
    data = json.loads((ROOT / "eval" / "eval_set.json").read_text())
    hits_at_k, reciprocal = 0, 0.0
    for item in data["in_scope"]:
        sources = [h.source for h in store.search(item["q"], k)]
        if item["source"] in sources:
            hits_at_k += 1
            reciprocal += 1 / (sources.index(item["source"]) + 1)
    refused = sum(
        1 for q in data["out_of_scope"] if not [h for h in store.search(q, k) if h.distance <= MAX_DISTANCE]
    )
    n = len(data["in_scope"])
    return {
        f"hit@{k}": hits_at_k / n,
        "mrr": reciprocal / n,
        "refusal_rate": refused / len(data["out_of_scope"]),
    }


if __name__ == "__main__":
    store = DocStore(ROOT / ".chroma")
    store.index(ROOT / "docs")
    print(json.dumps(evaluate(store), indent=2))
