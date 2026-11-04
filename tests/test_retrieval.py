"""Retrieval quality gate: fails CI if a change makes search worse."""
import pytest

from eval.run_eval import ROOT, evaluate
from rag.answer import NO_ANSWER, answer
from rag.store import DocStore


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    s = DocStore(tmp_path_factory.mktemp("chroma"))
    s.index(ROOT / "docs")
    return s


def test_retrieval_metrics(store):
    metrics = evaluate(store)
    assert metrics["hit@3"] >= 0.9
    assert metrics["mrr"] >= 0.8
    assert metrics["refusal_rate"] == 1.0


def test_out_of_scope_question_is_refused(store, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = answer(store, "What is the capital of France?")
    assert result.text == NO_ANSWER and not result.grounded and result.sources == []
