"""Анализ профиля сотрудника: цель развития, разрывы навыков, метрики истории.

Зона GLM (AI-ядро / core). Чистая логика без сети и внешних зависимостей.
Входы — dict-структуры в формате датасета (схема — в README стартового кита).
"""

from __future__ import annotations

from ..contracts import EmployeeContext

GRADE_ORDER = ["Junior", "Middle", "Senior", "Lead"]
RECURRING_EVENT_ID = "EV_036"
FAILED_STATUSES = {"dropped", "no_show", "declined"}


def next_grade(grade: str) -> str | None:
    if grade not in GRADE_ORDER:
        return None
    i = GRADE_ORDER.index(grade)
    if i + 1 >= len(GRADE_ORDER):
        return None
    return GRADE_ORDER[i + 1]


def skills_index(skills_catalog: dict) -> dict[str, dict]:
    return {s["skill_id"]: s for s in skills_catalog.get("skills", [])}


def events_index(events: list[dict]) -> dict[str, dict]:
    return {e["event_id"]: e for e in events}


def role_profile_for(skills_catalog: dict, role: str, grade: str) -> dict | None:
    for p in skills_catalog.get("role_profiles", []):
        if p.get("role") == role and p.get("grade") == grade:
            return p
    return None


def resolve_target(employee: dict) -> tuple[str, str]:
    goal = employee.get("career_goal")
    if goal and goal.get("target_role") and goal.get("target_grade"):
        return goal["target_role"], goal["target_grade"]
    ng = next_grade(employee.get("grade", ""))
    if ng is None:
        return employee.get("role", ""), employee.get("grade", "")
    return employee.get("role", ""), ng


def analyze_skill_gaps(
    employee: dict, skills_catalog: dict, target_role: str, target_grade: str
) -> list[dict]:
    profile = role_profile_for(skills_catalog, target_role, target_grade)
    if profile is None:
        return []
    critical = set(profile.get("critical_skills", []))
    names = skills_index(skills_catalog)
    current_skills = employee.get("skills", {})
    gaps: list[dict] = []
    for sid, req in profile.get("required_skills", {}).items():
        cur = int(current_skills.get(sid, 0))
        gap = max(0, int(req) - cur)
        if gap == 0:
            continue
        gaps.append(
            {
                "skill_id": sid,
                "name": names.get(sid, {}).get("name", sid),
                "current": cur,
                "required": int(req),
                "gap": gap,
                "critical": sid in critical,
            }
        )
    gaps.sort(key=lambda g: (not g["critical"], -g["gap"], g["skill_id"]))
    return gaps


def analyze_history(history_rows: list[dict], events_by_id: dict[str, dict]) -> dict:
    counts = {"completed": 0, "in_progress": 0, "dropped": 0, "no_show": 0, "declined": 0, "overdue": 0}
    by_type: dict[str, dict] = {}
    event_outcomes: dict[str, dict] = {}
    voluntary_total = 0
    voluntary_completed = 0
    mandatory_overdue = 0

    for row in sorted(history_rows, key=lambda r: r.get("date", "")):
        event_id = row.get("event_id", "")
        event = events_by_id.get(event_id, {})
        etype = event.get("type", "unknown")
        status = row.get("status", "")
        counts[status] = counts.get(status, 0) + 1

        bucket = by_type.setdefault(etype, {"total": 0, "completed": 0, "failed": 0})
        bucket["total"] += 1
        if status == "completed":
            bucket["completed"] += 1
        elif status in FAILED_STATUSES:
            bucket["failed"] += 1

        if event:
            if event.get("mandatory"):
                if status == "overdue":
                    mandatory_overdue += 1
            else:
                voluntary_total += 1
                if status == "completed":
                    voluntary_completed += 1

        event_outcomes[event_id] = {
            "status": status,
            "completion_pct": int(row.get("completion_pct") or 0),
        }

    total = len(history_rows)
    for bucket in by_type.values():
        t = bucket["total"]
        bucket["completion_rate"] = round(bucket["completed"] / t, 3) if t else 0.0
        bucket["fail_rate"] = round(bucket["failed"] / t, 3) if t else 0.0

    def rate(n: int) -> float:
        return round(n / total, 3) if total else 0.0

    return {
        "total": total,
        **counts,
        "completion_rate": rate(counts["completed"]),
        "drop_rate": rate(counts["dropped"]),
        "no_show_rate": rate(counts["no_show"]),
        "voluntary_total": voluntary_total,
        "voluntary_completed": voluntary_completed,
        "voluntary_completion_rate": (
            round(voluntary_completed / voluntary_total, 3) if voluntary_total else 0.0
        ),
        "mandatory_overdue": mandatory_overdue,
        "by_event_type": by_type,
        "event_outcomes": event_outcomes,
    }


def analyze_profile(
    employee: dict, skills_catalog: dict, events: list[dict], history_rows: list[dict]
) -> tuple[EmployeeContext, list[dict], dict]:
    target_role, target_grade = resolve_target(employee)
    gaps = analyze_skill_gaps(employee, skills_catalog, target_role, target_grade)
    by_event = events_index(events)
    own_rows = [r for r in history_rows if r.get("employee_id") == employee.get("employee_id")]
    metrics = analyze_history(own_rows, by_event)

    recent = sorted(own_rows, key=lambda r: r.get("date", ""), reverse=True)[:5]
    recent_events = [
        {
            "title": by_event.get(r.get("event_id", ""), {}).get("title", r.get("event_id")),
            "status": r.get("status", ""),
            "date": r.get("date", ""),
        }
        for r in recent
    ]

    ctx = EmployeeContext(
        employee_id=employee.get("employee_id", ""),
        full_name=employee.get("full_name", ""),
        role=employee.get("role", ""),
        grade=employee.get("grade", ""),
        tenure_months=int(employee.get("tenure_months", 0)),
        preferred_language=employee.get("preferred_language", "en"),
        next_role=target_role,
        next_grade=target_grade,
        skill_gaps=gaps,
        history_summary={
            k: v for k, v in metrics.items() if k not in ("event_outcomes", "by_event_type")
        },
        recent_events=recent_events,
    )
    return ctx, gaps, metrics
