# LLM-слой Career Quest. Зона AI-ядро/llm.
#
# РЕАЛИЗОВАНО (GLM по поручению тимлида, explainer.py): OpenAI (осн.) -> NVIDIA (фолбэк) ->
# heuristic (без LLM). Кэш до конца дня, общий бюджет 8 c. Тесты: tests/test_explainer.py
# (моки), live-режим за флагом env LLM_LIVE_TEST=1.
#
# Публичная точка: explainer.explain(candidate: ScoredCandidate, ctx: EmployeeContext,
# language: str) -> Explanation  (типы — backend/app/ai/contracts.py)

