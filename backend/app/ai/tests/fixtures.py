"""Мини-датасет для тестов AI-ядра (формат стартового кита)."""

from __future__ import annotations

TODAY = "2026-10-01"


def make_catalog() -> dict:
    return {
        "skills": [
            {"skill_id": "SK_SYSTEM_DESIGN", "name": "System Design", "type": "hard", "category": "engineering", "description": ""},
            {"skill_id": "SK_PUBLIC_SPEAKING", "name": "Public Speaking", "type": "soft", "category": "communication", "description": ""},
            {"skill_id": "SK_PYTHON", "name": "Python", "type": "hard", "category": "engineering", "description": ""},
            {"skill_id": "SK_MENTORING", "name": "Mentoring", "type": "soft", "category": "leadership", "description": ""},
        ],
        "role_profiles": [
            {
                "role": "Backend Engineer",
                "grade": "Middle",
                "required_skills": {"SK_PYTHON": 3, "SK_SYSTEM_DESIGN": 2, "SK_PUBLIC_SPEAKING": 2},
                "critical_skills": ["SK_PYTHON"],
            },
            {
                "role": "Backend Engineer",
                "grade": "Senior",
                "required_skills": {"SK_PYTHON": 4, "SK_SYSTEM_DESIGN": 4, "SK_PUBLIC_SPEAKING": 3},
                "critical_skills": ["SK_SYSTEM_DESIGN"],
            },
            {
                "role": "Backend Engineer",
                "grade": "Lead",
                "required_skills": {"SK_PYTHON": 4, "SK_SYSTEM_DESIGN": 5, "SK_PUBLIC_SPEAKING": 3, "SK_MENTORING": 4},
                "critical_skills": ["SK_MENTORING"],
            },
        ],
    }


def make_employee(**over) -> dict:
    emp = {
        "employee_id": "E9001",
        "full_name": "Test Person",
        "department": "Backend Development",
        "role": "Backend Engineer",
        "grade": "Middle",
        "manager_id": "E0050",
        "hire_date": "2022-10-01",
        "tenure_months": 48,
        "work_format": "office",
        "preferred_language": "ru",
        "career_goal": {"target_role": "Backend Engineer", "target_grade": "Senior"},
        "skills": {"SK_PYTHON": 4, "SK_SYSTEM_DESIGN": 2, "SK_PUBLIC_SPEAKING": 0},
        "last_review_date": "2026-06-01",
    }
    emp.update(over)
    return emp


def make_events() -> list[dict]:
    all_roles = ["Backend Engineer"]
    all_grades = ["Junior", "Middle", "Senior", "Lead"]
    return [
        {
            "event_id": "EV_SD_COURSE",
            "title": "System Design Intensive",
            "type": "course",
            "format": "online",
            "duration_hours": 20,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_SYSTEM_DESIGN", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2026-10-10"],
        },
        {
            "event_id": "EV_PS_WORKSHOP",
            "title": "Public Speaking Workshop",
            "type": "workshop",
            "format": "offline",
            "duration_hours": 8,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_PUBLIC_SPEAKING", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2026-10-15"],
        },
        {
            "event_id": "EV_MAND",
            "title": "Infosec Compliance",
            "type": "compliance",
            "format": "self_paced",
            "duration_hours": 2,
            "mandatory": True,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [],
            "prerequisites": {},
            "upcoming_sessions": [],
        },
        {
            "event_id": "EV_PREREQ",
            "title": "Advanced Architecture",
            "type": "course",
            "format": "online",
            "duration_hours": 30,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_SYSTEM_DESIGN", "gain": 2, "max_level": 5}],
            "prerequisites": {"SK_PYTHON": 5},
            "upcoming_sessions": ["2026-10-20"],
        },
        {
            "event_id": "EV_NOSCHED",
            "title": "Old Meetup",
            "type": "meetup",
            "format": "offline",
            "duration_hours": 3,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_MENTORING", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": [],
        },
        {
            "event_id": "EV_DONE",
            "title": "Python Deep Dive",
            "type": "course",
            "format": "online",
            "duration_hours": 16,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_PYTHON", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2026-10-25"],
        },
        {
            "event_id": "EV_036",
            "title": "Recurring Speaking Club",
            "type": "meetup",
            "format": "offline",
            "duration_hours": 2,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_PUBLIC_SPEAKING", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2026-10-05"],
        },
        {
            "event_id": "EV_PS1",
            "title": "Toastmasters 1",
            "type": "meetup",
            "format": "offline",
            "duration_hours": 2,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_PUBLIC_SPEAKING", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2026-10-08"],
        },
        {
            "event_id": "EV_PS2",
            "title": "Toastmasters 2",
            "type": "meetup",
            "format": "offline",
            "duration_hours": 2,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_PUBLIC_SPEAKING", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2026-11-08"],
        },
        {
            "event_id": "EV_PS_W1",
            "title": "Presentation Skills 1",
            "type": "workshop",
            "format": "offline",
            "duration_hours": 6,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_PUBLIC_SPEAKING", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2026-09-08"],
        },
        {
            "event_id": "EV_PS_W2",
            "title": "Presentation Skills 2",
            "type": "workshop",
            "format": "offline",
            "duration_hours": 6,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_PUBLIC_SPEAKING", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2026-09-20"],
        },
        {
            "event_id": "EV_SYS_OLD",
            "title": "Architecture Basics",
            "type": "course",
            "format": "online",
            "duration_hours": 12,
            "mandatory": False,
            "target_roles": all_roles,
            "target_grades": all_grades,
            "develops_skills": [{"skill_id": "SK_SYSTEM_DESIGN", "gain": 1, "max_level": 5}],
            "prerequisites": {},
            "upcoming_sessions": ["2025-05-10"],
        },
    ]


def hist(employee_id: str, event_id: str, status: str, d: str, **over) -> dict:
    row = {
        "record_id": f"R-{employee_id}-{event_id}-{d}",
        "employee_id": employee_id,
        "event_id": event_id,
        "date": d,
        "due_date": "",
        "status": status,
        "completion_pct": 100 if status == "completed" else 0,
        "score": "",
        "feedback_rating": "",
        "assigned_by": "self",
    }
    row.update(over)
    return row


def jury_history(employee_id: str = "E9001") -> list[dict]:
    return [
        hist(employee_id, "EV_PS1", "no_show", "2026-02-10"),
        hist(employee_id, "EV_PS2", "no_show", "2026-05-15"),
        hist(employee_id, "EV_PS_W1", "no_show", "2026-03-20"),
        hist(employee_id, "EV_PS_W2", "dropped", "2026-06-30", completion_pct=20),
        hist(employee_id, "EV_SYS_OLD", "completed", "2026-01-12", score=88),
        hist(employee_id, "EV_DONE", "completed", "2026-03-03", score=92),
        hist(employee_id, "EV_MAND", "completed", "2026-04-01"),
    ]
