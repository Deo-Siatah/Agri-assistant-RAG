# src/embeddings/embedding_service.py
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings

@lru_cache
def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")