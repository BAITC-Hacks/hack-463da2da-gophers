import os

import pytest

from app.ai.contracts import EmployeeContext, Factor, ScoredCandidate
from app.ai.llm import explainer


def make_ctx(**over) -> EmployeeContext:
    fields = dict(
        employee_id="E9001",
        full_name="Test Person",
        role="Backend Engineer",
        grade="Middle",
        tenure_months=48,
        preferred_language="ru",
        next_role="Backend Engineer",
        next_grade="Senior",
        skill_gaps=[{"skill_id": "SK_SYSTEM_DESIGN", "name": "System Design", "current": 2, "required": 4, "gap": 2, "critical": True}],
        history_summary={"total": 7, "completion_rate": 0.43},
        recent_events=[],
    )
    fields.update(over)
    return EmployeeContext(**fields)


def make_candidate() -> ScoredCandidate:
    return ScoredCandidate(
        event_id="EV_SD_COURSE",
        title="System Design Intensive",
        score=0.467,
        factors=[
            Factor(type="skill_gap", message="Closes 1 of 2 level(s) to reach 4 in System Design (2 now)", skill_id="SK_SYSTEM_DESIGN", weight=0.258),
            Factor(type="critical_skill", message="System Design is critical for the Senior grade", skill_id="SK_SYSTEM_DESIGN", weight=0.129),
            Factor(type="history_pattern", message="2 of 2 'course' activities completed previously", weight=0.125),
            Factor(type="prerequisites_met", message="No prerequisites required", weight=0.05),
            Factor(type="grade_fit", message="Aligned with the Senior transition target", weight=0.1),
            Factor(type="session_availability", message="Next session on 2026-10-10 (in 9 days)", weight=0.1),
        ],
    )


@pytest.fixture(autouse=True)
def _clean_cache(monkeypatch):
    explainer.clear_cache()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    yield
    explainer.clear_cache()


def test_openai_primary_and_language(monkeypatch):
    calls = {}

    def fake_openai(messages, timeout):
        calls["messages"] = messages
        calls["timeout"] = timeout
        return "Обоснование на русском"

    monkeypatch.setattr(explainer, "_call_openai", fake_openai)
    result = explainer.explain(make_candidate(), make_ctx(), "ru")
    assert result.engine == "openai"
    assert result.language == "ru"
    assert result.text == "Обоснование на русском"
    assert set(result.factors_used) >= {"skill_gap", "critical_skill", "history_pattern"}
    assert "Russian" in calls["messages"][0]["content"]
    assert "System Design" in calls["messages"][1]["content"]
    assert calls["timeout"] <= explainer.OPENAI_TIMEOUT_S


def test_kazakh_language_instruction(monkeypatch):
    seen = {}
    monkeypatch.setattr(explainer, "_call_openai", lambda m, t: (seen.setdefault("s", m[0]["content"]), "Tüsinikteme")[1])
    explainer.explain(make_candidate(), make_ctx(), "kk")
    assert "Kazakh" in seen["s"]


def test_nvidia_fallback_on_openai_failure(monkeypatch):
    monkeypatch.setattr(explainer, "_call_openai", lambda m, t: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(explainer, "_call_nvidia", lambda m, t: "Нәтиже")
    result = explainer.explain(make_candidate(), make_ctx(), "ru")
    assert result.engine == "nvidia"
    assert result.text == "Нәтиже"


def test_heuristic_when_both_providers_fail(monkeypatch):
    monkeypatch.setattr(explainer, "_call_openai", lambda m, t: (_ for _ in ()).throw(RuntimeError("down")))
    monkeypatch.setattr(explainer, "_call_nvidia", lambda m, t: (_ for _ in ()).throw(RuntimeError("down")))
    result = explainer.explain(make_candidate(), make_ctx(), "en")
    assert result.engine == "heuristic-fallback"
    assert "System Design" in result.text


def test_heuristic_when_no_keys(monkeypatch):
    result = explainer.explain(make_candidate(), make_ctx(), "ru")
    assert result.engine == "heuristic-fallback"


def test_cache_hit_avoids_second_call(monkeypatch):
    counter = {"n": 0}

    def fake_openai(messages, timeout):
        counter["n"] += 1
        return "Первый ответ"

    monkeypatch.setattr(explainer, "_call_openai", fake_openai)
    first = explainer.explain(make_candidate(), make_ctx(), "ru")
    second = explainer.explain(make_candidate(), make_ctx(), "ru")
    assert counter["n"] == 1
    assert first is second


def test_cache_invalidated_by_factor_change(monkeypatch):
    counter = {"n": 0}

    def fake_openai(messages, timeout):
        counter["n"] += 1
        return "Ответ"

    monkeypatch.setattr(explainer, "_call_openai", fake_openai)
    c1 = make_candidate()
    explainer.explain(c1, make_ctx(), "ru")
    c2 = make_candidate()
    c2.factors[0].weight = 0.9
    explainer.explain(c2, make_ctx(), "ru")
    assert counter["n"] == 2


def test_cache_separates_languages(monkeypatch):
    counter = {"n": 0}
    monkeypatch.setattr(explainer, "_call_openai", lambda m, t: counter.update(n=counter["n"] + 1) or "text")
    explainer.explain(make_candidate(), make_ctx(), "ru")
    explainer.explain(make_candidate(), make_ctx(), "en")
    assert counter["n"] == 2


def test_expired_cache_entry_recalled(monkeypatch):
    counter = {"n": 0}

    def fake_openai(messages, timeout):
        counter["n"] += 1
        return "Ответ"

    monkeypatch.setattr(explainer, "_call_openai", fake_openai)
    explainer.explain(make_candidate(), make_ctx(), "ru")
    key = explainer._cache_key(make_candidate(), make_ctx(), "ru")
    with explainer._cache_lock:
        _ts, value = explainer._cache[key]
        explainer._cache[key] = (0.0, value)
    again = explainer.explain(make_candidate(), make_ctx(), "ru")
    assert counter["n"] == 2
    assert again.text == "Ответ"


@pytest.mark.skipif(os.environ.get("LLM_LIVE_TEST") != "1", reason="live-тест только за флагом LLM_LIVE_TEST=1")
def test_live_openai_or_nvidia():
    result = explainer.explain(make_candidate(), make_ctx(), "ru")
    assert result.engine in ("openai", "nvidia", "heuristic-fallback")
    assert result.text
