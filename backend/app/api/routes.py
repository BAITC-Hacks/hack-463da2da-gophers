from __future__ import annotations

import csv
import hmac
import io
import json
import os
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from .career_paths import build_career_paths
from .store import store

router = APIRouter()


class CareerPathRequest(BaseModel):
    preferred_format: Literal["online", "offline", "self_paced"] | None = None
    hours_per_week: float | None = Field(default=None, gt=0, le=40)


def _require_token(role: str, access_token: str) -> None:
    """Optionally enforce the demo token configured for a role.

    The dataset demo also works without token environment variables, but a
    deployed instance can set HR_API_TOKEN and EMPLOYEE_API_TOKEN without a
    code change.  The role and employee identity are still mandatory headers.
    """
    variable = "HR_API_TOKEN" if role == "hr" else "EMPLOYEE_API_TOKEN"
    expected = os.getenv(variable, "")
    if expected and not hmac.compare_digest(access_token, expected):
        raise HTTPException(status_code=403, detail="Invalid access token")


def _require_hr(x_role: str, x_access_token: str) -> None:
    if x_role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR role required")
    _require_token("hr", x_access_token)


def _require_self_or_hr(
    employee_id: str,
    x_role: str,
    x_employee_id: str,
    x_access_token: str,
) -> None:
    role = x_role.lower()
    if role == "hr":
        _require_token("hr", x_access_token)
        return
    if role == "employee" and x_employee_id == employee_id:
        _require_token("employee", x_access_token)
        return
    raise HTTPException(status_code=403, detail="Employee may access only their own profile")


@router.get("/employees")
def employees(
    x_role: str = Header(default="", alias="X-Role"),
    x_access_token: str = Header(default="", alias="X-Access-Token"),
) -> list[dict[str, Any]]:
    _require_hr(x_role, x_access_token)
    return [store.summary(employee) for employee in store.employees.values()]


@router.get("/employees/{employee_id}")
def employee_profile(
    employee_id: str,
    x_role: str = Header(default="", alias="X-Role"),
    x_employee_id: str = Header(default="", alias="X-Employee-Id"),
    x_access_token: str = Header(default="", alias="X-Access-Token"),
) -> dict[str, Any]:
    _require_self_or_hr(employee_id, x_role, x_employee_id, x_access_token)
    return store.profile(employee_id)


@router.post("/employees/{employee_id}/complete/{event_id}")
def complete(
    employee_id: str,
    event_id: str,
    x_role: str = Header(default="", alias="X-Role"),
    x_employee_id: str = Header(default="", alias="X-Employee-Id"),
    x_access_token: str = Header(default="", alias="X-Access-Token"),
) -> dict[str, Any]:
    _require_self_or_hr(employee_id, x_role, x_employee_id, x_access_token)
    return store.complete(employee_id, event_id)


@router.post("/employees/{employee_id}/career-paths")
def career_paths(
    employee_id: str,
    request: CareerPathRequest,
    x_role: str = Header(default="", alias="X-Role"),
    x_employee_id: str = Header(default="", alias="X-Employee-Id"),
    x_access_token: str = Header(default="", alias="X-Access-Token"),
) -> dict[str, Any]:
    _require_self_or_hr(employee_id, x_role, x_employee_id, x_access_token)
    return build_career_paths(
        store,
        employee_id,
        preferred_format=request.preferred_format,
        hours_per_week=request.hours_per_week,
    )


@router.post("/recommendations/{employee_id}")
def recommendations(
    employee_id: str,
    x_role: str = Header(default="", alias="X-Role"),
    x_employee_id: str = Header(default="", alias="X-Employee-Id"),
    x_access_token: str = Header(default="", alias="X-Access-Token"),
) -> Any:
    _require_self_or_hr(employee_id, x_role, x_employee_id, x_access_token)
    store.employee(employee_id)
    try:
        from app.ai.recommender import recommend  # owned by the AI track
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Recommendation engine is not available yet") from exc
    result = recommend(store, employee_id, today=store.reference_date())
    available_ids = {step["event_id"] for step in store.available_steps(store.employee(employee_id))}
    available_recommendations = [item for item in result.recommendations if item.event_id in available_ids]
    return {
        "employee_id": result.employee_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": result.engine,
        "recommendations": [
            {
                "rank": rank,
                "event": store.event_summary(store.events[item.event_id]),
                "score": item.score,
                "factors": [
                    {
                        "type": factor.type,
                        "skill_id": factor.skill_id,
                        "message": factor.message,
                        "weight": factor.weight,
                    }
                    for factor in item.factors
                ],
                "explanation": {
                    "language": item.explanation.language,
                    "text": item.explanation.text,
                    "factors_used": item.explanation.factors_used,
                },
            }
            for rank, item in enumerate(available_recommendations, start=1)
        ],
    }


@router.get("/hr/dashboard")
def dashboard(
    x_role: str = Header(default="", alias="X-Role"),
    x_access_token: str = Header(default="", alias="X-Access-Token"),
) -> dict[str, Any]:
    _require_hr(x_role, x_access_token)
    return store.dashboard()


def _multipart(body: bytes, content_type: str) -> dict[str, bytes]:
    message = BytesParser(policy=default).parsebytes((f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
    return {part.get_param("name", header="content-disposition"): part.get_payload(decode=True) or b"" for part in message.iter_parts()}


@router.post("/admin/load-dataset")
async def load_dataset(
    request: Request,
    x_role: str = Header(default="", alias="X-Role"),
    x_access_token: str = Header(default="", alias="X-Access-Token"),
) -> dict[str, Any]:
    _require_hr(x_role, x_access_token)
    body, content_type = await request.body(), request.headers.get("content-type", "")
    try:
        if content_type.startswith("application/json"):
            payload = json.loads(body or b"{}")
            counts = store.load_payloads(**{key: payload.get(key) for key in ("employees", "events", "skills", "activity_history")})
        elif content_type.startswith("multipart/form-data"):
            files = _multipart(body, content_type)
            payload = {key: json.loads(value) for key, value in files.items() if key in {"employees", "events", "skills"} and value}
            if files.get("activity_history"):
                payload["activity_history"] = list(csv.DictReader(io.StringIO(files["activity_history"].decode("utf-8-sig"))))
            counts = store.load_payloads(**payload)
        else:
            raise HTTPException(status_code=415, detail="Use application/json or multipart/form-data")
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=422, detail={"errors": [str(exc)]}) from exc
    return {"status": "ok", **counts, "errors": []}
