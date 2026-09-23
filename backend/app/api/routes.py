from __future__ import annotations

import csv
import io
import json
from email.parser import BytesParser
from email.policy import default
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from .store import store

router = APIRouter()


@router.get("/employees")
def employees() -> list[dict[str, Any]]:
    return [store.summary(employee) for employee in store.employees.values()]


@router.get("/employees/{employee_id}")
def employee_profile(employee_id: str) -> dict[str, Any]:
    return store.profile(employee_id)


@router.post("/employees/{employee_id}/complete/{event_id}")
def complete(employee_id: str, event_id: str) -> dict[str, Any]:
    return store.complete(employee_id, event_id)


@router.post("/recommendations/{employee_id}")
def recommendations(employee_id: str) -> Any:
    store.employee(employee_id)
    try:
        from app.ai.recommender import recommend  # owned by the AI track
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Recommendation engine is not available yet") from exc
    return recommend(store, employee_id)


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
