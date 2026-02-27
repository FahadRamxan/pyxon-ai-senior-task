"""FastAPI application entry. Run with: uvicorn app.main:app --port 8002."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.routes import chat_router, feedback_router

# Resolve to absolute path so it works regardless of working directory
_STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup/shutdown hooks."""
    yield


app = FastAPI(
    title="Pyxon AI Chatbot",
    description="Agentic chatbot using LangChain, GPT-4o-mini, Google Search, and URL fetch.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat_router)
app.include_router(feedback_router)

# Serve static files (widget, embed.js) so /static/widget.html works too
if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def chat_ui() -> str:
    """Serve the full-page chat UI. API docs at /docs."""
    path = _STATIC_DIR / "chat.html"
    return path.read_text(encoding="utf-8")


@app.get("/widget", response_class=HTMLResponse, include_in_schema=False)
def widget() -> str:
    """Serve the embeddable chatbot widget (floating bubble + panel)."""
    path = _STATIC_DIR / "widget.html"
    if not path.is_file():
        raise FileNotFoundError(f"Widget not found: {path}")
    return path.read_text(encoding="utf-8")


@app.get("/embed.js", include_in_schema=False)
def embed_js() -> Response:
    """Serve the embed script so other sites can load the widget via iframe."""
    path = _STATIC_DIR / "embed.js"
    return Response(content=path.read_text(encoding="utf-8"), media_type="application/javascript")


@app.get("/health")
def health() -> dict:
    """Health check for deployment."""
    return {"status": "ok"}
