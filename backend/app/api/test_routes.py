from fastapi.testclient import TestClient

from app.api.store import store
from app.main import app

EMPLOYEE_HEADERS = {"X-Role": "employee", "X-Employee-Id": "E0001"}


def test_recommendation_response_matches_api_contract_and_recalculates() -> None:
    """The employee flow remains usable by the live frontend after completion."""
    store.load_default()
    client = TestClient(app)
    employee_id = "E0001"

    before = client.post(f"/recommendations/{employee_id}", headers=EMPLOYEE_HEADERS)
    assert before.status_code == 200
    payload = before.json()
    assert payload["employee_id"] == employee_id
    assert payload["generated_at"]
    assert 1 <= len(payload["recommendations"]) <= 3
    available_ids = {step["event_id"] for step in store.available_steps(store.employee(employee_id))}
    assert all(item["event"]["event_id"] in available_ids for item in payload["recommendations"])
    first = payload["recommendations"][0]
    assert {"rank", "event", "score", "factors", "explanation"} <= set(first)
    assert first["event"]["event_id"]
    assert len({factor["type"] for factor in first["factors"]}) >= 3

    completed = client.post(
        f"/employees/{employee_id}/complete/{first['event']['event_id']}",
        headers=EMPLOYEE_HEADERS,
    )
    assert completed.status_code == 200
    assert completed.json()["trajectory_updated"]

    after = client.post(f"/recommendations/{employee_id}", headers=EMPLOYEE_HEADERS)
    assert after.status_code == 200
    assert first["event"]["event_id"] not in {
        item["event"]["event_id"] for item in after.json()["recommendations"]
    }


def test_recommendations_never_return_a_step_that_backend_rejects(monkeypatch) -> None:
    """Protect the core demo flow for every profile in the supplied dataset."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    store.load_default()
    client = TestClient(app)

    for employee_id in store.employees:
        response = client.post(
            f"/recommendations/{employee_id}",
            headers={"X-Role": "employee", "X-Employee-Id": employee_id},
        )
        assert response.status_code == 200
        available_ids = {step["event_id"] for step in store.available_steps(store.employee(employee_id))}
        assert all(
            recommendation["event"]["event_id"] in available_ids
            for recommendation in response.json()["recommendations"]
        )
