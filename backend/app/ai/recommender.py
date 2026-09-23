"""Публичная точка входа AI-ядра для бек-трека.

Зона GLM. Бек вызывает: recommend(employee_id, employees=..., events=..., skills_catalog=..., history_rows=...)
Схема ответа — contracts.RecommendationResult (соответствует docs/openapi.yaml).
"""

from __future__ import annotations

from datetime import date

from .contracts import Explanation, Recommendation, RecommendationResult, ScoredCandidate
from .core.analyzer import EmployeeContext, analyze_profile
from .core.scoring import rank_candidates

_UNSET = object()


def _heuristic_explanation(candidate: ScoredCandidate, language: str) -> Explanation:
    text = "; ".join(f.message for f in candidate.factors[:4])
    return Explanation(
        language=language,
        text=text,
        factors_used=[f.type for f in candidate.factors],
        engine="heuristic-fallback",
    )


def _load_explain_fn():
    try:
        from .llm.explainer import explain

        return explain
    except Exception:
        return None


def recommend(
    employee_id: str | object,
    *legacy_args: object,
    employees: list[dict] | None = None,
    events: list[dict] | None = None,
    skills_catalog: dict | None = None,
    history_rows: list[dict] | None = None,
    today: date | None = None,
    top_k: int = 3,
    explain_fn=_UNSET,
) -> RecommendationResult:
    """Build recommendations from explicit datasets or the legacy API store.

    The explicit keyword-only form is the AI contract.  The second form keeps
    the already released Backend endpoint working while tracks are integrated:
    ``recommend(store, employee_id)``.
    """
    if not isinstance(employee_id, str):
        if len(legacy_args) != 1:
            raise TypeError("legacy recommend() expects (store, employee_id)")
        store = employee_id
        requested_id = legacy_args[0]
        if not isinstance(requested_id, str):
            raise TypeError("employee_id must be a string")
        try:
            employees = list(store.employees.values())
            events = list(store.events.values())
            skills_catalog = {
                "skills": list(store.skills.values()),
                "role_profiles": list(store.role_profiles.values()),
            }
            history_rows = list(store.history)
        except AttributeError as exc:
            raise TypeError("legacy store does not expose Career Quest datasets") from exc
        employee_id = requested_id

    if employees is None or events is None or skills_catalog is None or history_rows is None:
        raise TypeError("employees, events, skills_catalog and history_rows are required")
    employee = next((e for e in employees if e.get("employee_id") == employee_id), None)
    if employee is None:
        raise KeyError(f"employee not found: {employee_id}")

    ctx, gaps, metrics = analyze_profile(employee, skills_catalog, events, history_rows)
    candidates = rank_candidates(
        employee,
        events,
        gaps,
        metrics,
        ctx.next_role,
        ctx.next_grade,
        today=today,
        top_k=top_k,
    )

    fn = _load_explain_fn() if explain_fn is _UNSET else explain_fn

    recommendations: list[Recommendation] = []
    for rank, candidate in enumerate(candidates, start=1):
        explanation: Explanation | None = None
        if fn is not None:
            try:
                explanation = fn(candidate, ctx, ctx.preferred_language)
            except Exception:
                explanation = None
        if explanation is None:
            explanation = _heuristic_explanation(candidate, ctx.preferred_language)
        recommendations.append(
            Recommendation(
                rank=rank,
                event_id=candidate.event_id,
                title=candidate.title,
                score=candidate.score,
                factors=candidate.factors,
                explanation=explanation,
            )
        )

    engine = recommendations[0].explanation.engine if recommendations else "heuristic-fallback"
    return RecommendationResult(
        employee_id=employee_id,
        recommendations=recommendations,
        engine=engine,
    )
