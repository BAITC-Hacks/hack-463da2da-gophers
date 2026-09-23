from fastapi.testclient import TestClient

from app.api.store import store
from app.main import app


def test_employee_and_hr_endpoints_expose_only_their_expected_views(monkeypatch) -> None:
    store.load_default()
    client = TestClient(app)
    employee_headers = {"X-Role": "employee", "X-Employee-Id": "E0001"}
    hr_headers = {"X-Role": "hr"}

    assert client.get("/health").json() == {"status": "ok"}

    employees = client.get("/employees")
    assert employees.status_code == 403
    employees = client.get("/employees", headers=hr_headers)
    assert employees.status_code == 200 and employees.json()

    profile = client.get("/employees/E0001", headers=employee_headers)
    assert profile.status_code == 200
    assert profile.json()["employee"]["employee_id"] == "E0001"
    assert all(not event["mandatory"] for event in profile.json()["available_steps"])
    assert client.get("/employees/E0002", headers=employee_headers).status_code == 403
    assert client.post("/recommendations/E0001").status_code == 403

    forbidden = client.get("/hr/dashboard")
    assert forbidden.status_code == 403

    dashboard = client.get("/hr/dashboard", headers=hr_headers)
    assert dashboard.status_code == 200
    assert {"weak_skills", "employees_without_recommendation", "activity_engagement"} <= set(dashboard.json())

    monkeypatch.setenv("HR_API_TOKEN", "jury-only-token")
    assert client.get("/hr/dashboard", headers=hr_headers).status_code == 403
    assert client.get("/hr/dashboard", headers={**hr_headers, "X-Access-Token": "jury-only-token"}).status_code == 200
