from src.config.config_loader import load_config

def get_retriever(vector_store):

    config = load_config()

    return vector_store.as_retriever(
        search_kwargs={
            "k": config["retrieval"]["top_k"]
        }
    )