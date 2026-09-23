"""In-memory dataset store and contract-shaped API helpers."""
from __future__ import annotations

import csv
import io
import json
import os
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException


GRADES = ("Junior", "Middle", "Senior", "Lead")
ALLOWED_STATUSES = {"completed", "in_progress", "dropped", "no_show", "declined", "overdue"}
# The starter kit defines its evaluation "today" explicitly.  Using the
# workstation clock would eventually make all scheduled activities disappear.
DATASET_SNAPSHOT_DATE = "2026-10-01"
RECURRING_EVENT_IDS = {"EV_036"}


class DatasetStore:
    def __init__(self) -> None:
        self.employees: dict[str, dict[str, Any]] = {}
        self.events: dict[str, dict[str, Any]] = {}
        self.skills: dict[str, dict[str, Any]] = {}
        self.role_profiles: dict[tuple[str, str], dict[str, Any]] = {}
        self.history: list[dict[str, Any]] = []

    def load_default(self) -> None:
        configured_dir = os.getenv("DATASET_DIR")
        dataset_dir = Path(configured_dir) if configured_dir else Path()
        if not configured_dir or not dataset_dir.exists():
            dataset_dir = Path(__file__).resolve().parents[3] / "career_quest_dataset/case_1/career_quest_dataset"
        self.load_payloads(
            employees=json.loads((dataset_dir / "employees.json").read_text(encoding="utf-8")),
            events=json.loads((dataset_dir / "events.json").read_text(encoding="utf-8")),
            skills=json.loads((dataset_dir / "skills.json").read_text(encoding="utf-8")),
            activity_history=list(csv.DictReader((dataset_dir / "activity_history.csv").open(encoding="utf-8", newline=""))),
            replace=True,
        )

    def load_payloads(self, *, employees: Any = None, events: Any = None, skills: Any = None,
                      activity_history: Any = None, replace: bool = False) -> dict[str, int]:
        parsed_employees = self._items(employees, "employees") if employees is not None else None
        parsed_events = self._items(events, "events") if events is not None else None
        parsed_skills = self._items(skills, "skills") if skills is not None else None
        parsed_history = self._history_items(activity_history) if activity_history is not None else None
        errors = self._validate(
            parsed_employees,
            parsed_events,
            parsed_skills,
            parsed_history,
            reject_existing_history=not replace,
        )
        if errors:
            raise HTTPException(status_code=422, detail={"errors": errors})
        if replace:
            if parsed_employees is not None: self.employees.clear()
            if parsed_events is not None: self.events.clear()
            if parsed_skills is not None:
                self.skills.clear(); self.role_profiles.clear()
            if parsed_history is not None: self.history.clear()
        if parsed_skills is not None:
            for item in parsed_skills:
                self.skills[item["skill_id"]] = deepcopy(item)
            for profile in (skills or {}).get("role_profiles", []) if isinstance(skills, dict) else []:
                self.role_profiles[(profile["role"], profile["grade"])] = deepcopy(profile)
        if parsed_events is not None:
            self.events.update({item["event_id"]: deepcopy(item) for item in parsed_events})
        if parsed_employees is not None:
            self.employees.update({item["employee_id"]: deepcopy(item) for item in parsed_employees})
        if parsed_history is not None:
            existing = {row.get("record_id") for row in self.history}
            self.history.extend(deepcopy(row) for row in parsed_history if row.get("record_id") not in existing)
        return {"employees_loaded": len(parsed_employees or []), "events_loaded": len(parsed_events or []),
                "skills_loaded": len(parsed_skills or []), "history_records_loaded": len(parsed_history or [])}

    @staticmethod
    def _items(payload: Any, key: str) -> list[dict[str, Any]]:
        if isinstance(payload, dict): return payload.get(key, [])
        if isinstance(payload, list): return payload
        raise ValueError(f"{key}: expected JSON object or array")

    @staticmethod
    def _history_items(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list): return payload
        if isinstance(payload, str): return list(csv.DictReader(io.StringIO(payload)))
        raise ValueError("activity_history: expected CSV text or array")

    def _validate(
        self,
        employees: Any,
        events: Any,
        skills: Any,
        history: Any,
        *,
        reject_existing_history: bool,
    ) -> list[str]:
        errors: list[str] = []
        known_skills = set(self.skills) | {x.get("skill_id") for x in (skills or []) if isinstance(x, dict)}
        known_events = set(self.events) | {x.get("event_id") for x in (events or []) if isinstance(x, dict)}
        known_employees = set(self.employees) | {x.get("employee_id") for x in (employees or []) if isinstance(x, dict)}
        for collection, key in ((employees, "employee_id"), (events, "event_id"), (skills, "skill_id")):
            seen: set[str] = set()
            for index, item in enumerate(collection or [], 1):
                if not isinstance(item, dict):
                    errors.append(f"{key} row {index}: expected an object")
                    continue
                value = item.get(key)
                if not value:
                    errors.append(f"{key} row {index}: missing {key}")
                elif value in seen: errors.append(f"{key} row {index}: duplicate {value}")
                seen.add(value)
        existing_history_ids = {row.get("record_id") for row in self.history}
        history_ids: set[str] = set()
        for index, row in enumerate(history or [], 1):
            if not isinstance(row, dict):
                errors.append(f"activity_history row {index}: expected an object")
                continue
            record_id = row.get("record_id")
            if not record_id:
                errors.append(f"activity_history row {index}: missing record_id")
            elif record_id in history_ids or (reject_existing_history and record_id in existing_history_ids):
                errors.append(f"activity_history row {index}: duplicate record_id {record_id}")
            history_ids.add(record_id)
        for index, item in enumerate(employees or [], 1):
            if not isinstance(item, dict):
                continue
            for field in ("full_name", "department", "role", "tenure_months", "preferred_language", "skills"):
                if field not in item:
                    errors.append(f"employees row {index}: missing {field}")
            if item.get("grade") not in GRADES: errors.append(f"employees row {index}: invalid grade")
            employee_skills = item.get("skills", {})
            if not isinstance(employee_skills, dict):
                errors.append(f"employees row {index}: skills must be an object")
                continue
            for skill_id, level in employee_skills.items():
                if skill_id not in known_skills: errors.append(f"employees row {index}: unknown skill {skill_id}")
                elif not isinstance(level, int) or not 0 <= level <= 5:
                    errors.append(f"employees row {index}: invalid level for {skill_id}")
        for index, item in enumerate(events or [], 1):
            if not isinstance(item, dict):
                continue
            prerequisites = item.get("prerequisites", {})
            develops_skills = item.get("develops_skills", [])
            if not isinstance(prerequisites, dict):
                errors.append(f"events row {index}: prerequisites must be an object")
                prerequisites = {}
            if not isinstance(develops_skills, list):
                errors.append(f"events row {index}: develops_skills must be an array")
                develops_skills = []
            for skill_id in list(prerequisites) + [x.get("skill_id") for x in develops_skills if isinstance(x, dict)]:
                if skill_id not in known_skills: errors.append(f"events row {index}: unknown skill {skill_id}")
        for index, row in enumerate(history or [], 1):
            if not isinstance(row, dict):
                continue
            if row.get("employee_id") not in known_employees: errors.append(f"history row {index}: unknown employee")
            if row.get("event_id") not in known_events: errors.append(f"history row {index}: unknown event")
            if row.get("status") not in ALLOWED_STATUSES: errors.append(f"history row {index}: invalid status")
        return errors

    def employee(self, employee_id: str) -> dict[str, Any]:
        if employee_id not in self.employees: raise HTTPException(status_code=404, detail="Employee not found")
        return self.employees[employee_id]

    def target_profile(self, employee: dict[str, Any]) -> dict[str, Any] | None:
        goal = employee.get("career_goal") or {}
        role, grade = goal.get("target_role", employee["role"]), goal.get("target_grade")
        if not grade:
            index = GRADES.index(employee["grade"])
            if index == len(GRADES) - 1: return None
            grade = GRADES[index + 1]
        return self.role_profiles.get((role, grade))

    @staticmethod
    def reference_date() -> date:
        """Return the deterministic date of the supplied Career Quest dataset.

        `CAREER_QUEST_TODAY` is useful when a jury supplies another dated
        dataset, while the documented starter-kit snapshot stays the default.
        """
        raw_date = os.getenv("CAREER_QUEST_TODAY", DATASET_SNAPSHOT_DATE)
        try:
            return date.fromisoformat(raw_date)
        except ValueError:
            return date.fromisoformat(DATASET_SNAPSHOT_DATE)

    def summary(self, employee: dict[str, Any]) -> dict[str, Any]:
        keys = ("employee_id", "full_name", "department", "role", "grade", "tenure_months", "preferred_language", "career_goal")
        return {key: employee.get(key) for key in keys}

    def available_steps(self, employee: dict[str, Any]) -> list[dict[str, Any]]:
        completed = {
            row["event_id"]
            for row in self.history
            if row["employee_id"] == employee["employee_id"]
            and row["status"] == "completed"
            and row["event_id"] not in RECURRING_EVENT_IDS
        }
        target = self.target_profile(employee) or {}
        target_role = target.get("role", employee["role"])
        target_grade = target.get("grade", employee["grade"])
        reference_date = self.reference_date().isoformat()
        result = []
        for event in self.events.values():
            if event.get("mandatory") or event["event_id"] in completed: continue
            if employee["role"] not in event.get("target_roles", []) and target_role not in event.get("target_roles", []): continue
            if employee["grade"] not in event.get("target_grades", []) and target_grade not in event.get("target_grades", []): continue
            if any(employee.get("skills", {}).get(skill, 0) < level for skill, level in event.get("prerequisites", {}).items()): continue
            if event.get("format") != "self_paced" and not any(day >= reference_date for day in event.get("upcoming_sessions", [])): continue
            result.append(self.event_summary(event))
        return result

    @staticmethod
    def event_summary(event: dict[str, Any]) -> dict[str, Any]:
        keys = ("event_id", "title", "type", "format", "duration_hours", "mandatory", "develops_skills", "prerequisites", "upcoming_sessions")
        return {key: deepcopy(event.get(key)) for key in keys}

    def profile(self, employee_id: str) -> dict[str, Any]:
        employee = self.employee(employee_id); target = self.target_profile(employee)
        required, critical = (target or {}).get("required_skills", {}), set((target or {}).get("critical_skills", []))
        skills = [{"skill_id": skill_id, "name": self.skills.get(skill_id, {}).get("name", skill_id),
                   "type": self.skills.get(skill_id, {}).get("type", "hard"), "current": employee.get("skills", {}).get(skill_id, 0),
                   "required": level, "gap": max(0, level - employee.get("skills", {}).get(skill_id, 0)), "critical": skill_id in critical}
                  for skill_id, level in required.items()]
        history = [self.activity_record(row) for row in self.history if row["employee_id"] == employee_id]
        met = bool(target) and all(employee.get("skills", {}).get(k, 0) >= v for k, v in required.items())
        return {"employee": self.summary(employee), "next_grade": {"role": target["role"], "grade": target["grade"], "requirements_met": met} if target else None,
                "skills": skills, "history": history, "available_steps": self.available_steps(employee)}

    def activity_record(self, row: dict[str, Any]) -> dict[str, Any]:
        result = deepcopy(row); result["title"] = self.events.get(row["event_id"], {}).get("title", row["event_id"])
        for key in ("completion_pct", "score", "feedback_rating"):
            if result.get(key) in ("", None): result[key] = None
            else: result[key] = int(result[key])
        result["due_date"] = result.get("due_date") or None
        return result

    def complete(self, employee_id: str, event_id: str) -> dict[str, Any]:
        employee = self.employee(employee_id)
        if event_id not in self.events: raise HTTPException(status_code=404, detail="Event not found")
        event = self.events[event_id]
        if event.get("mandatory") or event_id not in {x["event_id"] for x in self.available_steps(employee)}:
            raise HTTPException(status_code=409, detail="Event is not available for completion")
        updates = []
        for gain in event.get("develops_skills", []):
            skill_id = gain["skill_id"]; before = employee.setdefault("skills", {}).get(skill_id, 0)
            after = min(before + int(gain["gain"]), int(gain["max_level"])); employee["skills"][skill_id] = after
            updates.append({"skill_id": skill_id, "before": before, "after": after, "capped_by_max_level": after == int(gain["max_level"])})
        record_id = f"LOCAL{len(self.history) + 1:06d}"
        self.history.append({"record_id": record_id, "employee_id": employee_id, "event_id": event_id, "date": self.reference_date().isoformat(), "due_date": "", "status": "completed", "completion_pct": "100", "score": "", "feedback_rating": "", "assigned_by": "self"})
        target = self.target_profile(employee); requirements_met = bool(target) and all(employee["skills"].get(key, 0) >= value for key, value in target["required_skills"].items())
        return {"employee_id": employee_id, "event_id": event_id, "skills_updated": updates, "trajectory_updated": bool(updates), "requirements_met": requirements_met}

    def dashboard(self) -> dict[str, Any]:
        gaps: dict[str, list[tuple[int, str]]] = defaultdict(list)
        without = []
        for employee in self.employees.values():
            target = self.target_profile(employee)
            if target:
                for skill_id, required in target["required_skills"].items():
                    gap = max(0, required - employee.get("skills", {}).get(skill_id, 0))
                    if gap: gaps[skill_id].append((gap, employee["department"]))
            if not self.available_steps(employee): without.append({"employee_id": employee["employee_id"], "full_name": employee["full_name"], "reason": "No eligible voluntary activities available"})
        weak = []
        for skill_id, values in sorted(gaps.items(), key=lambda pair: (-sum(x[0] for x in pair[1]), pair[0])):
            by_dept: dict[str, list[int]] = defaultdict(list)
            for gap, department in values: by_dept[department].append(gap)
            weak.append({"skill_id": skill_id, "name": self.skills.get(skill_id, {}).get("name", skill_id), "avg_gap": round(sum(x[0] for x in values) / len(values), 2), "affected_employees": len(values),
                         "departments": [{"department": dept, "avg_gap": round(sum(nums) / len(nums), 2)} for dept, nums in sorted(by_dept.items())]})
        event_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in self.history: event_rows[row["event_id"]].append(row)
        engagement = []
        for event_id, rows in event_rows.items():
            statuses = Counter(row["status"] for row in rows); total = len(rows)
            engagement.append({"event_id": event_id, "title": self.events.get(event_id, {}).get("title", event_id), "participants": total,
                               "completion_rate": round(statuses["completed"] / total, 3), "drop_rate": round((statuses["dropped"] + statuses["no_show"]) / total, 3)})
        return {"weak_skills": weak, "employees_without_recommendation": without, "activity_engagement": sorted(engagement, key=lambda x: x["event_id"])}


store = DatasetStore()
