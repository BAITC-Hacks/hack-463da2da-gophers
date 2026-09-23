# AGENTS.md — трек Backend (зона Алмаса, инструмент любой)

Работаешь по треку **Backend**. Твоя зона: `backend/app/api/` и `backend/app/main.py`. Твой трек в `TODO.md`: «Backend (Алмас)», этапы 0–4. Инструмент (Antigravity, Codex или другой) не важен — роль определяет трек, а не бренд агента.

Перед началом работы объяви: `Работаю по треку Backend. Моя зона: backend/app/api/. Мой инструмент: <...>.`

## Что ты строишь

1. **FastAPI-каркас**: конфиг (.env: OPENAI_API_KEY, NVIDIA_API_KEY), requirements.txt, линтер (ruff), pytest, `GET /health`, CORS для `http://localhost:5173`.
2. **Данные**: загрузка/валидация 4 файлов датасета (`career_quest_dataset/case_1/career_quest_dataset/`, в docker смонтирован в `/data`), in-memory store.
3. **Эндпоинты** (контракт — `docs/openapi.yaml`, НЕ меняй его сам):
   - `GET /employees` — список
   - `GET /employees/{id}` — профиль + история + доступные шаги
   - `POST /recommendations/{id}` — вызов AI-ядра: `backend/app/ai/recommender.py:recommend()`
   - `POST /employees/{id}/complete/{event_id}` — gain до max_level, пересчёт траектории, запись в activity_history
   - `POST /admin/load-dataset` — загрузка проверочных профилей жюри в формате датасета (КРИТИЧНО для защиты)
   - `GET /hr/dashboard` — агрегации для HR-экрана
4. **Роли**: сотрудник/HR (токен в заголовке), HR-эндпоинты закрыты.

## Границы

Скоринг и LLM — трек AI-ядро (`backend/app/ai/`, вызывай `recommend()`, не пиши свой). UI — трек Frontend (`frontend/`). Каждый этап — коммит `feat(api): ...`. Перед коммитом: `git pull`.
