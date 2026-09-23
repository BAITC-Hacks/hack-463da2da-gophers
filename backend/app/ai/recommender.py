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
    employee_id: str,
    *,
    employees: list[dict],
    events: list[dict],
    skills_catalog: dict,
    history_rows: list[dict],
    today: date | None = None,
    top_k: int = 3,
    explain_fn=_UNSET,
) -> RecommendationResult:
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
