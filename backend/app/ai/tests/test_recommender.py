from datetime import date

import pytest

from app.ai.contracts import Explanation
from app.ai.recommender import recommend
from app.ai.tests.fixtures import TODAY, jury_history, make_catalog, make_employee, make_events

TODAY_D = date.fromisoformat(TODAY)


def stub_explain(candidate, ctx, language):
    return Explanation(language=language, text=f"stub for {candidate.event_id}", factors_used=["skill_gap"], engine="openai")


def broken_explain(candidate, ctx, language):
    raise RuntimeError("LLM down")


def test_recommend_happy_path():
    result = recommend(
        "E9001",
        employees=[make_employee()],
        events=make_events(),
        skills_catalog=make_catalog(),
        history_rows=jury_history(),
        today=TODAY_D,
        explain_fn=stub_explain,
    )
    assert result.employee_id == "E9001"
    assert result.engine == "openai"
    assert 1 <= len(result.recommendations) <= 3
    assert [r.rank for r in result.recommendations] == list(range(1, len(result.recommendations) + 1))
    for rec in result.recommendations:
        assert len({f.type for f in rec.factors}) >= 3
        assert rec.explanation.language == "ru"
        assert rec.score >= 0


def test_recommend_fallback_when_llm_fails():
    result = recommend(
        "E9001",
        employees=[make_employee()],
        events=make_events(),
        skills_catalog=make_catalog(),
        history_rows=jury_history(),
        today=TODAY_D,
        explain_fn=broken_explain,
    )
    assert result.engine == "heuristic-fallback"
    assert all(r.explanation.engine == "heuristic-fallback" for r in result.recommendations)
    assert all(r.explanation.text for r in result.recommendations)


def test_recommend_explain_fn_none_disables_llm():
    result = recommend(
        "E9001",
        employees=[make_employee()],
        events=make_events(),
        skills_catalog=make_catalog(),
        history_rows=[],
        today=TODAY_D,
        explain_fn=None,
    )
    assert result.engine == "heuristic-fallback"


def test_recommend_unknown_employee():
    with pytest.raises(KeyError):
        recommend(
            "NOPE",
            employees=[make_employee()],
            events=make_events(),
            skills_catalog=make_catalog(),
            history_rows=[],
        )


def test_recommend_no_eligible_events_returns_empty():
    events = [e for e in make_events() if e["event_id"] == "EV_MAND"]
    result = recommend(
        "E9001",
        employees=[make_employee()],
        events=events,
        skills_catalog=make_catalog(),
        history_rows=[],
        today=TODAY_D,
        explain_fn=None,
    )
    assert result.recommendations == []
