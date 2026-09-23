"""Контракты AI-ядра Career Quest.

Единственный общий файл для core/ (GLM) и llm/ (Codex, 2-й контекст тимлида).
Схемы соответствуют docs/openapi.yaml (Factor, Recommendation).

Кто что реализует:
- GLM:  core/analyzer.py (анализ профиля), core/scoring.py (скоринг), recommender.py (интеграция)
- Codex: llm/explainer.py (LLM-обоснование: OpenAI -> NVIDIA фолбэк, ru/kk/en, кэш, <10 c)

Меняет contracts.py только GLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Допустимые типы факторов (enum из docs/openapi.yaml). В каждой рекомендации >= 3 РАЗНЫХ типов.
FACTOR_TYPES = (
    "skill_gap",            # разрыв навыка vs требование next grade
    "critical_skill",       # критичный навык для следующего грейда
    "history_pattern",      # паттерн истории участия (drops/no_show/завершаемость)
    "prerequisites_met",    # пререквизиты выполнены
    "grade_fit",            # соответствие target_roles/target_grades
    "session_availability", # self_paced или ближайшие upcoming_sessions
)


@dataclass
class Factor:
    """Один фактор обоснования рекомендации."""

    type: str                 # один из FACTOR_TYPES
    message: str              # человекочитаемо, язык — ru/kk/en по запросу
    skill_id: str | None = None
    weight: float = 0.0       # вклад в скоринг, 0..1


@dataclass
class EmployeeContext:
    """Контекст сотрудника, который core собирает для LLM-слоя."""

    employee_id: str
    full_name: str
    role: str
    grade: str
    tenure_months: int
    preferred_language: str                       # "kk" | "ru" | "en"
    next_role: str = ""
    next_grade: str = ""
    skill_gaps: list[dict] = field(default_factory=list)        # [{skill_id, name, current, required, critical}]
    history_summary: dict = field(default_factory=dict)         # {drop_rate, no_show_rate, completed, ...}
    recent_events: list[dict] = field(default_factory=list)     # последние активности [{title, status}]


@dataclass
class ScoredCandidate:
    """Кандидат после скоринга. factors уже содержит >= 3 фактора разных типов."""

    event_id: str
    title: str
    score: float
    factors: list[Factor] = field(default_factory=list)


@dataclass
class Explanation:
    """Результат LLM-слоя (или фолбэк, если LLM недоступен)."""

    language: str                       # "kk" | "ru" | "en"
    text: str                           # связное обоснование по >= 3 факторам
    factors_used: list[str] = field(default_factory=list)
    engine: str = "openai"              # "openai" | "nvidia" | "heuristic-fallback"


@dataclass
class Recommendation:
    """Готовая рекомендация (скоринг + объяснение)."""

    rank: int                           # 1..3
    event_id: str
    title: str
    score: float
    factors: list[Factor] = field(default_factory=list)
    explanation: Explanation | None = None


@dataclass
class RecommendationResult:
    """Ответ recommend() для бек-трека (Antigravity/Алмас вызывает это)."""

    employee_id: str
    recommendations: list[Recommendation] = field(default_factory=list)
    engine: str = "openai"              # какой LLM-бэкенд в итоге сработал
