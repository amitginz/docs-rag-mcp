"""Relevance-gate logic, tested with fakes so no model download is needed."""
import pytest

from rag.answer import NO_ANSWER, answer
from rag.rerank import CrossEncoderGate, gate_from_env
from rag.store import Hit


def hit(name: str, distance: float = 0.3) -> Hit:
    return Hit(source=f"{name}.md", heading=name, text=f"text about {name}", distance=distance)


class FakeStore:
    def __init__(self, hits):
        self.hits, self.requested_k = hits, None

    def search(self, query, k=4):
        self.requested_k = k
        return self.hits[:k]


class FakeGate:
    def __init__(self, transform):
        self.transform, self.seen = transform, None

    def apply(self, question, hits):
        self.seen = list(hits)
        return self.transform(hits)


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("RAG_RERANK", raising=False)


def test_gate_that_rejects_everything_makes_the_pipeline_refuse():
    store = FakeStore([hit("a"), hit("b")])
    result = answer(store, "near-topic but unanswerable", gate=FakeGate(lambda hits: []))
    assert result.text == NO_ANSWER and not result.grounded and result.sources == [] and result.hits == ()


def test_gate_reorders_hits_and_the_best_one_drives_the_answer():
    store = FakeStore([hit("a"), hit("b"), hit("c")])
    result = answer(store, "q", gate=FakeGate(lambda hits: list(reversed(hits))))
    assert [h.heading for h in result.hits] == ["c", "b", "a"]
    assert "text about c" in result.text


def test_with_a_gate_more_candidates_are_fetched_but_only_k_survive():
    store = FakeStore([hit(str(i)) for i in range(20)])
    gate = FakeGate(lambda hits: hits)
    result = answer(store, "q", k=2, gate=gate)
    assert store.requested_k == 6 and len(gate.seen) == 6  # candidate factor of 3
    assert len(result.hits) == 2


def test_without_a_gate_behaviour_is_unchanged():
    store = FakeStore([hit(str(i)) for i in range(20)])
    result = answer(store, "q", k=2, gate=None)
    assert store.requested_k == 2 and len(result.hits) == 2


def test_distance_filter_still_runs_before_the_gate():
    store = FakeStore([hit("near", 0.3), hit("far", 0.9)])
    gate = FakeGate(lambda hits: hits)
    answer(store, "q", gate=gate)
    assert [h.heading for h in gate.seen] == ["near"]


def test_gate_is_off_by_default_and_enabled_by_env(monkeypatch):
    assert gate_from_env() is None
    monkeypatch.setenv("RAG_RERANK", "1")
    monkeypatch.setenv("RAG_RERANK_MIN", "-7.5")
    gate = gate_from_env()
    assert isinstance(gate, CrossEncoderGate) and gate.min_score == -7.5


def test_explicit_none_beats_the_environment(monkeypatch):
    monkeypatch.setenv("RAG_RERANK", "1")
    store = FakeStore([hit("a")])
    assert answer(store, "q", gate=None).grounded  # would raise if it tried to load the model


def test_cross_encoder_gate_filters_by_score_and_sorts_best_first():
    class StubModel:
        def rerank(self, question, passages):
            return [{"text about a": -9.0, "text about b": 2.5, "text about c": -3.0}[p] for p in passages]

    gate = CrossEncoderGate(min_score=-5.0)
    gate._model = StubModel()
    kept = gate.apply("q", [hit("a"), hit("b"), hit("c")])
    assert [h.heading for h in kept] == ["b", "c"]
    assert [h.score for h in kept] == [2.5, -3.0]
    assert gate.apply("q", []) == []


def test_missing_dependency_gives_an_actionable_error(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name.startswith("fastembed"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(RuntimeError, match="requirements-rerank.txt"):
        CrossEncoderGate(-4.0).apply("q", [hit("a")])
