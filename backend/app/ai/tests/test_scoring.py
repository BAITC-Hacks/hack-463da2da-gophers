from datetime import date

from app.ai.core.analyzer import analyze_profile
from app.ai.core.scoring import (
    _availability_component,
    effective_closing,
    is_eligible,
    rank_candidates,
)
from app.ai.tests.fixtures import (
    TODAY,
    hist,
    jury_history,
    make_catalog,
    make_employee,
    make_events,
)

TODAY_D = date.fromisoformat(TODAY)


def _setup(history_rows=None, employee=None):
    emp = employee or make_employee()
    events = make_events()
    ctx, gaps, metrics = analyze_profile(emp, make_catalog(), events, history_rows or [])
    return emp, events, ctx, gaps, metrics


def test_eligibility_filters():
    emp, events, ctx, gaps, metrics = _setup(jury_history())
    eligible = {
        e["event_id"]
        for e in events
        if is_eligible(e, emp, metrics, ctx.next_role, ctx.next_grade)
    }
    assert eligible == {"EV_SD_COURSE", "EV_PS_WORKSHOP", "EV_036"}


def test_mandatory_never_recommended():
    emp, events, ctx, gaps, metrics = _setup([])
    assert not is_eligible(events[2], emp, metrics, ctx.next_role, ctx.next_grade)


def test_recurring_event_allowed_after_completion():
    rows = jury_history() + [hist("E9001", "EV_036", "completed", "2026-07-01")]
    emp, events, ctx, gaps, metrics = _setup(rows)
    eligible = {
        e["event_id"]
        for e in events
        if is_eligible(e, emp, metrics, ctx.next_role, ctx.next_grade)
    }
    assert "EV_036" in eligible
    assert "EV_SYS_OLD" not in eligible


def test_prerequisite_blocks():
    emp, events, ctx, gaps, metrics = _setup([])
    ev = next(e for e in events if e["event_id"] == "EV_PREREQ")
    assert not is_eligible(ev, emp, metrics, ctx.next_role, ctx.next_grade)
    strong = make_employee(skills={"SK_PYTHON": 5, "SK_SYSTEM_DESIGN": 2, "SK_PUBLIC_SPEAKING": 3})
    _, _, ctx2, gaps2, metrics2 = _setup([], strong)
    assert is_eligible(ev, strong, metrics2, ctx2.next_role, ctx2.next_grade)


def test_gain_capped_by_max_level():
    develops = {"skill_id": "SK_X", "gain": 3, "max_level": 4}
    gap = {"current": 3, "required": 5}
    assert effective_closing(develops, gap) == 1


def test_gain_capped_by_requirement():
    develops = {"skill_id": "SK_X", "gain": 5, "max_level": 5}
    gap = {"current": 2, "required": 3}
    assert effective_closing(develops, gap) == 1


def test_availability_windows():
    near = {"format": "online", "upcoming_sessions": ["2026-10-10"]}
    late = {"format": "online", "upcoming_sessions": ["2026-11-10"]}
    far = {"format": "online", "upcoming_sessions": ["2027-06-01"]}
    past = {"format": "online", "upcoming_sessions": ["2025-01-01", "2026-10-02"]}
    assert _availability_component({"format": "self_paced"}, TODAY_D) == (1.0, "Self-paced: can start any time")
    assert _availability_component(near, TODAY_D)[0] == 1.0
    assert _availability_component(late, TODAY_D)[0] == 0.7
    assert _availability_component(far, TODAY_D)[0] == 0.4
    assert _availability_component(past, TODAY_D)[0] == 1.0


def test_ranking_no_gaps_still_returns_candidates():
    emp = make_employee(grade="Senior", skills={"SK_PYTHON": 4, "SK_SYSTEM_DESIGN": 4, "SK_PUBLIC_SPEAKING": 3}, career_goal=None)
    _, events, ctx, gaps, metrics = _setup([], emp)
    ranked = rank_candidates(emp, events, gaps, metrics, ctx.next_role, ctx.next_grade, today=TODAY_D)
    assert ranked, "даже без разрывов должны быть кандидаты (поддержание)"
    assert all(len({f.type for f in c.factors}) >= 3 for c in ranked)


def test_ranking_max_three():
    emp, events, ctx, gaps, metrics = _setup([])
    ranked = rank_candidates(emp, events, gaps, metrics, ctx.next_role, ctx.next_grade, today=TODAY_D)
    assert 1 <= len(ranked) <= 3


def test_ranking_sorted_desc():
    emp, events, ctx, gaps, metrics = _setup([])
    ranked = rank_candidates(emp, events, gaps, metrics, ctx.next_role, ctx.next_grade, today=TODAY_D)
    scores = [c.score for c in ranked]
    assert scores == sorted(scores, reverse=True)
