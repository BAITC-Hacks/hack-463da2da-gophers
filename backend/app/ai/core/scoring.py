"""Скоринг активностей-кандидатов: мультифакторный, объяснимый.

Зона GLM (AI-ядро / core). Правило против однофакторности (проверочные профили жюри):
кандидат с большим разрывом, но негативной историей по типу активности,
обязан проигрывать критичному для следующего грейда кандидату с хорошей историей.
"""

from __future__ import annotations

from datetime import date

from ..contracts import Factor, ScoredCandidate
from .analyzer import RECURRING_EVENT_ID

W_GAP = 0.55
W_HISTORY = 0.25
W_AVAIL = 0.10
W_FIT = 0.10
CRITICAL_MULT = 1.6
NEAR_SESSION_DAYS = 14
LATE_SESSION_DAYS = 45


def _today(today: date | None) -> date:
    return today or date.today()


def is_eligible(
    event: dict,
    employee: dict,
    history_metrics: dict,
    target_role: str,
    target_grade: str,
) -> bool:
    if event.get("mandatory"):
        return False
    event_id = event.get("event_id", "")
    if event_id != RECURRING_EVENT_ID and event_id in history_metrics.get("event_outcomes", {}):
        return False
    roles = event.get("target_roles", [])
    if employee.get("role") not in roles and target_role not in roles:
        return False
    grades = event.get("target_grades", [])
    if employee.get("grade") not in grades and target_grade not in grades:
        return False
    skills = employee.get("skills", {})
    for sid, min_level in (event.get("prerequisites") or {}).items():
        if int(skills.get(sid, 0)) < int(min_level):
            return False
    if event.get("format") != "self_paced":
        if not event.get("upcoming_sessions"):
            return False
    return True


def effective_closing(develops: dict, gap: dict) -> int:
    current = int(gap["current"])
    required = int(gap["required"])
    after = min(current + int(develops.get("gain", 0)), int(develops.get("max_level", 5)))
    return max(0, min(after, required) - current)


def _availability_component(event: dict, today: date) -> tuple[float, str]:
    if event.get("format") == "self_paced":
        return 1.0, "Self-paced: can start any time"
    sessions = sorted(
        s for s in (date.fromisoformat(x) for x in event.get("upcoming_sessions", []) if x)
        if s >= today
    )
    if not sessions:
        return 0.0, "No upcoming sessions"
    days = (sessions[0] - today).days
    if days <= NEAR_SESSION_DAYS:
        return 1.0, f"Next session on {sessions[0].isoformat()} (in {days} days)"
    if days <= LATE_SESSION_DAYS:
        return 0.7, f"Next session on {sessions[0].isoformat()} (in {days} days)"
    return 0.4, f"Next session on {sessions[0].isoformat()} (in {days} days)"


def _history_component(event: dict, metrics: dict) -> tuple[float, str]:
    bucket = (metrics.get("by_event_type") or {}).get(event.get("type", ""), {})
    total = bucket.get("total", 0)
    if not total:
        return 0.0, f"No track record with '{event.get('type')}' activities yet"
    failed = bucket.get("failed", 0)
    comp = 0.5 * bucket.get("completion_rate", 0.0) - 1.0 * bucket.get("fail_rate", 0.0)
    if comp >= 0:
        msg = f"{bucket.get('completed', 0)} of {total} '{event.get('type')}' activities completed previously"
    else:
        msg = f"{failed} of {total} '{event.get('type')}' activities missed or dropped previously"
    return comp, msg


def _gap_component(event: dict, gaps: list[dict]) -> tuple[float, float, list[dict]]:
    weighted_total = sum(
        g["gap"] * (CRITICAL_MULT if g["critical"] else 1.0) for g in gaps
    )
    gaps_by_id = {g["skill_id"]: g for g in gaps}
    value = 0.0
    details: list[dict] = []
    for develops in event.get("develops_skills", []):
        gap = gaps_by_id.get(develops.get("skill_id"))
        if gap is None:
            continue
        closing = effective_closing(develops, gap)
        if closing <= 0:
            continue
        weight = CRITICAL_MULT if gap["critical"] else 1.0
        value += closing * weight
        details.append({**gap, "closing": closing})
    component = value / weighted_total if weighted_total > 0 else 0.0
    return component, value, details


def score_event(
    event: dict,
    employee: dict,
    gaps: list[dict],
    history_metrics: dict,
    target_grade: str,
    today: date | None = None,
) -> ScoredCandidate:
    today = _today(today)
    gap_component, _, details = _gap_component(event, gaps)
    history_component, history_msg = _history_component(event, history_metrics)
    availability_component, availability_msg = _availability_component(event, today)
    if target_grade in event.get("target_grades", []):
        fit_component, fit_msg = 1.0, f"Aligned with the {target_grade} transition target"
    else:
        fit_component, fit_msg = 0.5, "Matches current grade only"

    score = (
        W_GAP * gap_component
        + W_HISTORY * history_component
        + W_AVAIL * availability_component
        + W_FIT * fit_component
    )
    score = round(max(0.0, min(1.0, score)), 3)

    factors: list[Factor] = []
    if details:
        top = max(details, key=lambda d: d["closing"] * (CRITICAL_MULT if d["critical"] else 1.0))
        factors.append(
            Factor(
                type="skill_gap",
                message=(
                    f"Closes {top['closing']} of {top['gap']} level(s) to reach "
                    f"{top['required']} in {top['name']} ({top['current']} now)"
                ),
                skill_id=top["skill_id"],
                weight=round(gap_component, 3),
            )
        )
        critical_hits = [d for d in details if d["critical"]]
        if critical_hits:
            c = critical_hits[0]
            factors.append(
                Factor(
                    type="critical_skill",
                    message=f"{c['name']} is critical for the {target_grade} grade",
                    skill_id=c["skill_id"],
                    weight=round(gap_component * 0.5, 3),
                )
            )
    else:
        factors.append(
            Factor(
                type="skill_gap",
                message="Does not directly close any skill gap for the next grade",
                weight=0.0,
            )
        )

    factors.append(
        Factor(
            type="history_pattern",
            message=history_msg,
            weight=round(abs(history_component) * W_HISTORY, 3),
        )
    )
    prereqs = event.get("prerequisites") or {}
    factors.append(
        Factor(
            type="prerequisites_met",
            message=(
                "No prerequisites required"
                if not prereqs
                else f"Prerequisites satisfied: {', '.join(f'{k}>={v}' for k, v in prereqs.items())}"
            ),
            weight=0.05,
        )
    )
    factors.append(Factor(type="grade_fit", message=fit_msg, weight=round(W_FIT * fit_component, 3)))
    factors.append(
        Factor(
            type="session_availability",
            message=availability_msg,
            weight=round(W_AVAIL * availability_component, 3),
        )
    )

    return ScoredCandidate(
        event_id=event.get("event_id", ""),
        title=event.get("title", ""),
        score=score,
        factors=factors,
    )


def rank_candidates(
    employee: dict,
    events: list[dict],
    gaps: list[dict],
    history_metrics: dict,
    target_role: str,
    target_grade: str,
    today: date | None = None,
    top_k: int = 3,
) -> list[ScoredCandidate]:
    scored = [
        score_event(event, employee, gaps, history_metrics, target_grade, today)
        for event in events
        if is_eligible(event, employee, history_metrics, target_role, target_grade)
    ]
    scored.sort(key=lambda c: (-c.score, c.event_id))
    return scored[:top_k]
