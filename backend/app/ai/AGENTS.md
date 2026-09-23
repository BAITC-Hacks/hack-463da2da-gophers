# AGENTS.md — зона GLM (AI-ядро)

Я — **GLM** (opencode, агент тимлида). Моя зона: `backend/app/ai/`. Мой трек в `TODO.md`: «GLM (трек AI-ядра)», этапы 0–4.

## Что я строю

Мультифакторный движок рекомендаций (ядро всего проекта, 50 из 100 баллов критериев):

1. **Анализ профиля** — разрывы навыков vs требования next grade (career_goal или grade+1), critical_skills, метрики истории (drop-rate, no_show, overdue по типам событий).
2. **Скоринг** — gap_score (критичные навыки весом больше), понижение по негативной истории, фильтры (пререквизиты, target_roles/grades, не completed, mandatory — исключить). Выход: топ-1..3 с факторами.
3. **LLM-слой** — OpenAI gpt-4o-mini → обоснование минимум по 3 факторам, NVIDIA API фолбэк, ru/kk/en по preferred_language, кэш, дедлайн 10 сек.
4. **Тесты на проверочные профили жюри** — кейс «Public Speaking ниже всех, но 3 пропуска подобных + критичный System Design» → рекомендация НЕ «бери минимальный навык».

## Контракты

- Antigravity вызывает мой код через `backend/app/ai/recommender.py:recommend(employee_id, ...) -> RecommendationResult`
- Схема факторов и ответа — в `docs/openapi.yaml` (components.schemas.Recommendation, Factor)
- Датасет: `career_quest_dataset/case_1/career_quest_dataset/` (формат — в README.md там же)

## Правила

Работаю ТОЛЬКО тут. Эндпоинты — зона Antigravity (`backend/app/api/`), UI — зона Codex (`frontend/`). Каждый этап — коммит `feat(ai): ...`. Общие файлы (AGENTS.md, TODO.md, openapi.yaml, docker-compose.yml) — только через GLM.
