from app.api.store import DATASET_SNAPSHOT_DATE, store


def test_target_grade_activity_is_available_and_can_be_completed() -> None:
    """A next-grade recommendation must never turn into a 409 on completion."""
    store.load_default()
    employee_id = "E0001"  # Junior backend engineer with a Middle career goal.

    available_ids = {step["event_id"] for step in store.available_steps(store.employee(employee_id))}
    assert "EV_009" in available_ids  # Middle-grade Cloud Certification Prep.

    completed = store.complete(employee_id, "EV_009")
    assert completed["trajectory_updated"] is True
    assert completed["event_id"] == "EV_009"
    assert store.history[-1]["date"] == DATASET_SNAPSHOT_DATE


def test_recurring_club_stays_available_after_completion_and_snapshot_is_stable() -> None:
    store.load_default()
    employee = next(
        candidate
        for candidate in store.employees.values()
        if any(
            row["employee_id"] == candidate["employee_id"]
            and row["event_id"] == "EV_036"
            and row["status"] == "completed"
            for row in store.history
        )
        and "EV_036" in {step["event_id"] for step in store.available_steps(candidate)}
    )

    assert employee["employee_id"]
    assert store.reference_date().isoformat() == DATASET_SNAPSHOT_DATE
