# LLM-слой Career Quest. ЗОНА CODEX (2-й контекст тимлида), работаем по треку AI-ядро.
#
# Контракт (не менять без GLM): backend/app/ai/contracts.py
#
# Задача Codex — реализовать в этом пакете:
#   explainer.py:
#     def explain(candidate: ScoredCandidate, ctx: EmployeeContext,
#                 language: str) -> Explanation
#   Требования:
#   1) OpenAI API (gpt-4o-mini) — основная; NVIDIA API — фолбэк при ошибке/таймауте.
#      Ключи из env: OPENAI_API_KEY, NVIDIA_API_KEY.
#   2) Итоговое Explanation.text обязано опираться МИНИМУМ на 3 РАЗНЫХ фактора из
#      candidate.factors (типы см. FACTOR_TYPES в contracts.py).
#   3) Язык текста = language (ru/kk/en), не смешивать языки.
#   4) Жёсткий таймаут всего вызова: 8 секунд (беку остаётся запас до лимита 10 с).
#   5) Кэш по (employee_id, event_id, hash факторов), TTL до конца дня.
#   6) Фолбэк без LLM: собрать Explanation из factor.message (engine="heuristic-fallback").
#   7) Ключи НЕ логировать, НЕ хардкодить.
#
# Тесты: mocks без реальных вызовов API + один optional live-тест за флагом env LLM_LIVE_TEST=1.
