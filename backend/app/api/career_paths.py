"""Career Twin path builder using the existing explainable recommendation score."""
from __future__ import annotations

from copy import deepcopy
from math import ceil
from typing import Any

from app.ai.core.analyzer import analyze_profile
from app.ai.core.scoring import rank_candidates

from .store import DatasetStore

MAX_STEPS = 3
FLEXIBLE_FORMATS = ("self_paced", "online")


def _readiness(skills: dict[str, int], requirements: dict[str, int]) -> float:
    """Return progress towards the next-grade requirements on a 0..100 scale."""
    total_required = sum(int(level) for level in requirements.values())
    if not total_required:
        return 100.0
    reached = sum(
        min(int(skills.get(skill_id, 0)), int(required))
        for skill_id, required in requirements.items()
    )
    return round(100 * reached / total_required, 1)


def _project_skills(skills: dict[str, int], events: list[dict[str, Any]]) -> dict[str, int]:
    """Apply the projected gains exactly as completion does, including max_level."""
    projected = deepcopy(skills)
    for event in events:
        for gain in event.get("develops_skills", []):
            skill_id = gain["skill_id"]
            before = int(projected.get(skill_id, 0))
            projected[skill_id] = min(before + int(gain["gain"]), int(gain["max_level"]))
    return projected


def _factor_payload(candidate: Any) -> list[dict[str, Any]]:
    return [
        {
            "type": factor.type,
            "skill_id": factor.skill_id,
            "message": factor.message,
            "weight": factor.weight,
        }
        for factor in candidate.factors
    ]


def _build_path(
    *,
    kind: str,
    title: str,
    candidates: list[Any],
    events_by_id: dict[str, dict[str, Any]],
    employee: dict[str, Any],
    requirements: dict[str, int],
    store: DatasetStore,
    hours_per_week: float | None,
    reason: str,
    constraint_honored: bool,
) -> dict[str, Any]:
    selected = candidates[:MAX_STEPS]
    events = [events_by_id[candidate.event_id] for candidate in selected]
    total_hours = sum(float(event.get("duration_hours", 0)) for event in events)
    readiness_before = _readiness(employee.get("skills", {}), requirements)
    readiness_after = _readiness(_project_skills(employee.get("skills", {}), events), requirements)

    return {
        "kind": kind,
        "title": title,
        "status": "ready" if events else "no_eligible_steps",
        "constraint_honored": constraint_honored,
        "reason": reason,
        "steps": [
            {
                "rank": index,
                "score": candidate.score,
                "event": store.event_summary(events_by_id[candidate.event_id]),
            }
            for index, candidate in enumerate(selected, start=1)
        ],
        "factors": _factor_payload(selected[0]) if selected else [],
        "total_hours": total_hours,
        "estimated_weeks": ceil(total_hours / hours_per_week) if events and hours_per_week else None,
        "readiness": {"before": readiness_before, "after": readiness_after},
    }


def build_career_paths(
    store: DatasetStore,
    employee_id: str,
    *,
    preferred_format: str | None = None,
    hours_per_week: float | None = None,
) -> dict[str, Any]:
    """Build a fast and a flexible path without suggesting unavailable events.

    Candidate quality remains owned by the shared AI scoring module.  The API
    layer adds only product constraints: current availability, format, time,
    sequential gain simulation and a stable response for the frontend.
    """
    employee = store.employee(employee_id)
    target = store.target_profile(employee)
    if target is None:
        return {
            "employee_id": employee_id,
            "target": None,
            "constraints": {"preferred_format": preferred_format, "hours_per_week": hours_per_week},
            "paths": [],
            "reason": "No next-grade target is configured for this employee.",
        }

    all_events = list(store.events.values())
    skills_catalog = {
        "skills": list(store.skills.values()),
        "role_profiles": list(store.role_profiles.values()),
    }
    context, gaps, history_metrics = analyze_profile(employee, skills_catalog, all_events, store.history)
    available_ids = {item["event_id"] for item in store.available_steps(employee)}
    events_by_id = {event["event_id"]: event for event in all_events if event["event_id"] in available_ids}
    candidates = [
        candidate
        for candidate in rank_candidates(
            employee,
            all_events,
            gaps,
            history_metrics,
            context.next_role,
            context.next_grade,
            today=store.reference_date(),
            top_k=len(all_events),
        )
        if candidate.event_id in events_by_id
    ]
    requirements = target.get("required_skills", {})

    # Fast means the best projected next-grade progress for every hour invested.
    fast_candidates = sorted(
        candidates,
        key=lambda candidate: (
            -(candidate.score / max(float(events_by_id[candidate.event_id].get("duration_hours", 0)), 1.0)),
            -candidate.score,
            candidate.event_id,
        ),
    )
    fast = _build_path(
        kind="fast",
        title="Fast path",
        candidates=fast_candidates,
        events_by_id=events_by_id,
        employee=employee,
        requirements=requirements,
        store=store,
        hours_per_week=hours_per_week,
        reason="Prioritizes available activities with the strongest AI score per hour.",
        constraint_honored=True,
    )

    if preferred_format:
        flexible_candidates = [
            candidate
            for candidate in candidates
            if events_by_id[candidate.event_id].get("format") == preferred_format
        ]
        flexible_reason = (
            f"Uses only eligible {preferred_format} activities to honor the selected format."
            if flexible_candidates
            else f"No eligible {preferred_format} activities are available, so no mismatched event is suggested."
        )
    else:
        flexible_candidates = sorted(
            candidates,
            key=lambda candidate: (
                FLEXIBLE_FORMATS.index(events_by_id[candidate.event_id].get("format"))
                if events_by_id[candidate.event_id].get("format") in FLEXIBLE_FORMATS
                else len(FLEXIBLE_FORMATS),
                -candidate.score,
                candidate.event_id,
            ),
        )
        flexible_reason = "Prioritizes self-paced and online activities while preserving AI recommendation quality."

    flexible = _build_path(
        kind="flexible",
        title="Flexible path",
        candidates=flexible_candidates,
        events_by_id=events_by_id,
        employee=employee,
        requirements=requirements,
        store=store,
        hours_per_week=hours_per_week,
        reason=flexible_reason,
        constraint_honored=True,
    )

    return {
        "employee_id": employee_id,
        "target": {"role": target["role"], "grade": target["grade"]},
        "constraints": {"preferred_format": preferred_format, "hours_per_week": hours_per_week},
        "paths": [fast, flexible],
    }
