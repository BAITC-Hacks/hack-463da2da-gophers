"""Проверка на сценарий жюри из ТЗ.

«У сотрудника ниже всего Public Speaking, но по истории он трижды пропускал подобные
активности, а для перехода на следующий грейд критичен System Design. Рекомендация
вида "бери минимальный навык" на таком профиле промахивается.»
"""

from datetime import date

from app.ai.recommender import recommend
from app.ai.tests.fixtures import TODAY, jury_history, make_catalog, make_employee, make_events

TODAY_D = date.fromisoformat(TODAY)


def _run(employee=None, history=None):
    return recommend(
        "E9001",
        employees=[employee or make_employee()],
        events=make_events(),
        skills_catalog=make_catalog(),
        history_rows=history if history is not None else jury_history(),
        today=TODAY_D,
        explain_fn=None,
    )


def test_jury_case_system_design_beats_public_speaking():
    result = _run()
    top = result.recommendations[0]
    assert top.event_id == "EV_SD_COURSE"
    assert top.event_id != "EV_PS_WORKSHOP"


def test_jury_case_not_largest_gap_skill():
    result = _run()
    ps_recs = [
        r for r in result.recommendations
        if r.event_id in ("EV_PS_WORKSHOP", "EV_036")
    ]
    assert all(r.rank > 1 for r in ps_recs)


def test_jury_case_top_has_critical_and_history_factors():
    result = _run()
    types = {f.type for f in result.recommendations[0].factors}
    assert "critical_skill" in types
    assert "history_pattern" in types
    assert "skill_gap" in types


def test_jury_case_score_margin():
    result = _run()
    top, second = result.recommendations[0], result.recommendations[1]
    assert top.score - second.score >= 0.1


def test_clean_history_public_speaking_can_win():
    """Контроль симметрии: без негативной истории по PS и с закрытым SD-разрывом
    PS-активность может быть топом (правило не «всегда против PS»)."""
    emp = make_employee(skills={"SK_PYTHON": 4, "SK_SYSTEM_DESIGN": 4, "SK_PUBLIC_SPEAKING": 1})
    result = _run(employee=emp, history=[])
    top = result.recommendations[0]
    assert top.event_id in ("EV_PS_WORKSHOP", "EV_036")
