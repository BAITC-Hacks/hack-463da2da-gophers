# Заглушка Этапа 0 от GLM, чтобы docker compose up работал сразу.
# Зона Antigravity: заменить/расширить на своём Этапе 0 (см. backend/app/api/AGENTS.md).
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.store import store

app = FastAPI(title="Career Quest API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.on_event("startup")
def load_dataset() -> None:
    store.load_default()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
