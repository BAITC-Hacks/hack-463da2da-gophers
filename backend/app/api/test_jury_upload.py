from fastapi.testclient import TestClient

from app.api.store import store
from app.main import app


def _jury_employee(employee_id: str, language: str) -> dict:
    """Minimal employee record in the published dataset format."""
    return {
        "employee_id": employee_id,
        "full_name": f"Jury Profile {employee_id}",
        "department": "Backend Development",
        "role": "Backend Engineer",
        "grade": "Middle",
        "manager_id": None,
        "hire_date": "2024-01-01",
        "tenure_months": 20,
        "work_format": "hybrid",
        "preferred_language": language,
        "career_goal": {"target_role": "Backend Engineer", "target_grade": "Senior"},
        "skills": {"SK_PYTHON": 3, "SK_SYSTEM_DESIGN": 2, "SK_PUBLIC_SPEAKING": 1},
        "last_review_date": "2026-09-01",
    }


def test_admin_loads_three_jury_profiles_and_reports_validation_errors() -> None:
    store.load_default()
    client = TestClient(app)
    employees = [_jury_employee("JURY001", "ru"), _jury_employee("JURY002", "kk"), _jury_employee("JURY003", "en")]
    history = [
        {
            "record_id": f"JR{index}", "employee_id": employee["employee_id"], "event_id": "EV_002",
            "date": "2026-09-01", "due_date": "", "status": "completed", "completion_pct": 100,
            "score": 90, "feedback_rating": 5, "assigned_by": "self",
        }
        for index, employee in enumerate(employees, start=1)
    ]
    response = client.post(
        "/admin/load-dataset",
        headers={"X-Role": "hr"},
        json={"employees": {"employees": employees}, "activity_history": history},
    )
    assert response.status_code == 200
    assert response.json()["employees_loaded"] == 3
    assert response.json()["history_records_loaded"] == 3
    assert client.get("/employees/JURY003").status_code == 200

    invalid = client.post(
        "/admin/load-dataset",
        headers={"X-Role": "hr"},
        json={"employees": {"employees": [{"employee_id": "BROKEN", "grade": "Unknown", "skills": {"SK_NOT_REAL": 1}}]}},
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["errors"]
    store.load_default()
