from fastapi.testclient import TestClient

from app.api.store import store
from app.main import app


def test_career_twin_honors_format_and_projects_readiness() -> None:
    store.load_default()
    client = TestClient(app)

    response = client.post(
        "/employees/E0001/career-paths",
        headers={"X-Role": "employee", "X-Employee-Id": "E0001"},
        json={"preferred_format": "self_paced", "hours_per_week": 8},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["target"] == {"role": "Backend Engineer", "grade": "Middle"}
    assert payload["constraints"] == {"preferred_format": "self_paced", "hours_per_week": 8}
    assert {path["kind"] for path in payload["paths"]} == {"fast", "flexible"}

    flexible = next(path for path in payload["paths"] if path["kind"] == "flexible")
    assert flexible["constraint_honored"] is True
    assert 0 <= len(flexible["steps"]) <= 3
    assert all(step["event"]["format"] == "self_paced" for step in flexible["steps"])
    assert flexible["estimated_weeks"] is None or flexible["estimated_weeks"] >= 1
    assert flexible["readiness"]["after"] >= flexible["readiness"]["before"]
    assert len({factor["type"] for factor in flexible["factors"]}) >= 3

    invalid_format = client.post(
        "/employees/E0001/career-paths",
        headers={"X-Role": "employee", "X-Employee-Id": "E0001"},
        json={"preferred_format": "hybrid"},
    )
    assert invalid_format.status_code == 422
