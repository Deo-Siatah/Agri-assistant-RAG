# src/embeddings/embedding_service.py
from functools import lru_cache
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from src.config.settings import get_settings


@lru_cache
def get_embeddings() -> HuggingFaceEndpointEmbeddings:
    settings = get_settings()
    return HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        task="feature-extraction",
        huggingfacehub_api_token=settings.hugging_face_url,
    )