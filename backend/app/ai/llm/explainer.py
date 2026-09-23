"""LLM-слой Career Quest: объяснение рекомендации по факторам.

Зона AI-ядро/llm. Контракт: backend/app/ai/contracts.py.
Провайдеры: OpenAI (осн.) -> NVIDIA API (фолбэк, OpenAI-совместимый) -> heuristic (без LLM).
Ключи только из env (OPENAI_API_KEY, NVIDIA_API_KEY), не логируются и не хардкодятся.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import datetime, timedelta

import httpx

from ..contracts import EmployeeContext, Explanation, ScoredCandidate

TOTAL_BUDGET_S = 8.0
OPENAI_TIMEOUT_S = 5.0
MAX_TEXT_LEN = 800

LANG_NAMES = {"ru": "Russian", "kk": "Kazakh", "en": "English"}

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
OPENAI_MODEL_DEFAULT = "gpt-4o-mini"
NVIDIA_MODEL_DEFAULT = "meta/llama-3.3-70b-instruct"

_cache: dict[tuple, tuple[float, Explanation]] = {}
_cache_lock = threading.Lock()


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


def _end_of_day_ts() -> float:
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.timestamp()


def _cache_key(candidate: ScoredCandidate, ctx: EmployeeContext, language: str) -> tuple:
    payload = [
        (f.type, f.skill_id, f.message, round(f.weight, 3)) for f in candidate.factors
    ]
    digest = hashlib.md5(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return (ctx.employee_id, candidate.event_id, digest, language)


def _chat(
    url: str, api_key: str, model: str, messages: list[dict], timeout: float
) -> str:
    response = httpx.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 220,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _call_openai(messages: list[dict], timeout: float) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return _chat(
        OPENAI_URL,
        api_key,
        os.environ.get("OPENAI_MODEL", OPENAI_MODEL_DEFAULT),
        messages,
        timeout,
    )


def _call_nvidia(messages: list[dict], timeout: float) -> str:
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is not set")
    return _chat(
        NVIDIA_URL,
        api_key,
        os.environ.get("NVIDIA_MODEL", NVIDIA_MODEL_DEFAULT),
        messages,
        timeout,
    )


def _build_messages(
    candidate: ScoredCandidate, ctx: EmployeeContext, language: str
) -> list[dict]:
    lang = LANG_NAMES.get(language, "English")
    system = (
        "You are an HR career-development assistant. Explain to the employee why this "
        "specific activity is the recommended next step. Write ONLY in "
        f"{lang}. Ground the reasoning strictly on at least 3 DIFFERENT factors from the "
        "provided list (grade requirements, skill gaps, critical skills, participation "
        "history, prerequisites, availability). Be specific: use the numbers and skill "
        "names from the factors. 2-3 sentences, plain text, no markdown, no lists."
    )
    payload = {
        "employee": {
            "name": ctx.full_name,
            "role": ctx.role,
            "grade": ctx.grade,
            "tenure_months": ctx.tenure_months,
            "preferred_language": ctx.preferred_language,
        },
        "target": {"next_role": ctx.next_role, "next_grade": ctx.next_grade},
        "skill_gaps": ctx.skill_gaps,
        "history_summary": ctx.history_summary,
        "activity": {
            "event_id": candidate.event_id,
            "title": candidate.title,
            "score": candidate.score,
        },
        "factors": [
            {
                "type": f.type,
                "skill": f.skill_id,
                "detail": f.message,
                "weight": f.weight,
            }
            for f in candidate.factors
        ],
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def _heuristic_explanation(
    candidate: ScoredCandidate, language: str
) -> Explanation:
    top = sorted(candidate.factors, key=lambda f: f.weight, reverse=True)[:4]
    text = ". ".join(f.message for f in top).strip()
    return Explanation(
        language=language,
        text=text,
        factors_used=sorted({f.type for f in candidate.factors}),
        engine="heuristic-fallback",
    )


def explain(
    candidate: ScoredCandidate,
    ctx: EmployeeContext,
    language: str = "en",
) -> Explanation:
    key = _cache_key(candidate, ctx, language)
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and hit[0] > now:
            return hit[1]

    messages = _build_messages(candidate, ctx, language)
    start = time.monotonic()

    engine = "openai"
    text: str | None = None
    try:
        text = _call_openai(messages, min(OPENAI_TIMEOUT_S, TOTAL_BUDGET_S))
    except Exception:
        remaining = TOTAL_BUDGET_S - (time.monotonic() - start)
        if remaining >= 1.0:
            try:
                text = _call_nvidia(messages, remaining)
                engine = "nvidia"
            except Exception:
                text = None

    if not text:
        return _heuristic_explanation(candidate, language)

    explanation = Explanation(
        language=language,
        text=text[:MAX_TEXT_LEN],
        factors_used=sorted({f.type for f in candidate.factors}),
        engine=engine,
    )
    with _cache_lock:
        _cache[key] = (_end_of_day_ts(), explanation)
    return explanation
