from app.ai.core.analyzer import (
    analyze_history,
    analyze_profile,
    analyze_skill_gaps,
    events_index,
    next_grade,
    resolve_target,
)
from app.ai.tests.fixtures import make_catalog, make_employee, make_events

import pytest


def test_next_grade_order():
    assert next_grade("Junior") == "Middle"
    assert next_grade("Middle") == "Senior"
    assert next_grade("Lead") is None


def test_resolve_target_from_career_goal():
    emp = make_employee()
    assert resolve_target(emp) == ("Backend Engineer", "Senior")


def test_resolve_target_without_goal_is_next_grade():
    emp = make_employee(career_goal=None)
    assert resolve_target(emp) == ("Backend Engineer", "Senior")


def test_resolve_target_lead_without_goal_stays():
    emp = make_employee(grade="Lead", career_goal=None)
    assert resolve_target(emp) == ("Backend Engineer", "Lead")


def test_gaps_only_unmet_sorted_critical_first():
    emp = make_employee()
    gaps = analyze_skill_gaps(emp, make_catalog(), "Backend Engineer", "Senior")
    by_id = {g["skill_id"]: g for g in gaps}
    assert by_id["SK_SYSTEM_DESIGN"] == {
        "skill_id": "SK_SYSTEM_DESIGN",
        "name": "System Design",
        "current": 2,
        "required": 4,
        "gap": 2,
        "critical": True,
    }
    assert by_id["SK_PUBLIC_SPEAKING"]["gap"] == 3
    assert by_id["SK_PUBLIC_SPEAKING"]["critical"] is False
    assert "SK_PYTHON" not in by_id
    assert gaps[0]["skill_id"] == "SK_SYSTEM_DESIGN"


def test_gaps_unknown_role_profile_is_empty():
    emp = make_employee(role="QA Engineer")
    assert analyze_skill_gaps(emp, make_catalog(), "QA Engineer", "Senior") == []


def test_history_metrics_counts_and_rates():
    from app.ai.tests.fixtures import hist

    rows = [
        hist("E1", "EV_A", "completed", "2026-01-01"),
        hist("E1", "EV_B", "completed", "2026-02-01"),
        hist("E1", "EV_C", "dropped", "2026-03-01", completion_pct=40),
        hist("E1", "EV_D", "no_show", "2026-04-01"),
    ]
    events = {eid: {"event_id": eid, "type": "course" if eid in ("EV_A", "EV_B") else "workshop"} for eid in ("EV_A", "EV_B", "EV_C", "EV_D")}
    m = analyze_history(rows, events)
    assert m["total"] == 4
    assert m["completed"] == 2
    assert m["dropped"] == 1
    assert m["no_show"] == 1
    assert m["completion_rate"] == 0.5
    assert m["by_event_type"]["workshop"]["fail_rate"] == 1.0
    assert m["event_outcomes"]["EV_C"]["status"] == "dropped"


def test_history_filters_to_employee():
    from app.ai.tests.fixtures import jury_history

    other = [dict(r, employee_id="E8888") for r in jury_history("E7777")]
    emp = make_employee()
    ctx, gaps, metrics = analyze_profile(emp, make_catalog(), make_events(), other)
    assert metrics["total"] == 0
    assert ctx.skill_gaps == gaps


def test_analyze_profile_context_fields():
    emp = make_employee()
    ctx, gaps, metrics = analyze_profile(emp, make_catalog(), make_events(), [])
    assert ctx.employee_id == "E9001"
    assert ctx.next_grade == "Senior"
    assert ctx.preferred_language == "ru"
    assert ctx.history_summary["total"] == 0
