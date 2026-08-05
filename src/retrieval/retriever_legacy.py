from src.config.app_config import get_app_config

def get_retriever(vector_store):

    config = get_app_config()

    return vector_store.as_retriever(
        search_kwargs={
            "k": config.retrieval.top_k
        }
    )