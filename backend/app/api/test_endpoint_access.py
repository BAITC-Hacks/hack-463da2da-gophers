from fastapi.testclient import TestClient

from app.api.store import store
from app.main import app


def test_employee_and_hr_endpoints_expose_only_their_expected_views() -> None:
    store.load_default()
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}

    employees = client.get("/employees")
    assert employees.status_code == 200
    assert employees.json()

    profile = client.get("/employees/E0001")
    assert profile.status_code == 200
    assert profile.json()["employee"]["employee_id"] == "E0001"
    assert all(not event["mandatory"] for event in profile.json()["available_steps"])

    forbidden = client.get("/hr/dashboard")
    assert forbidden.status_code == 403

    dashboard = client.get("/hr/dashboard", headers={"X-Role": "hr"})
    assert dashboard.status_code == 200
    assert {"weak_skills", "employees_without_recommendation", "activity_engagement"} <= set(dashboard.json())
