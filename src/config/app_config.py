from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class AppInfo(BaseModel):
    name: str = "Agri Assistant"


class LLMConfig(BaseModel):
    provider: str = Field(default="groq")
    model: str = Field(default="llama-3.3-70b-versatile")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class RetrievalConfig(BaseModel):
    top_k: int = Field(default=3, ge=1)
    similarity_threshold: float = Field(default=1.0, ge=0.0)


class SplittingConfig(BaseModel):
    chunk_size: int = Field(default=1000, ge=1)
    chunk_overlap: int = Field(default=200, ge=0)

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, value: int, info: Any) -> int:
        chunk_size = info.data.get("chunk_size")
        if chunk_size is not None and value >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return value


class VectorStoreConfig(BaseModel):
    path: str = Field(default="data/vectorstore")
    rebuild: bool = Field(default=True)


class LoggingConfig(BaseModel):
    enabled: bool = Field(default=True)


class AppConfig(BaseModel):
    app: AppInfo = Field(default_factory=AppInfo)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    splitting: SplittingConfig = Field(default_factory=SplittingConfig)
    vectorstore: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def _default_config_path() -> Path:
    return Path(__file__).with_name("app.yaml")


def load_app_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path) if config_path is not None else _default_config_path()

    if not path.exists():
        raise FileNotFoundError(f"App config not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file) or {}

    return AppConfig.model_validate(raw_config)


@lru_cache
def get_app_config(config_path: str | Path | None = None) -> AppConfig:
    cache_key = str(config_path) if config_path is not None else None
    if cache_key is None:
        return load_app_config()
    return load_app_config(cache_key)