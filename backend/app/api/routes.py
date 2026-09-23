from __future__ import annotations

import csv
import io
import json
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


@router.get("/employees")
def employees() -> list[dict[str, Any]]:
    return [store.summary(employee) for employee in store.employees.values()]


@router.get("/employees/{employee_id}")
def employee_profile(employee_id: str) -> dict[str, Any]:
    return store.profile(employee_id)


@router.post("/employees/{employee_id}/complete/{event_id}")
def complete(employee_id: str, event_id: str) -> dict[str, Any]:
    return store.complete(employee_id, event_id)


@router.post("/employees/{employee_id}/career-paths")
def career_paths(employee_id: str, request: CareerPathRequest) -> dict[str, Any]:
    return build_career_paths(
        store,
        employee_id,
        preferred_format=request.preferred_format,
        hours_per_week=request.hours_per_week,
    )


@router.post("/recommendations/{employee_id}")
def recommendations(employee_id: str) -> Any:
    store.employee(employee_id)
    try:
        from app.ai.recommender import recommend  # owned by the AI track
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Recommendation engine is not available yet") from exc
    result = recommend(store, employee_id)
    return {
        "employee_id": result.employee_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": result.engine,
        "recommendations": [
            {
                "rank": item.rank,
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
            for item in result.recommendations
        ],
    }


@router.get("/hr/dashboard")
def dashboard(x_role: str = Header(default="", alias="X-Role")) -> dict[str, Any]:
    if x_role.lower() != "hr": raise HTTPException(status_code=403, detail="HR role required")
    return store.dashboard()


def _multipart(body: bytes, content_type: str) -> dict[str, bytes]:
    message = BytesParser(policy=default).parsebytes((f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
    return {part.get_param("name", header="content-disposition"): part.get_payload(decode=True) or b"" for part in message.iter_parts()}


@router.post("/admin/load-dataset")
async def load_dataset(request: Request, x_role: str = Header(default="", alias="X-Role")) -> dict[str, Any]:
    if x_role.lower() != "hr": raise HTTPException(status_code=403, detail="HR role required")
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
