# Run with: uvicorn src.api.main:app --reload --port 8000
# Interactive docs available at: http://localhost:8000/docs

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.api.routers.ask import router as ask_router
from src.api.routers.health import router as health_router
from src.config.app_config import get_app_config
from src.config.settings import get_settings


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app_config = get_app_config()

    from src.embeddings.embedding_service import get_embeddings

    embeddings = get_embeddings()

    logger.info(
        "Startup complete | app=%s | llm_provider=%s | llm_model=%s | retrieval_top_k=%s | vectorstore_path=%s | GROQ_API_KEY=%s | DATABASE_URL=%s | REDIS_URL=%s | embeddings=%s",
        app_config.app.name,
        app_config.llm.provider,
        app_config.llm.model,
        app_config.retrieval.top_k,
        app_config.vectorstore.path,
        "set" if settings.groq_api_key else "unset",
        "set" if settings.database_url else "unset",
        "set" if settings.redis_url else "unset",
        type(embeddings).__name__ if embeddings is not None else "none",
    )

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="Agri Assistant API",
    description="RAG-powered maize agronomic advice API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174","https://agri-assistant-rag-1.onrender.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
# Add the production frontend domain here once deployed.
app.add_middleware(RequestLoggingMiddleware)
app.include_router(health_router)
app.include_router(ask_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Welcome to Agri Assistant API",
        "docs": "/docs",
    }
