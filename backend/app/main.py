# Заглушка Этапа 0 от GLM, чтобы docker compose up работал сразу.
# Зона Antigravity: заменить/расширить на своём Этапе 0 (см. backend/app/api/AGENTS.md).
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Career Quest API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
